import sys
import numpy as np
import scipy
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCharts import QChart, QChartView, QScatterSeries, QValueAxis, QLineSeries

h=scipy.constants.h
e=scipy.constants.e
c=scipy.constants.c
k=scipy.constants.k

class Chart_2D(QMainWindow):
    def __init__(self, x_variable, y_variable):
        super().__init__()

        self.series = QScatterSeries()

        #Adding a single point to series
        
        self.blank_setup()
        
        #for i, val in enumerate(phet_calc_wavelength):
        #    self.series.append(val, phet_calc_current[i])

        #QPointF is designed for floating point precision
        #however append seems to use this by default?
        #self.series.append(QPointF(11,1))

        #setup a saved series for allowing retention of one wavelength or intensity vs current dataset
        self.saved_series = QScatterSeries()
        self.saved_series.setMarkerShape(QScatterSeries.MarkerShapeTriangle)
        self.saved_series.setColor(QColor(255,127,0))


        
        self.x_variable=x_variable
        self.y_variable=y_variable

        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(self.series)
        self.chart.addSeries(self.saved_series)
        #Default axes then adding own leads to overlap
        #self.chart.createDefaultAxes()
        #self.chart.setTitleFont(QFont("Arial",pointSize=16))
        #self.chart.setTitle(f"Plot: {self.x_variable} vs {self.y_variable}")

        #font = QFont("Arial", 14)

        #Variable setting
        if self.x_variable=="Wavelength":
            self.x_min=100
            self.x_max=600
            self.x_interval=50
            self.x_title="Wavelength (nm)"
        elif self.x_variable=="Frequency":
            self.x_min=0
            self.x_max=2000
            self.x_interval=200
            self.x_title="Frequency (THz)"
        elif self.x_variable=="Intensity":
            self.x_min=0
            self.x_max=100
            self.x_interval=10
            self.x_title="Intensity (% of Maximum Power)"
        else:
            self.x_min=0
            self.x_max=10
            self.x_interval=1
            self.x_title="Default Variable"
            

        if self.y_variable=="KE":
            self.y_min=-0.1
            self.y_max=11
            self.y_anchor=0
            self.y_interval=0.5
            self.y_title="Kinetic energy (eV)"

        elif self.y_variable=="Current":
            self.y_min=-0.1
            self.y_max=2
            self.y_anchor=0
            self.y_interval=0.2
            self.y_title="Current (A?)"
        else:
            self.y_min=0
            self.y_max=10
            self.y_anchor=0
            self.y_interval=1
            self.y_title="Default Variable"

        #X-axis
        self.axis_x = QValueAxis()
        #Tick count just sets a given number of ticks
        #self.axis_x.setTickCount(100)
        self.axis_x.setMin(self.x_min)
        self.axis_x.setMax(self.x_max)
        #Ticks at given start point and interval
        self.axis_x.setTickType(QValueAxis.TicksDynamic)
        #self.axis_x.setTickAnchor(100) #Think anchor defaults to minimum
        self.axis_x.setTickInterval(self.x_interval) 
        self.axis_x.setTitleText(self.x_title)
        #labels font affects both axis title and tick labels
        #self.axis_x.setLabelsFont(font)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.series.attachAxis(self.axis_x)
        #make sure to attach axes to all series you want to plot
        self.saved_series.attachAxis(self.axis_x)

        #Y-axis
        self.axis_y = QValueAxis()
        #self.axis_y.setTickCount(20)
        self.axis_y.setMin(self.y_min)
        self.axis_y.setMax(self.y_max)
        self.axis_y.setTickType(QValueAxis.TicksDynamic)
        self.axis_y.setTickAnchor(self.y_anchor)
        self.axis_y.setTickInterval(self.y_interval)
        self.axis_y.setTitleText(self.y_title)
        #self.axis_y.setLabelsFont(font)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_y)
        self.saved_series.attachAxis(self.axis_y)

        self._chart_view = QChartView(self.chart)
        #Pretty fuzzy if not anti-aliased!
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setCentralWidget(self._chart_view)

    def save_series(self):
        self.saved_series.replace(self.series.points())
        for i, value in enumerate(self.series.points()):
            if self.series.pointConfiguration(i)[self.series.PointConfiguration.Visibility] == False:
                self.saved_series.setPointConfiguration(i, {self.series.PointConfiguration.Visibility:False})
            else:
                self.saved_series.setPointConfiguration(i, {self.series.PointConfiguration.Visibility:True})
        self.series.clear()
        self.blank_setup()


    def blank_setup(self):
        for i, value in enumerate(np.linspace(100, 600, 51)):
            self.series.append(value,0)
            self.series.setPointConfiguration(i, {self.series.PointConfiguration.Visibility:False})

    #BORK NOTE - found in example this return function for widgets in other files from main
    #Still did not work
    #def chartreturn(self):
    #    return self.chart

class Oscillo(QMainWindow):
    def __init__(self):
        super().__init__()

        self.series = QLineSeries()
        self.series.setColor(QColor(255,127,0))
        
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(self.series)

        #Variable setting
        self.x_min=-2e-3
        self.x_max=2e-3
        self.x_interval=1e-3
        self.x_title="Time"

        self.y_min=-1.2
        self.y_max=1.2
        self.y_anchor=0
        self.y_interval=1.2
        self.y_title="Voltage"

        #X-axis
        self.axis_x = QValueAxis()
        #Tick count just sets a given number of ticks
        #self.axis_x.setTickCount(100)
        self.axis_x.setMin(self.x_min)
        self.axis_x.setMax(self.x_max)
        #Ticks at given start point and interval
        self.axis_x.setTickType(QValueAxis.TicksDynamic)
        #self.axis_x.setTickAnchor(100) #Think anchor defaults to minimum
        self.axis_x.setTickInterval(self.x_interval) 
        self.axis_x.setTitleText(self.x_title)
        #labels font affects both axis title and tick labels
        #self.axis_x.setLabelsFont(font)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.series.attachAxis(self.axis_x)

        #Y-axis
        self.axis_y = QValueAxis()
        #self.axis_y.setTickCount(20)
        self.axis_y.setMin(self.y_min)
        self.axis_y.setMax(self.y_max)
        self.axis_y.setTickType(QValueAxis.TicksDynamic)
        self.axis_y.setTickAnchor(self.y_anchor)
        self.axis_y.setTickInterval(self.y_interval)
        self.axis_y.setTitleText(self.y_title)
        #self.axis_y.setLabelsFont(font)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_y)

        #x_range = np.linspace(-1e-2, 1e-2, 2001)
        #omega = 2*np.pi*3000
        #self.series.clear
        #for x in x_range:
        #    y=0.5*np.exp(complex(0, omega*x)).real
        #    self.series.append(x, y)

        self._chart_view = QChartView(self.chart)
        #Pretty fuzzy if not anti-aliased!
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setCentralWidget(self._chart_view)

class KE_Oscillo(QMainWindow):
    def __init__(self):
        super().__init__()

        self.series = QScatterSeries()
        self.series.setColor(QColor(255,127,0))
        
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(self.series)

        #Variable setting
        self.x_min=0
        self.x_max=10
        self.x_interval=0.5
        self.x_title="Time"

        self.y_min=0
        self.y_max=10
        self.y_anchor=0
        self.y_interval=0.5
        self.y_title="Voltage"

        #X-axis
        self.axis_x = QValueAxis()
        #Tick count just sets a given number of ticks
        #self.axis_x.setTickCount(100)
        self.axis_x.setMin(self.x_min)
        self.axis_x.setMax(self.x_max)
        #Ticks at given start point and interval
        self.axis_x.setTickType(QValueAxis.TicksDynamic)
        #self.axis_x.setTickAnchor(100) #Think anchor defaults to minimum
        self.axis_x.setTickInterval(self.x_interval) 
        self.axis_x.setTitleText(self.x_title)
        #labels font affects both axis title and tick labels
        #self.axis_x.setLabelsFont(font)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.series.attachAxis(self.axis_x)

        #Y-axis
        self.axis_y = QValueAxis()
        #self.axis_y.setTickCount(20)
        self.axis_y.setMin(self.y_min)
        self.axis_y.setMax(self.y_max)
        self.axis_y.setTickType(QValueAxis.TicksDynamic)
        self.axis_y.setTickAnchor(self.y_anchor)
        self.axis_y.setTickInterval(self.y_interval)
        self.axis_y.setTitleText(self.y_title)
        #self.axis_y.setLabelsFont(font)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_y)

        #x_range = np.linspace(-1e-2, 1e-2, 2001)
        #omega = 2*np.pi*3000
        #self.series.clear
        #for x in x_range:
        #    y=0.5*np.exp(complex(0, omega*x)).real
        #    self.series.append(x, y)

        self._chart_view = QChartView(self.chart)
        #Pretty fuzzy if not anti-aliased!
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setCentralWidget(self._chart_view)
    def adv(self):
        curr_points = self.series.pointsVector()
        #This function is very useful - KE tracker really chugs once >4000 or so
        #keeping between 500 and 1000 definitely means can keep going for longer without slowing too much
        #1000 is too few if at max intensity though - chops off at about 3 seconds, so extended to 1500
        #crash 27/08 - removePoints not removeMultiple
        if len(curr_points)>1500:
            self.series.removePoints(0, 500)
        curr_points = self.series.pointsVector()
        shift_points = [QPointF(point.x()-0.01, point.y()) for point in curr_points]
        self.series.replace(shift_points)


#Standalone app for testing
#if __name__ == "__main__":
#    app = QApplication(sys.argv)
#
#    window=Oscillo()
#    window.show()
    #Scales window size, but doesn't scale any labels
#    window.resize(440,300)
#    sys.exit(app.exec())
#