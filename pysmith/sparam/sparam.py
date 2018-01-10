'''
Plots touchstone SNP files and calculates average

@author: khershberger
'''

import matplotlib

# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QFileDialog,
    QMenu,
    QSizePolicy,
    QVBoxLayout,
    QWidget
    )

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
    )
from matplotlib.figure import Figure

import numpy as np

import os
import logging
import skrf

def calcNetworkStatistics(networks):
    logger = logging.getLogger()
    # Determine Overlapping frequency range and minimum step size
    
    freqMin = None
    freqMax = None
    freqStep = None
    for net in networks:
        if freqMin is None:
            freqMin = net.frequency.start
        else:
            if freqMin < net.frequency.start:
                freqMin = net.frequency.start
                
        if freqMax is None:
            freqMax = net.frequency.stop
        else:
            if freqMax > net.frequency.stop:
                freqMax = net.frequency.stop

        if freqStep is None:
            freqStep = net.frequency.step
        else:
            if freqStep < net.frequency.step:
                freqStep = net.frequency.step
    
    msg = 'Freq Min: {:g}, Max {:g}, Step {:g}'.format(freqMin, freqMax, freqStep)
    logger.debug(msg)
    print(msg)
    
    fStats = skrf.Frequency(freqMin, freqMax, (freqMax-freqMin)/freqStep+1, 'Hz')
    fStats.unit = net.frequency.unit
    
    allS = []
    for net in networks:
        netTemp = net.interpolate(fStats)
        allS.append(netTemp.s)

    dataAvg           = skrf.network.Network()
    dataAvg.frequency = fStats
    
    ## Rectangular domain
    #dataAvg.s         = np.mean(allS, axis=0)
    # Polar domain
    dataAvg.s         = np.mean(np.abs(allS),axis=0) * np.exp(1j * np.mean(np.unwrap(np.angle(allS),axis=0),axis=0))

    dataAvg.name      = 'Mean'
    
    return dataAvg

class sparamPlot(QWidget):
    def __init__(self):

        # Setup Logger        
        self.logger = logging.getLogger()
        self.logger.debug('sparamPlot.__init__()')

        super().__init__()
        
        # Set default options
        self.opt = {}
        self.opt['format']  = 'db'
        self.opt['avgColor'] = '#0000ff'
        self.opt['avgLinewidth'] = 3.0
        self.opt['plot_figure_size'] = (15,9)  # Not sure if this applys sine we're now in a QWidget?
        self.opt['plot_figure_dpi'] = 100
        
        # Create our matplotlib stuff
        self.logger.debug('Creating figure and canvas')
        
        self.fig = Figure(figsize=self.opt['plot_figure_size'],
                          dpi=self.opt['plot_figure_dpi'], 
                          facecolor='w', 
                          edgecolor='k')
        
        self.ax = None
        self.axZoomed = None
        
#         FigureCanvas.__init__(self, self.fig)
#         self.setParent(parent)
#         FigureCanvas.setSizePolicy(self,
#                                    QSizePolicy.Expanding,
#                                    QSizePolicy.Expanding)
#         FigureCanvas.updateGeometry(self)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setSizePolicy( QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.canvas.updateGeometry()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        
        # Now to construct the widget GUI:
        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)  # the matplotlib canvas
        self.setLayout(vbox)

    def on_key_press(self, event):
        self.logger.debug('you pressed {}'.format(event.key))
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas, self.mpl_toolbar)

    def on_button_press(self, event):
        self.logger.debug('you pressed {}'.format(event.button))
        if event.dblclick:
            self.logger.debug('Double click on: {:s}'.format(str(event.inaxes)))
            self.toggleZoom(event.inaxes)
            # we want to allow other navigation modes as well. Only act in case
            # shift was pressed and the correct mouse button was used
            #if event.key != 'shift' or event.button != 1:
            #    return
                
    def toggleZoom(self, ax):
        """
        Toggles the enlargement of a sub-plot to entire figure window.
        
        Implementation inspired by:
        https://www.semipol.de/2015/09/04/matplotlib-interactively-zooming-to-a-subplot.html
        """
        if ax is not None:
            if self.axZoomed is None:
                # Store pre-zoom information
                self.axZoomed = (ax, ax.get_position())
                ax.set_position([0.1, 0.1, 0.85, 0.65])
                
                # hide all the other axes...
                for axTemp in self.fig.axes:
                    if axTemp is not ax:
                        axTemp.set_visible(False)
                    
            else:
                # Restore axes position
                self.axZoomed[0].set_position(self.axZoomed[1])
                self.axZoomed = None
                
                # Restore other axes
                for axTemp in self.fig.axes:
                    axTemp.set_visible(True)
            
            self.canvas.draw()
            self.mpl_toolbar.update()           # Reset navigation history
            self.mpl_toolbar.push_current()     # Push current state into navigation stack

    def loadData(self, filelist):
        self.logger.info('sparamPlot.loadData()')
        
        self.dataAvg = None
        
        self.data = []
        for fnameWithPath in filelist:
            fname = os.path.basename(fnameWithPath)
            self.logger.info('Loading: ' + fname)
        
            spnet = skrf.network.Network()
            spnet.read_touchstone(fnameWithPath)
            #spnet.name = fname
            self.data.append(spnet)
            
    def calcStatistics(self):
        try:
            self.dataAvg = calcNetworkStatistics(self.data)
            self.plotData()
        except Exception:
            logging.exception('sparamData.calcStatistics(): Exception occured')
        
        
    def saveStatistics(self):
        try:
            self.logger.debug('sparamData.saveStatistics()')
            if self.dataAvg is None:
                self.logger.warning('Statistics not calculated.')
            else:
                filename = QFileDialog.getSaveFileName(self, 'Save average', 
                                                     '','S2P Files (*.S2P)')
                self.dataAvg.write_touchstone(filename=filename[0])
        except Exception:
            logging.exception('sparamData.saveStatistics(): Exception occured')
        

    def plotData(self):
        self.logger.info('sparamPlot.plotData()')
        
        self.fig.clf()
        self.ax = None
        self.axZoomed = None
        
        # Determine maximum port count
        nports = 0
        for net in self.data:
            nports = max(nports, net.nports)
            
        if (nports < 1):
            self.logger.warning('Maximum port count less than 1')
            return

        # Create the plot axes and store handles
        self.ax = [[None for k1 in range(nports)] for k2 in range(nports)]
        #if self.opt['plot_phase']:
        #    self.axb = [[None] * nports] * nports
        #else:
        #    self.axb = None
        
        for row in range(nports):
            for col in range(nports):
                #axTemp = self.fig.add_subplot(nports, nports, row*nports+col+1)
                self.ax[row][col] = self.fig.add_subplot(nports, nports, row*nports+col+1)

                #if self.opt['plot_phase']:
                #        self.axb[row][col] = axTemp.twinx()
                
        def plotSmatrix(net, color=None, linewidth=None):
            for row in range(nports):
                for col in range(nports):
                    axTemp = self.ax[row][col]

                    self.logger.debug('Adding subplot')
                    axTemp.grid(True)
                
                    axTemp.set_title('S{:d}{:d}'.format(row+1,col+1))
                    
                    # Now determine plot type:
                    if   self.opt['format'] == 'db':
                        net.plot_s_db(row,col, ax=axTemp, show_legend=False, color=color, linewidth=linewidth)
                    elif self.opt['format'] == 'phase':
                        net.plot_s_deg(row,col, ax=axTemp, show_legend=False, color=color, linewidth=linewidth)
                    elif self.opt['format'] == 'smith':
                        if row == col:
                            net.plot_s_smith(row,col, ax=axTemp, show_legend=False, color=color, linewidth=linewidth)
                        else:
                            net.plot_s_db(row,col, ax=axTemp, show_legend=False, color=color, linewidth=linewidth)
                    else:
                        self.logger.warning('Unknown plot format {:s}'.format(self.opt['format']))
                    
                    
        # Do the plotting:
        for net in self.data:
            plotSmatrix(net)
        try:
            plotSmatrix(self.dataAvg, 
                        color=self.opt['avgColor'],
                        linewidth=self.opt['avgLinewidth'])
        except AttributeError:
            pass
            
        
        # Tidy up the layout                             
        plotCaption = 'Caption'
        self.fig.tight_layout()
        self.fig.subplots_adjust(top = 0.9)
        st = self.fig.suptitle(plotCaption, fontsize='x-large')
        st.set_y(0.96)
        
        self.canvas.draw()
        self.mpl_toolbar.update()           # Reset navigation history
        self.mpl_toolbar.push_current()     # Push current state into navigation stack
        
    def menuOptionsCreate(self):
        # Create options Menu
        self.menuOptions = QMenu('Options', self)

        # Create Format subMenu
        menuFormat = self.menuOptions.addMenu('&Format')
        ag = QActionGroup(self, exclusive=True)
        a = ag.addAction(QAction('dB', self, checkable=True))
        if self.opt['format'] == 'db':
            a.setChecked(True)
        menuFormat.addAction(a)
        a = ag.addAction(QAction('Phase', self, checkable=True))
        if self.opt['format'] == 'phase':
            a.setChecked(True)
        menuFormat.addAction(a)
        a = ag.addAction(QAction('Smith', self, checkable=True))
        if self.opt['format'] == 'smith':
            a.setChecked(True)
        menuFormat.addAction(a)
        menuFormat.triggered[QAction].connect(self.setFormat)
        
        # Create statistics subMenu
        menuStatistics = self.menuOptions.addMenu('&Statistics')
        menuStatisticsCalc = menuStatistics.addAction('&Calculate')
        menuStatisticsCalc.triggered.connect(self.calcStatistics)
        menuStatisticsSave = menuStatistics.addAction('&Save')
        menuStatisticsSave.triggered.connect(self.saveStatistics)

        return self.menuOptions

    def setFormat(self, item):
        try:
            message = item.text() +" is triggered"
            logging.debug(message)
            
            if   item.text() == 'dB':
                self.opt['format'] = 'db'
            elif item.text() == 'Phase':
                self.opt['format'] = 'phase'
            elif item.text() == 'Smith':
                self.opt['format'] = 'smith'
                
            self.plotData()
            
        except Exception as e:
            logging.exception('sparamData.menuHandler(): Exception!')
        
    def menuHandler(self, item):
        try:
            message = item.text() +" is triggered"
            logging.debug(message)
            print(message)
            
            logging.debug('Selected {:s}'.format(item.text()))
            if item.text() == 'Test1':
                logging.debug('Selected Test1')
            
        except Exception as e:
            logging.exception('sparamData.menuHandler(): Exception!')
        