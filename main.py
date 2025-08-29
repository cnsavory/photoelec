import numpy as np
import sys
import scipy
import random
import time
from functools import partial
from PySide6.QtCore import QObject, Qt, Slot, QRectF, QTimer, QPointF, QMargins
from PySide6.QtGui import (QBrush, QColor, QPainter, QPen, QPainterPath, QRadialGradient, QGradient, 
                           QFont)
from PySide6.QtWidgets import (QApplication, QSlider, QWidget, QGridLayout, QSpinBox, QLabel, QDoubleSpinBox, 
QVBoxLayout, QPushButton, QTabWidget, QComboBox, QGraphicsView, QGraphicsItem, QGraphicsScene, 
QGraphicsProxyWidget, QGraphicsSimpleTextItem)
from chart import Chart_2D, Oscillo, KE_Oscillo
#from animation_pane import Electron, Plate, MainAnimationPane

h=scipy.constants.h
e=scipy.constants.e
c=scipy.constants.c
k=scipy.constants.k

class Wave(QWidget):
    def __init__(self, parent=None):
        super(Wave, self).__init__(parent)
        self.setWindowTitle("Wavelength")

        #Create slider widget
        self.slider= QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(100)
        self.slider.setMaximum(600)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(50)
        self.slider.setSingleStep(10)
        #remember the connect when sending the signal!
        self.slider.valueChanged.connect(self.slider_to_box)
        self.slider.valueChanged.connect(self.slider_to_ke)
        
        #Only update chart at slider's final position
        #Note this does not yet update when box value is changed instead!
        #Box only has signals for when text/value changed - ie would be triggered
        #whenever slider changes too given above reciprocal updates.
        self.slider.valueChanged.connect(self.ke_to_chart)
        self.slider.valueChanged.connect(self.reset_elecs)
        
        #Merged current plotting into current calculation slot - no risk of overplotting
        #self.slider.valueChanged.connect(self.current_to_chart)

        #Create spinbox, good for displaying integers?
        spinbox_label = QLabel("Wavelength (nm)")
        self.spinbox = QSpinBox()
        self.spinbox.setMaximum(600)
        self.spinbox.setMinimum(100)
        #Danger of infinite loop? Not obviously so
        self.spinbox.valueChanged.connect(self.box_to_slider)
        #self.spinbox.textChanged.connect(self.ke_to_chart)

        #Intensity Slider
        self.slideri= QSlider(Qt.Orientation.Horizontal)
        self.slideri.setMinimum(0)
        self.slideri.setMaximum(100)
        self.slideri.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slideri.setTickInterval(10)
        self.slideri.setSingleStep(1)
        #remember the connect when sending the signal!
        self.slideri.valueChanged.connect(self.slideri_to_boxi)
        self.slideri.valueChanged.connect(self.slideri_to_oscillo)
        self.slideri.valueChanged.connect(self.reset_elecs)

        #Intensity box
        intensity_label = QLabel("Intensity (% of Max Power)")
        self.intensity = QSpinBox()
        self.intensity.setMaximum(100)
        self.intensity.setMinimum(0)
        #Danger of infinite loop? Not obviously so
        self.intensity.valueChanged.connect(self.boxi_to_slideri)
        #On press, slider resets Current plot
        self.slideri.sliderPressed.connect(self.wipe_intensity)
        #self.slideri.valueChanged.connect(self.slider_to_current)
        
        self.powerdict = {'sodium':5.159120066772471e-14, 'zinc':5.4195652077219776e-14, 'calcium':5.246463359088317e-14,
        'copper':4.393591405908849e-14, 'platinum':3.697302254000795e-14}
        self.wfdict = {'sodium': 2.35, 'calcium':2.80, 'copper': 4.40, 'zinc': 4.24, 'platinum':5.9}
        self.wf = self.wfdict['sodium']
        self.optpower = self.powerdict['sodium']

        #Combobox for selecting metal target
        target_label = QLabel("Target metal")
        self.target = QComboBox()
        self.target.insertItems(0, list(self.wfdict.keys()))
        self.target.currentIndexChanged.connect(self.change_target)
        self.target.currentIndexChanged.connect(self.reset_elecs)

        #Try importing Scatter graph
        #self.graph = MainGraph()
        self.graph = MainGraph(self.slideri.value())

        self.slider.valueChanged.connect(self.graph._scene.beam.change_colour)
        self.slider.valueChanged.connect(self.graph._scene.lamp.change_colour)

        #Save button
        self.save_button = QPushButton("Save dataset")
        self.save_button.clicked.connect(self.main_save_series)

        #Kinetic Energy box
        ke_label = QLabel("Kinetic energy (eV)")
        self.ke = QDoubleSpinBox()
        self.ke.setReadOnly(True)
        self.ke.setMaximum(1000)
        self.ke.setMinimum(0)

        #Current box
        curr_label = QLabel("Current (A?)")
        self.curr = QDoubleSpinBox()
        self.curr.setReadOnly(True)
        self.curr.setMaximum(100)
        self.curr.setMinimum(0)
        self.curr.valueChanged.connect(self.current_to_graphic_current)

        #First time, these need to be here to have all widgets defined?
        self.slider.valueChanged.connect(self.slider_to_current)
        self.slider.valueChanged.connect(self.slider_to_oscillo)
        self.slideri.valueChanged.connect(self.slider_to_current)
        self.slideri.valueChanged.connect(self.slider_to_ke)

        #Set Slider grid layout
        gridlayout = QGridLayout()
        gridlayout.addWidget(self.spinbox, 0, 0)
        gridlayout.addWidget(spinbox_label, 1, 0)
        gridlayout.addWidget(self.slider, 2, 0)
        gridlayout.addWidget(self.intensity, 0, 1)
        gridlayout.addWidget(intensity_label, 1, 1)
        gridlayout.addWidget(self.slideri, 2, 1)
        gridlayout.addWidget(self.ke, 0, 2)
        gridlayout.addWidget(ke_label, 1, 2)
        gridlayout.addWidget(self.save_button, 2, 2)
        #gridlayout.addWidget(curr_label, 1, 3)
        #gridlayout.addWidget(self.curr, 0, 3)
        gridlayout.addWidget(target_label, 1, 3)
        gridlayout.addWidget(self.target, 2, 3)
        #Space stretches twice as much if window is expanded
        gridlayout.setColumnStretch(0,1)
        gridlayout.setColumnStretch(1,1)
        gridlayout.setColumnStretch(2,1)
        gridlayout.setColumnStretch(3,1)
        #self.setLayout(layout)

        #Set overall layout
        #note defaults to stretching col 1 of grid layout to match
        layout=QVBoxLayout()
        layout.addLayout(gridlayout)
        layout.addWidget(self.graph)
        self.setLayout(layout)

        #Updates box value if slider changed
    def slider_to_box(self):
        self.spinbox.setValue(self.slider.value())
    
        #Reciprocal update of slider value if box changed
    def box_to_slider(self):
        self.slider.setValue(self.spinbox.value())

    def slideri_to_boxi(self):
        self.intensity.setValue(self.slideri.value())
    
        #Reciprocal update of slider value if box changed
    def boxi_to_slideri(self):
        self.slideri.setValue(self.intensity.value())

    def change_target(self):
        new_target = self.target.currentText()
        self.wf = self.wfdict[new_target]
        self.optpower = self.powerdict[new_target]
        self.graph._chart1.series.clear()
        self.graph._chart1.blank_setup()
        self.graph._chart2.series.clear()
        self.graph._chart2.blank_setup()
        self.graph._chart3.series.clear()
        self.graph._chart3.blank_setup()
        self.graph._chart4.series.clear()
        self.graph._chart4.blank_setup()

    def slider_to_ke(self):
        ke=(h*c/(self.slider.value()*1e-9))-self.wf*e
        if ke < 0:
            ke=0
        ke_elec=ke/e
        if self.slideri.value()==0:
            ke_elec=0
        self.ke.setValue(ke_elec)
    
    def ke_to_chart(self):
        #Only plot multiples of 10 nm to avoid overcrowding
        if self.slider.value() % 10 == 0.0:
            #Keeping non-replace versions for security
            #Colour change unnecessary, but keeping it in for demonstration
            #self.graph._chart1.series.append(self.slider.value(), self.ke.value())
            self.graph._chart1.series.replace(float(self.slider.value()), float(0), float(self.slider.value()), self.ke.value())
            self.graph._chart1.series.setPointConfiguration(self.slider.value()/10-10, {self.graph._chart1.series.PointConfiguration.Visibility:True, 
                                                                                        self.graph._chart1.series.PointConfiguration.Color:QColor(0, 191, 255)})
            #self.graph._chart2.series.append(c/(self.slider.value()*1e-9*1e12), self.ke.value())
            self.graph._chart2.series.replace(float(self.slider.value()), float(0), float(c/(self.slider.value()*1e-9*1e12)), self.ke.value())
            self.graph._chart2.series.setPointConfiguration(self.slider.value()/10-10, {self.graph._chart1.series.PointConfiguration.Visibility:True})

    def slider_to_current(self):
        si_wave = self.slider.value()*1e-9
        ke_norm=((-h*c/si_wave)+self.wf*e)
        #Linear (power), F-D and thermal factor
        I = self.optpower*(self.slideri.value()/100)*si_wave/(h*c)*e*(1/(np.exp(ke_norm/(k*300))+1))*((h*c/si_wave-self.wf*e)/k*300)**2
        #Crude cutoff to get inversion - essentially if F-D and thermal factors 'equal 1', switch to linear
        if 10.93*(self.slideri.value()/100)*si_wave/(h*c)*e < I:
            I = 10.93*(self.slideri.value()/100)*si_wave/(h*c)*e
        self.curr.setValue(I)
        # Still only plots if a multiple of 10nm - problem if they change intensity at a non-multiple
        # Wouldn't matter so much if implement the deletion of previous data - perhaps on intensity slider pressed??
        if self.slider.value() % 10 == 0.0:
            rng = np.random.default_rng()
            noise=rng.normal(loc=0.0, scale=0.01)
            I_noise = I+noise
            self.graph._chart3.series.replace(float(self.slider.value()), float(0), float(self.slider.value()), I_noise)
            self.graph._chart3.series.setPointConfiguration(self.slider.value()/10-10, {self.graph._chart3.series.PointConfiguration.Visibility:True, 
                                                                                        self.graph._chart3.series.PointConfiguration.Color:QColor(0, 191, 255)})
            self.graph._chart4.series.replace(float(self.slider.value()), float(0), float(c/(self.slider.value()*1e3)), I_noise)
            self.graph._chart4.series.setPointConfiguration(self.slider.value()/10-10, {self.graph._chart3.series.PointConfiguration.Visibility:True, 
                                                                                        self.graph._chart3.series.PointConfiguration.Color:QColor(0, 191, 255)})
            #Original append version
            #self.graph._chart3.series.append(si_wave*1e9, I_noise)
            #self.graph._chart4.series.append(c/(si_wave*1e12), I_noise)
    
    def slider_to_oscillo(self):
        if self.slider.value() % 10 == 0:
            x_range = np.linspace(-2e-3, 2e-3, 401)
            freq_thz = c/(self.slider.value()*1e3)
            omega = 2*np.pi*freq_thz
            self.graph._chart5.series.clear()
            #Osc in graphics scene
            self.graph._scene.osc.series.clear()
            for x in x_range:
                y=(self.slideri.value()/100)*np.exp(complex(0, omega*x)).real
                self.graph._chart5.series.append(x, y)
                self.graph._scene.osc.series.append(x,y)

    def slideri_to_oscillo(self):
        if self.slideri.value() % 5 == 0:
            x_range = np.linspace(-2e-3, 2e-3, 401)
            freq_thz = c/(self.slider.value()*1e3)
            omega = 2*np.pi*freq_thz
            self.graph._chart5.series.clear()
            #Osc in graphics scene
            self.graph._scene.osc.series.clear()
            for x in x_range:
                y=(self.slideri.value()/100)*np.exp(complex(0, omega*x)).real
                self.graph._chart5.series.append(x, y)
                self.graph._scene.osc.series.append(x,y)


    def wipe_intensity(self):
        self.graph._chart1.series.clear()
        self.graph._chart1.blank_setup()
        self.graph._chart2.series.clear()
        self.graph._chart2.blank_setup()
        self.graph._chart3.series.clear()
        self.graph._chart3.blank_setup()
        self.graph._chart4.series.clear()
        self.graph._chart4.blank_setup()

    def main_save_series(self):
        self.graph._chart1.save_series()
        self.graph._chart2.save_series()
        self.graph._chart3.save_series()
        self.graph._chart4.save_series()

    def reset_elecs(self):
        #print(self.graph._scene.items())
        for i in self.graph._scene.items():
            i.regen_switch()
        max_ke=(h*c/(self.slider.value()*1e-9))-self.wf*e
        if max_ke < 0:
            max_ke=0
        max_ke_elec=max_ke/e
        if self.slideri.value()==0:
            max_ke_elec=0
        #Avoid too many electrons at once
        
        #if len(self.graph._scene.items()) < 100:
        #    self.graph._scene.init_elec(self.slideri.value(), np.sqrt(max_ke_elec+1))
        #else:
        #    global wait_timer
        #    wait_timer=QTimer()
        #    wait_timer.setSingleShot(True)
        #    wait_timer.timeout.connect(partial(self.wait_reset, max_ke_elec))
        #    wait_timer.start(1000)

        #Scaling factor of number of photoelectrons based off constant power output
        #For all surfaces, this linear scaling only occurs up to 200 nm after which scattering dominates
        si_wave = self.slider.value()
        if si_wave < 200:
            ph_scale = si_wave/200
        else:
            ph_scale = 1

        #making this a permanent attribute in case also want
        #to introduce distribution/scattering at high wavelength later

        #Have instead moved the sparsity of electrons control to the init_elec function
        #Set max speed to just sqrt of KE - mass factor effectively cancels with the scaling factor
        #necessary to actually see the electron movement on a sensible timescale!
        self.graph._scene.init_elec(self.slideri.value(), np.sqrt(max_ke_elec), np.sqrt(max_ke_elec), ph_scale)

    def current_to_graphic_current(self):
        self.graph._scene.curr.setValue(self.curr.value())
            
        

class MainGraph(QTabWidget):
    def __init__(self, intensity, p=None):
        super().__init__(p)

        #screen_size = self.screen.size()
        #minimum_graph_size = QSize(screen_size.width()/2, screen_size.height()/1.75)

        self._chart1 = Chart_2D("Wavelength", "KE")
        self._chart2 = Chart_2D("Frequency", "KE")
        self._chart3 = Chart_2D("Wavelength", "Current")
        self._chart4 = Chart_2D("Frequency", "Current")
        self._chart5 = Oscillo()
        self._scene = MainAnimationPane(intensity)
        self._tab6 = QGraphicsView(self._scene)
        self._tab6.show()
        self._chart6 = KE_Oscillo()

        self.addTab(self._chart1, "Wavelength vs Kinetic Energy")
        self.addTab(self._chart2, "Frequency vs Kinetic Energy")
        self.addTab(self._chart3, "Wavelength vs Current")
        self.addTab(self._chart4, "Frequency vs Current")
        self.addTab(self._chart5, "Oscilloscope")
        self.addTab(self._tab6, "Animation")
        self.addTab(self._chart6, "Kinetic energy tracker")
####
#### Moved all animation related classes here - otherwise destroy elec method
#### does not find plate as MainAnimationPane was defined in this script
class Plate(QGraphicsItem):
    def __init__(self):
        super().__init__()

        self.color = QColor(0,0,0) 

    def boundingRect(self):
        return QRectF(0, 0, 15, 150)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(self.color, 10))
        painter.drawLine(5, 0, 5, 150)
    #Dummy function to make it easier to code wavelength/intensity update functions
    def regen_switch(self):
        return None
    
class Lamp(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.color = QColor(0.5*255,0.5*255,0.5*255)
        self.setRotation(-45)

    def boundingRect(self):
        return QRectF(0, 0, 100, 70)
    
    def paint(self,painter,option,widget):
        lamp_path = QPainterPath()
        lamp_path.moveTo(100, 20)
        lamp_path.lineTo(60, 20)
        #Arc to function makes minimal sense to me - the end point specified is not actually
        #where it ends up, though it will draw extra lines to end up where it thinks it should.
        #Sweep angle is definitely the 'total angle' spanned by the arc after any start line/angle
        #the start angle is very ambiguous
        #width and height do seem to be fixed, but the height doesn't actually correspond to the 
        #height spanned by the curve alone? is it as if it were the full circle and you are only taking part?
        #But then width doesn't seem to obey the same rules??
        #lamp_path.arcTo(30, 0, 30, 20, 0, 90)

        lamp_path.quadTo(45, 0, 30, 0)
        #continuing this line makes awkward control point determination to keep symmetry
        #easier to just make mirror image
        #05/08 - no, can't do moveTo as it starts a new path - fill gets messed up


        #Not convinced this is symmetric but looks ok
        lamp_path.quadTo(45, 35, 30, 70)
        lamp_path.quadTo(47.5, 70, 60, 50)
        lamp_path.lineTo(100, 50)
        lamp_path.closeSubpath()

        
        #draw as separate paths to make filling/changing fill easier
        bulb_path = QPainterPath()
        bulb_path.moveTo(30, 70)
        bulb_path.quadTo(50, 35, 30, 0)
        bulb_path.quadTo(15, 35, 30, 70)

        painter.setRenderHint(QPainter.Antialiasing)
        #make pen self.color for cool glow!
        painter.setPen(QPen(QColor(0,0,0), 2))
        painter.drawPath(lamp_path)
        painter.fillPath(lamp_path, QColor(0,0,0))
        painter.drawPath(bulb_path)
        painter.fillPath(bulb_path, self.color)

    def regen_switch(self):
        return None
    
    def change_colour(self):
        beamcol = wave.slider.value()
        #Values from stackoverflow 3407942, Dan Bruton
        red = 0
        green = 0
        blue = 0
        if beamcol < 350:
            red = 0.5
            green = 0.5
            blue = 0.5
        elif beamcol >= 350 and beamcol < 380:
            red = (beamcol - 350)/60 + 0.5
            green = (380 - beamcol)/60
            blue = (beamcol - 350)/60 + 0.5
        elif beamcol >= 380 and beamcol < 440:
            red = (440 - beamcol)/60
            blue = 1
        elif beamcol >= 440 and beamcol < 490:
            green = (beamcol - 440)/50
            blue = 1
        elif beamcol >= 490 and beamcol < 510:
            green = 1
            blue = (510-beamcol)/20
        elif beamcol >= 510 and beamcol < 580:
            red = (beamcol - 510)/70
            green = 1
        elif beamcol >=580 and beamcol < 645:
            red = 1
            green = (645-beamcol)/65
        elif beamcol >=645 and beamcol <=780:
            red = 1
        self.color = QColor(red*255, green*255, blue*255)
        self.update()

class Beam(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.color = QColor(0.5*255,0.5*255,0.5*255)
        #Setting rotation here is much better than rotating painter! 
        #rotates bounding box etc as well
        self.setRotation(-45)

    def boundingRect(self):
        return QRectF(0, 0, 70, 100)
    
    def paint(self,painter,option,widget):
        beam_path = QPainterPath()
        beam_path.moveTo(70, 15)
        beam_path.lineTo(70, 85)
        beam_path.lineTo(0,100)
        beam_path.lineTo(0,0)
        beam_path.closeSubpath()

        linearGrad = QRadialGradient(70, 50, 70)
        linearGrad.setColorAt(1, Qt.white)
        linearGrad.setColorAt(0, self.color)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(0.5)
        painter.setPen(Qt.NoPen)
        #painter.rotate(-45)
        painter.drawPath(beam_path)
        painter.fillPath(beam_path, linearGrad)

    def regen_switch(self):
        return None
    
    def change_colour(self):
        beamcol = wave.slider.value()
        #Values from stackoverflow 3407942, Dan Bruton
        red = 0
        green = 0
        blue = 0
        if beamcol < 350:
            red = 0.5
            green = 0.5
            blue = 0.5
        elif beamcol >= 350 and beamcol < 380:
            red = (beamcol - 350)/60 + 0.5
            green = (380 - beamcol)/60
            blue = (beamcol - 350)/60 + 0.5
        elif beamcol >= 380 and beamcol < 440:
            red = (440 - beamcol)/60
            blue = 1
        elif beamcol >= 440 and beamcol < 490:
            green = (beamcol - 440)/50
            blue = 1
        elif beamcol >= 490 and beamcol < 510:
            green = 1
            blue = (510-beamcol)/20
        elif beamcol >= 510 and beamcol < 580:
            red = (beamcol - 510)/70
            green = 1
        elif beamcol >=580 and beamcol < 645:
            red = 1
            green = (645-beamcol)/65
        elif beamcol >=645 and beamcol <=780:
            red = 1
        self.color = QColor(red*255, green*255, blue*255)
        self.update()

class Wire1(QGraphicsItem):
    def __init__(self):
        super().__init__()

        self.color = QColor(0,0,0) 

    def boundingRect(self):
        return QRectF(0, 0, 250, 300)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(self.color, 1))

        wire1_path = QPainterPath()
        wire1_path.moveTo(15, 150)
        wire1_path.lineTo(0, 150)
        wire1_path.lineTo(0, 350)
        wire1_path.lineTo(150,350)
        wire1_path.lineTo(150,347)
        wire1_path.lineTo(3,347)
        wire1_path.lineTo(3,153)
        wire1_path.lineTo(15,153)
        wire1_path.closeSubpath()
        painter.drawPath(wire1_path)
        painter.fillPath(wire1_path, self.color)
    #Dummy function to make it easier to code wavelength/intensity update functions
    def regen_switch(self):
        return None
    
class Wire2(QGraphicsItem):
    def __init__(self):
        super().__init__()

        self.color = QColor(0,0,0) 

    def boundingRect(self):
        return QRectF(0, 0, 250, 300)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(self.color, 1))

        wire1_path = QPainterPath()
        wire1_path.moveTo(400, 150)
        wire1_path.lineTo(415, 150)
        wire1_path.lineTo(415, 350)
        wire1_path.lineTo(250,350)
        wire1_path.lineTo(250,347)
        wire1_path.lineTo(412,347)
        wire1_path.lineTo(412,153)
        wire1_path.lineTo(400,153)
        wire1_path.closeSubpath()
        painter.drawPath(wire1_path)
        painter.fillPath(wire1_path, self.color)
    #Dummy function to make it easier to code wavelength/intensity update functions
    def regen_switch(self):
        return None    

class Wire3(QGraphicsItem):
    def __init__(self):
        super().__init__()

        self.color = QColor(0,0,0) 

    def boundingRect(self):
        return QRectF(0, 0, 70, 30)
    
    def paint(self, painter, option, widget):
        wire_path = QPainterPath()
        wire_path.moveTo(0,0)
        wire_path.quadTo(30, -30, 70, 30)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(self.color, 5))
        painter.drawPath(wire_path)
        #painter.drawLine(0, 0, 100, 0)
    #Dummy function to make it easier to code wavelength/intensity update functions
    def regen_switch(self):
        return None

class Proxy(QGraphicsProxyWidget):
    def __init__(self):
        super().__init__()

    def regen_switch(self):
        return None

class Instrument(QGraphicsItem):
    def __init__(self):
        super().__init__()

    def boundingRect(self):
        return QRectF(0, 0, 120, 80)
    
    def paint(self,painter,option,widget):
        beam_path = QPainterPath()
        beam_path.moveTo(5, 0)
        beam_path.lineTo(115, 0)
        beam_path.quadTo(120, 0, 120, 5)
        beam_path.lineTo(120,75)
        beam_path.quadTo(120, 80, 115, 80)
        beam_path.lineTo(5, 80)
        beam_path.quadTo(0, 80, 0, 75)
        beam_path.lineTo(0, 5)
        beam_path.quadTo(0, 0, 5, 0)
        beam_path.closeSubpath()

        linearGrad = QRadialGradient(60, 40, 200)
        linearGrad.setColorAt(0, QColor(0.5*255, 0.5*255, 0.5*255))
        linearGrad.setColorAt(1, Qt.white)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1))
        #painter.rotate(-45)
        painter.drawPath(beam_path)
        painter.fillPath(beam_path, linearGrad)

    def regen_switch(self):
        return None
    
class Ammeter_text(QGraphicsSimpleTextItem):
    def __init__(self):
        super().__init__()

        self.setFont(QFont("Courier New", 15))
        self.setText("Ammeter")
        self.setBrush(QColor(120, 0, 0))
        self.setPen(QPen(Qt.black, 0.1))
    
    #SE 62577372 - recommends centering text by subtracting center of bounding rect
    def centreAt(self,pos):
        self.setPos(pos - self.boundingRect().center())

    def regen_switch(self):
        return None


class MainAnimationPane(QGraphicsScene):
    def __init__(self, intensity):
        super().__init__()

        #self.scene=QGraphicsScene()
        self.setSceneRect(0, 0, 400, 400)

        #scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        self.wire1 = Wire1()
        self.addItem(self.wire1)
        self.wire1.setPos(0,0)
        self.wire2 = Wire2()
        self.addItem(self.wire2)
        self.wire2.setPos(0,0)
        self.wire3 = Wire3()
        self.addItem(self.wire3)
        self.wire3.setPos(250,-30)

        self.ammeter_housing = Instrument()
        self.addItem(self.ammeter_housing)
        self.ammeter_housing.setPos(140,320)
        self.curr = QDoubleSpinBox()
        self.curr.setReadOnly(True)
        #self.curr.setDecimals(3) 3rd decimal doesn't work properly?
        self.curr.setStyleSheet("font: 15pt Arial")
        self.currproxy = Proxy()
        self.currproxy.setWidget(self.curr)
        self.addItem(self.currproxy)
        self.curr_text = Ammeter_text()
        self.addItem(self.curr_text)
        self.currproxy.setPos(150, 330)
        self.curr_text.setPos(155, 370)

        self.osc = Oscillo()
        #self.linearGrad = QRadialGradient(60, 40, 200)
        #self.linearGrad.setColorAt(0, QColor(0.5*255, 0.5*255, 0.5*255))
        #self.linearGrad.setColorAt(1, Qt.white)
        self.osc_palette = self.osc.palette()
        #cannot use palette to set a gradient as colour, going with solid colour for now
        self.osc_palette.setColor(self.osc.backgroundRole(), QColor(0.5*255, 0.5*255, 0.5*255))
        self.osc.setPalette(self.osc_palette)
        #self.osc.setStyleSheet("border-color:Qt.white")
        self.osc.resize(160,120)
        self.osc.axis_x.setTitleText(None)
        self.osc.axis_x.setLabelsVisible(False)
        self.osc.axis_y.setTitleText(None)
        self.osc.axis_y.setLabelsVisible(False)
        self.osc.chart.setMargins(QMargins(0,0,0,0))
        self.osc.chart.setBackgroundRoundness(0)
        self.oscproxy = Proxy()
        self.oscproxy.setWidget(self.osc)
        self.addItem(self.oscproxy)
        self.oscproxy.setPos(300, -50)


        self.regen_list = []
        self.plate_1 = Plate()
        self.plate_2 = Plate()
        self.addItem(self.plate_1)
        self.addItem(self.plate_2)
        self.beam = Beam()
        self.addItem(self.beam)
        self.beam.setPos(110,33)
        self.lamp = Lamp()
        self.addItem(self.lamp)
        self.lamp.setPos(150,15)

        self.plate_1.setPos(15,100)
        self.plate_2.setPos(390,100)
        self.default_speed = 2

        #Should be unused now that connections to intensity slider established
        #I.e. default is to have no electrons excited
        #self.init_elec(intensity, self.default_speed)

        self.timer = QTimer()
        self.timer.timeout.connect(self.advance)
        self.timer.timeout.connect(self.update_ke_track)
        self.timer.start(1000/100)


    def add_elec(self, speed, base_speed):
        elect = Electron(speed, base_speed)
        elect.setPos(15,100+random.random()*150)
        self.addItem(elect)


    def init_elec(self, intensity, speed, base_speed, ph_scale):
        if speed == 0:
            if hasattr(self, 'sparse_timer'):
                self.sparse_timer.stop()
            return None
        else:
            #Change intensity to affect total number of electrons in view at a time?
            #Moved to sparse add function as better to keep sending signals and then just 
            #ignore when over limit than trying to control timer.
            #for i in range(0,round(intensity/2)):
                #self.add_elec(speed)
            
            #Attempt to spread initial electrons out
            #self.add_elec(speed)
            self.sparse_timer = QTimer()
            self.sparse_timer.timeout.connect(partial(self.sparse_add, speed, base_speed, intensity, ph_scale))
            self.sparse_timer.start(100)

    def sparse_add(self, speed, base_speed, intensity, ph_scale):
        #50 is a better max number of electrons than 100, which is too crowded
        #27/08: plus 10 is to account for the permanent scene items - need to keep track if this changes
        if len(self.items()) < ph_scale*round(intensity/2)+10:
            #small random subtraction to recreate something of a distribution of speeds
            #To replace with actual distribution from current equation?
            self.add_elec(speed-(random.random()/4)*speed, base_speed)
        else:
            return
        
    def update_ke_track(self):
        wave.graph._chart6.adv()

        


class Electron(QGraphicsItem):
    def __init__(self, speed, base_speed):
        super().__init__()

        self.speed=speed
        self.base_speed = base_speed
        self.size = 5
        self.regen = True

        self.color = QColor(0,0,255) 

    def boundingRect(self):
        return QRectF(0, 0, self.size, self.size)
    

    #All custom Graphics items need a paint function to describe the object to be rendered
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor(0,0,255)))
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(self.color, 2))
        #print(painter.background())
        #painter.setPen(QPen(Qt.black, 2))
        rect = QRectF(0,0,self.size,self.size)
        painter.drawEllipse(rect)
        painter.setBackgroundMode(Qt.TransparentMode)

    #advance is also an inherited method; triggered below whenever timer runs out (auto resets)
    def advance(self, phase):
        #Moves electron across according to speed, map to parent makes this a relative motion
        self.setPos(self.mapToParent(self.speed,0))
        if self.collidesWithItem(wave.graph._scene.plate_2):
            wave.graph._scene.removeItem(self)
            self.regen_elec()
            #currently appends KE not speed, in line with voltage propotional to KE
            wave.graph._chart6.series.append(10,self.speed**2)

    def regen_elec(self):
        if self.regen==True:
            #20/08 original behaviour - regenerated electron had same speed
            #speed = self.speed
            #20/08 new behaviour - randomize speed
            speed = self.base_speed-(random.random()/4)*self.base_speed
            global regen_timer
            regen_timer=QTimer()
            #For some reason, appending timer to list works??
            #Presumably because then the timer becomes some separate entity with something else referring to it
            #and thus it doesn't get over written??
            #This might get expensive with lots of timers running, however hopefully with single shots, they
            # individually won't keep updating and getting more expensive?
            #May need to implement some regular purge to make sure they don't build up too much.
            wave.graph._scene.regen_list.append(regen_timer)
            regen_timer.setSingleShot(True)
            regen_partial= partial(wave.graph._scene.add_elec, speed, self.base_speed)
            regen_timer.timeout.connect(regen_partial)
            #Originally delay made sense, however switching off regen is much easier if delay is effectively zero.
            regen_timer.start(1000/1000)

    def regen_switch(self):
        self.regen=False

####

if __name__ == '__main__':
    #Create the Qt Application
    app=QApplication(sys.argv)
    #Create and show the form
    wave=Wave()
    wave.show()
    wave.resize(1000,800)
    #Run the Main QT loop
    sys.exit(app.exec())