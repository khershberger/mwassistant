'''
Tutorial from:
    http://zetcode.com/gui/pyqt5/menustoolbars/

@author: khershberger
'''

import logging
import sys
import traceback
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    qApp,
    QApplication,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QStyle,
    QTextEdit,
    QTreeView,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget)
from PyQt5.QtGui import (
    QFont,
    QIcon,
    QStandardItem,
    QStandardItemModel)
from PyQt5.QtCore import (
    Qt,
    QCoreApplication)
# from PyQt5 import QtCore

from qtconsole.qt import QtGui
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

import pysmith.sparam.sparam

__version__ = '0.1.0'

class loggingAdapter(logging.Handler):
    def __init__(self, parent, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class ConsoleWidget(RichJupyterWidget):
    def __init__(self, *args, customBanner=None,  myWidget=None, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        if customBanner is not None:
            self.banner = customBanner

        self.font_size = 6
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel(show_banner=False)
        self.kernel_manager.kernel.gui = 'qt'
        self.kernel_client = self._kernel_manager.client()
        self.kernel_client.start_channels()

        def stop():
            self.kernel_client.stop_channels()
            self.kernel_manager.shutdown_kernel()
        self.exit_requested.connect(stop)
        
        self.kernel_manager.kernel.shell.push({'widget':self,'myWidget':myWidget})

    def push_vars(self, variableDict):
        """
        Given a dictionary containing name / value pairs, push those variables
        to the Jupyter console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):
        """
        Clears the terminal
        """
        self._control.clear()

        # self.kernel_manager

    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)

    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self._execute(command, False)


class PysmithMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Construct the menubar
        bar = self.menuBar()
        file = bar.addMenu('&File')
        openAction = QAction('&Open', self)
        #openAction.triggered.connect(self.processTrigger) 
        file.addAction(openAction)
        file.triggered[QAction].connect(self.processTrigger)
        # Aabout Menu
        a = bar.addAction('&About')
        a.triggered.connect(self.triggerMenuAbout)

        ### Log Dock
        
        # Create Log Widget
        self.logTextEdit = QPlainTextEdit()
        self.logTextEdit.setReadOnly(True)
        logAdapter = loggingAdapter(self, self.logTextEdit)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
        logAdapter.setFormatter(formatter)
        
        # Setup logging
        logger = logging.getLogger() 
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logAdapter)
        logger.debug('Log adapter hopefully attached')
        
        # Create dock for log window
        self.dockLog = QDockWidget('Log', self)
        self.dockLog.setWidget(self.logTextEdit)
        self.dockLog.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockLog)

        ### Create main dock
        
        # Create textEdit linked to Jupyter widget
        logging.info('Creating sparam widget')
        self.sparamDock = pysmith.sparam.sparam.sparamPlot()
        bar.addMenu(self.sparamDock.menuOptionsCreate())
                
        # Create the docs
        self.dockMain = QDockWidget('Empty main widget', self)
        self.dockMain.setWidget(self.sparamDock)
        self.dockMain.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockMain)

        ### Jupyter Dock
        
        # Create Jupyter widget
        logging.info('Creating JupyterWidget')
        # Turn down logging level
        logging.getLogger('ipykernel').setLevel(logging.WARNING)
        #logging.getLogger('traitlets').setLevel(logging.WARNING)
        jupyterWidgetConsole = ConsoleWidget(myWidget=self)

        # Create the docs
        self.dockJupyter = QDockWidget('Jupyter console', self)
        self.dockJupyter.setWidget(jupyterWidgetConsole)
        self.dockJupyter.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockJupyter)

        # Now we construct the central Widget & it's layout
        mainWidget = QWidget(self)
                
        # Create & assign layout for mainWidget
        layout = QHBoxLayout()
        mainWidget.setLayout(layout)

        # Tabbify overlapping docks
        self.tabifyDockWidget(self.dockLog, self.dockJupyter)

        # Set mainWidget to be central widget
        self.setCentralWidget(mainWidget)
        self.setGeometry(150, 150, 1400, 1000)
        self.setWindowTitle('PySmith')
        self.show()

    def processTrigger(self, q):
        try:
            message = q.text()+" is triggered"
            logging.debug(message)
            print(message)
            
            if q.text() == '&Open':
                filelist = QFileDialog.getOpenFileNames(self, 'Open file', 
                                                     '','S2P Files (*.S2P)')
                logging.info(filelist[0])
                self.sparamDock.loadData(filelist[0])
                self.sparamDock.plotData()
                
            
        except Exception as e:
            logging.exception('processTrigger(): Exception!')
            
    def triggerMenuAbout(self, event):
        dlg = dialogAbout(self)
        
            
class dialogAbout(QMessageBox):
    """
    Shows an about dialog with version information.
    
    The formatting in 'Details' region is horrible. Apparently resizing
    a QMessageBox is not easily done.  Consnsus seems to be to create 
    using a QDialog instead.  Too lazy to do thta right now though.
    """
    def __init__(self,parent=None):
        super().__init__(parent)

        from matplotlib import __version__ as versionMatplotlib
        from numpy import __version__ as versionNumpy
        from PyQt5.QtCore import QT_VERSION_STR
        from PyQt5.Qt import PYQT_VERSION_STR

        versionPython     = sys.version
        versionPySmith    = __version__
        
        versionDetails = '\n'.join([
                'PySmith version {:s}'.format(versionPySmith),
                'Python version: {:s}'.format(versionPython),
                'Qt version: {:s}'.format(QT_VERSION_STR),
                'PyQt version: {:s}'.format(PYQT_VERSION_STR),
                'matplotlib version: {:s}'.format(versionMatplotlib),
                'numpy version: {:s}'.format(versionNumpy)
                ])

        self.setWindowTitle('About PySmith')
        self.setText('               PySmith version {:s}               '.format(versionPySmith))
        self.setDetailedText(versionDetails)
        
        self.show()
        

def main():
    app = QApplication(sys.argv)
    guiMain = PysmithMainWindow()
    try:
        retval = app.exec_()
    except:     # This doesn't seem to actually work.
        print('Uncaught Exception')
        sys.exit(1)
    sys.exit(retval)

if __name__ == '__main__':
    main()