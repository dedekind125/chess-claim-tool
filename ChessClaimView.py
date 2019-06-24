"""
Chess Claim Tool: ChessClaimView

Copyright (C) 2019 Serntedakis Athanasios <thanasis@brainfriz.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import platform
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QTreeView, QPushButton, QDesktopWidget,
QAbstractItemView, QHBoxLayout, QVBoxLayout, QLabel, QStatusBar, QMessageBox, QAction, QDialog)
from PyQt5.QtGui import QStandardItemModel, QPixmap, QMovie, QStandardItem, QColor
from PyQt5.QtCore import Qt, QSize
from helpers import resource_path

class ChessClaimView(QMainWindow):
    """ The main window of the application.
    Attributes:
        rowCount(int): The number of the row the TreeView Table has.
        iconsSize(int): The recommended size of the icons.
        mac_notification: Notification for macOS
        win_notification: Notification for windows OS
    """
    def __init__(self):
        super().__init__()

        self.resize(720, 275)
        self.iconsSize = 16
        self.setWindowTitle('Chess Claim Tool')
        self.center()

        if (platform.system() == "Darwin"):
            from MacNotification import Notification
            self.mac_notification = Notification()
        elif (platform.system() == "Windows"):
            from win10toast import ToastNotifier
            self.win_notification = ToastNotifier()

    def center(self):
        """ Centers the window on the screen """
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
            (screen.height()-size.height())/2)

    def set_GUI(self):
        """ Initialize GUI components. """

        # Create the Menu
        self.livePgnOption = QAction('Live PGN',self)
        self.livePgnOption.setCheckable(True)
        aboutAction = QAction('About',self)

        menubar = self.menuBar()

        optionsMenu = menubar.addMenu('&Options')
        optionsMenu.addAction(self.livePgnOption)

        aboutMenu = menubar.addMenu('&Help')
        aboutMenu.addAction(aboutAction)

        aboutAction.triggered.connect(self.slots.on_about_clicked)

        # Create the Claims Table (TreeView)
        self.claimsTable = QTreeView()
        self.claimsTable.setFocusPolicy(Qt.NoFocus)
        self.claimsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.claimsTable.header().setDefaultAlignment(Qt.AlignCenter)
        self.claimsTable.setSortingEnabled(True)
        self.claimsTable.setIndentation(0)
        self.claimsTable.setUniformRowHeights(True)

        # Create the Claims Model
        self.claimsTableModel = QStandardItemModel()
        labels = ["#","Timestamp","Type","Board","Players","Move"]
        self.claimsTableModel.setHorizontalHeaderLabels(labels)
        self.claimsTable.setModel(self.claimsTableModel)

        # Create the Scan & Stop Button Box
        self.buttonBox = ButtonBox(self)

        # Create the Sources Button
        sourcesButton = QPushButton("Add Sources")
        sourcesButton.setObjectName("sources")
        sourcesButton.clicked.connect(self.slots.on_sourcesButton_clicked)

        # Create the Status Bar
        self.pixmapCheck = QPixmap(resource_path("check_icon.png"))
        self.pixmapError = QPixmap(resource_path("error_icon.png"))

        self.sourceLabel = QLabel()
        self.sourceImage = QLabel()
        self.sourceImage.setObjectName("source-image")
        self.downloadLabel = QLabel()
        self.downloadImage = QLabel()
        self.downloadImage.setObjectName("download-image")
        self.scanLabel = QLabel()
        self.scanImage = QLabel()
        self.scanImage.setObjectName("scan-image")

        self.spinner = QMovie(resource_path("spinner.gif"))
        self.spinner.setScaledSize(QSize(self.iconsSize, self.iconsSize))
        self.spinner.start()

        self.statusBar = QStatusBar()
        self.statusBar.setSizeGripEnabled(False)

        self.statusBar.addWidget(self.sourceLabel)
        self.statusBar.addWidget(self.sourceImage)
        self.statusBar.addWidget(self.downloadLabel)
        self.statusBar.addWidget(self.downloadImage)
        self.statusBar.addWidget(self.scanLabel)
        self.statusBar.addWidget(self.scanImage)
        self.statusBar.addPermanentWidget(sourcesButton)
        self.statusBar.setContentsMargins(10,5,9,5)

        # Container Layout for the Central Widget
        containerLayout = QVBoxLayout()
        containerLayout.setSpacing(0)
        containerLayout.addWidget(self.claimsTable)
        containerLayout.addWidget(self.buttonBox)

        # Central Widget
        containerWidget = QWidget()
        containerWidget.setLayout(containerLayout)

        self.setCentralWidget(containerWidget)
        self.setStatusBar(self.statusBar)

    def resize_claimsTable(self):
        """ Resize the table (if needed) after the insertion of a new element. """
        for index in range(0,6):
            self.claimsTable.resizeColumnToContents(index)

    def set_slots(self, slots):
        """ Connect the Slots """
        self.slots = slots

    def add_to_table(self,type,bo_number,players,move):
        """ Add new row to the claimsTable
        Args:
            type: The type of the draw (3 Fold Repetition, 5 Fold Repetition,
                                        50 Moves Rule, 75 Moves Rule).
            bo_number: The number of the boards, if this information is available.
            players: The name of the players.
            move: With which move the draw is valid.
        """

        # Before insertion, remove rows as descripted in the remove_rows function
        self.remove_rows(type,players)

        timestamp = str(datetime.now().strftime('%H:%M:%S'))
        row = []
        count = str(self.claimsTableModel.rowCount()+1)
        items = [count,timestamp,type,bo_number,players,move]

        """ Convert each item(str) to QStandardItem, make the necessary stylistic
        additions and append it to row."""

        for index in range(len(items)):
            standardItem = QStandardItem(items[index])
            standardItem.setTextAlignment(Qt.AlignCenter)

            if(index == 2):
                font = standardItem.font()
                font.setBold(True)
                standardItem.setFont(font)

            if (items[index] == "5 Fold Repetition" or items[index] == "75 Moves Rule"):
                standardItem.setData(QColor(255,0,0), Qt.ForegroundRole)

            row.append(standardItem)

        self.claimsTableModel.appendRow(row)

        # After the insertion resize the table
        self.resize_claimsTable()

        # Always the last row(the bottom of the table) should be visible.
        self.claimsTable.scrollToBottom()

        #Send Notification
        self.notify(type,players,move)

    def notify(self,type,players,move):
        """ Send notification depending on the OS.
        Args:
            type: The type of the draw (3 Fold Repetition, 5 Fold Repetition,
                                        50 Moves Rule, 75 Moves Rule).
            players: The names of the players.
            move: With which move the draw is valid.
        """
        if (platform.system() == "Darwin"):
            self.mac_notification.clearNotifications()
            self.mac_notification.notify(type,players,move)
        elif(platform.system() == "Windows"):
                self.win_notification.show_toast(type,
                                   players+"\n"+move,
                                   icon_path=resource_path("logo.ico"),
                                   duration=5,
                                   threaded=True)

    def remove_from_table(self,index):
        """ Remove element from the claimsTable.
        Args:
            index: The index of the row we want to remove. First row has index=0.
        """
        self.claimsTableModel.removeRow(index)

    def remove_rows(self,type,players):
        """ Removes a existing row from the Claims Table when same players made
        the same type of draw with a new move - or they made 5 Fold Repetition
        over the 3 Fold or 75 Moves Rule over 50 moves Rule.

        Args:
            type: The type of the draw (3 Fold Repetition, 5 Fold Repetition,
                                        50 Moves Rule, 75 Moves Rule).
            players: The names of the players.
        """
        for index in range(self.claimsTableModel.rowCount()):

            try:
                modelType = self.claimsTableModel.item(index,2).text()
                modelPlayers = self.claimsTableModel.item(index,4).text()
            except AttributeError:
                modelType = ""
                modelPlayers = ""

            if (modelType == type and modelPlayers == players):
                self.remove_from_table(index)
                self.reset_countColumn()
                break
            elif (type == "5 Fold Repetition" and modelType == "3 Fold Repetition" and modelPlayers == players) :
                self.remove_from_table(index)
                self.reset_countColumn()
                break
            elif (type == "75 Moves Rule" and modelType == "50 Moves Rule" and modelPlayers == players):
                self.remove_from_table(index)
                self.reset_countColumn()
                break

    def reset_countColumn(self):
        """ Re-index the numbers in the first column of Claims Table
        (the "#" column) after the removal of rows (see remove_rows()).
        """
        rowCount = self.claimsTableModel.rowCount()
        for index in range(rowCount):
            standardItem = QStandardItem(str(index+1))
            standardItem.setTextAlignment(Qt.AlignCenter)
            self.claimsTableModel.setItem(index,0,standardItem)

    def clear_table(self):
        """ Clear all the elements off the Claims Table. """
        for index in range(self.claimsTableModel.rowCount()):
            self.claimsTableModel.removeRow(0)

    def set_sources_status(self,status,validSources=None):
        """ Adds the sourcess in the statusBar.
        Args:
            status(str): The status of the validity of the sources.
                "ok": At least one source is valid.
                "error": None of the sources are valid.
            validSources(list): The list of valid sources, if there is any.
                This list is used here to display the ToolTip.
        """
        self.sourceLabel.setText("Sources:")

        # Set the ToolTip if there are sources.
        try:
            text = ""
            for index in range(len(validSources)):
                if (index == len(validSources) - 1):
                    number = str(index+1)
                    text = text+number+") "+validSources[index].get_value()
                else:
                    number = str(index+1)
                    text = text+number+") "+validSources[index].get_value()+"\n"
            self.sourceLabel.setToolTip(text)
        except TypeError:
            pass

        if (status == "ok"):
            self.sourceImage.setPixmap(self.pixmapCheck.scaled(self.iconsSize,self.iconsSize,transformMode=Qt.SmoothTransformation))
        else:
            self.sourceImage.setPixmap(self.pixmapError.scaled(self.iconsSize,self.iconsSize,transformMode=Qt.SmoothTransformation))

    def set_download_status(self,status):
        """ Adds download status in the statusBar.
        Args:
            status(str): The status of the download(s).
                "ok": The download of the sources is successful.
                "error": The download of the sources failed.
                "stop": The download process stopped.
        """
        timestamp = str(datetime.now().strftime('%H:%M:%S'))
        self.downloadLabel.setText(timestamp+" Download:")
        if (status == "ok"):
            self.downloadImage.setPixmap(self.pixmapCheck.scaled(self.iconsSize,self.iconsSize,transformMode=Qt.SmoothTransformation))
        elif (status == "error"):
            self.downloadImage.setPixmap(self.pixmapError.scaled(self.iconsSize,self.iconsSize,transformMode=Qt.SmoothTransformation))
        elif (status == "stop"):
            self.downloadImage.clear()
            self.downloadLabel.clear()

    def set_scan_status(self,status):
        """ Adds the scan status in the statusBar.
        Args:
            status(str): The status of the scan process.
                "active": The scan process is active.
                "wait": The scan process waits for a new file.
                "stop": The scan process stopped.
        """
        timestamp = str(datetime.now().strftime('%H:%M:%S'))
        self.scanLabel.setText(timestamp+" Scan:")
        if (status == "wait"):
            self.scanImage.setPixmap(self.pixmapCheck.scaled(self.iconsSize,self.iconsSize,transformMode=Qt.SmoothTransformation))
        elif (status == "active"):
            self.scanImage.setMovie(self.spinner)
        elif (status == "stop"):
            self.scanLabel.clear()
            self.scanImage.setVisible(False)

    def change_scanButton_text(self,status):
        """ Changes the text of the scanButton depending on the status of the application.
        Args:
            status(str): The status of the scan process.
                "active": The scan process is active.
                "wait": The scan process is being terminated
                "stop": The scan process stopped.
        """
        if (status == "active"):
            self.buttonBox.scanButton.setText("Scanning PGN...")
        elif (status == "stop"):
            self.buttonBox.scanButton.setText("Start Scan")
        elif(status == "wait"):
            self.buttonBox.scanButton.setText("Please Wait")

    def enable_buttons(self):
        self.buttonBox.scanButton.setEnabled(True)
        self.buttonBox.stopButton.setEnabled(True)

    def disable_buttons(self):
        self.buttonBox.scanButton.setEnabled(False)
        self.buttonBox.stopButton.setEnabled(False)

    def enable_statusBar(self):
        """ Show download and scan status messages - if they were previously
        hidden (by disable_statusBar) - from the statusBar."""
        self.downloadLabel.setVisible(True)
        self.scanLabel.setVisible(True)
        self.downloadImage.setVisible(True)

    def disable_statusBar(self):
        """ Hide download and scan status messages from the statusBar. """
        self.downloadLabel.setVisible(False)
        self.downloadImage.setVisible(False)
        self.scanLabel.setVisible(False)
        self.scanImage.setVisible(False)

    def closeEvent(self,event):
        """ Reimplement the close button
        If the program is actively scanning a pgn a warning dialog shall be raised
        in order to make sure that the user didn't clicked the close Button accidentally.
        Args:
            event: The exit QEvent.
        """
        try:
            if (self.slots.scanWorker.isRunning):
                exitDialog = QMessageBox()
                exitDialog.setWindowTitle("Warning")
                exitDialog.setText("Scanning in Progress")
                exitDialog.setInformativeText("Do you want to quit?")
                exitDialog.setIcon(exitDialog.Warning)
                exitDialog.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                exitDialog.setDefaultButton(QMessageBox.Cancel)
                replay = exitDialog.exec()

                if replay == QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()
        except:
            event.accept()

    def load_warning(self):
        """ Displays a Warning Dialog.
        trigger:
            User clicked the "Start Scanning" Button without any valid pgn source.
        """
        warningDialog = QMessageBox()
        warningDialog.setIcon(warningDialog.Warning)
        warningDialog.setWindowTitle("Warning")
        warningDialog.setText("PGN File(s) Not Found")
        warningDialog.setInformativeText("Please enter at least one valid PGN source.")
        warningDialog.exec()

    def load_about_dialog(self):
        """ Displays the About Dialog."""
        self.aboutDialog = AboutDialog()
        self.aboutDialog.set_GUI()
        self.aboutDialog.show()

class ButtonBox(QWidget):
    """ Provides a Horizontal Box with two Buttons.
    Attributes:
        scanButton: The scan Button
        stopButton: The stop Button
    """
    def __init__(self,mainWindow):
        super().__init__()

        # Create the Buttons
        self.scanButton = QPushButton("Start Scan")
        self.scanButton.setObjectName("Scan")
        self.stopButton = QPushButton("Stop")
        self.stopButton.setObjectName("Stop")

        self.scanButton.clicked.connect(mainWindow.slots.on_scanButton_clicked)
        self.stopButton.clicked.connect(mainWindow.slots.on_stopButton_clicked)

        # Add all the above elements to layout.
        layout = QHBoxLayout()
        layout.setContentsMargins(0,5,0,0)
        layout.setSpacing(5)
        layout.addWidget(self.scanButton)
        layout.addWidget(self.stopButton)

        self.setLayout(layout)

class AboutDialog(QDialog):
    """ About dialog's GUI. """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

    def set_GUI(self):
        """ Initialize GUI components. """

        # Create the logo
        logo = QLabel()
        logoPixmap = QPixmap(resource_path("logo.png"))
        logo.setPixmap(logoPixmap)

        # Create the information labels
        appname = QLabel("Chess Claim Tool")
        appname.setObjectName("appname")
        version = QLabel("Version 0.2.1")
        version.setObjectName("version")
        copyright = QLabel("Serntedakis Athanasios 2019 © All Rights Reserved")
        copyright.setObjectName("copyright")

        # Align All elements to the center.
        logo.setAlignment(Qt.AlignCenter)
        appname.setAlignment(Qt.AlignCenter)
        version.setAlignment(Qt.AlignCenter)
        copyright.setAlignment(Qt.AlignCenter)

        # Add all the above elements to layout.
        layout = QVBoxLayout()
        layout.addWidget(logo)
        layout.addWidget(appname)
        layout.addWidget(version)
        layout.addWidget(copyright)

        self.setLayout(layout)
