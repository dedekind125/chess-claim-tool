"""
Chess Claim Tool: SourceDialogView

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
from PyQt5.QtWidgets import (QDialog, QWidget, QComboBox, QLineEdit, QPushButton,
                            QLabel, QHBoxLayout, QCheckBox, QVBoxLayout, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from functools import partial
from helpers import resource_path

class AddSourceDialog(QDialog):
    """ The dialog's GUI.
    Attributes:
        sources(list of SourceHBox): A list of all the sources
        sourcesCounter(int): The number of the sources in the dialog.
    """
    def __init__(self):
        super().__init__()
        self.setModal(True)
        self.setMinimumWidth(420)
        self.resize(420, 100)
        self.iconsSize = 20
        self.setWindowTitle("PGN Sources")

        """ Removes the "?" from the dialog (visible at Windows OS) """
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.sources = []
        self.sourcesCounter = 0

    def set_GUI(self):
        """ Initialize GUI components. """

        # Create the first Horizontal Source Box.
        self.sourceHBox = SourceHBox(self)
        self.sources.append(self.sourceHBox)
        self.sourcesCounter = self.sourcesCounter+1

        # Create the Apply & Ok Button Box.
        self.bottomBox = BottomBox(self)

        # Create the Add New Source Icon.
        addsourceButton = QPushButton("")
        addsourceButton.setIcon(QIcon(resource_path("add_icon.png")))
        addsourceButton.setIconSize(QSize(self.iconsSize+4,self.iconsSize+4))
        addsourceButton.setObjectName('AddSource')
        addsourceButton.clicked.connect(self.on_addsourceButton_clicked)

        # Add all the above elements to layout.
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.sourceHBox)
        self.layout.addWidget(addsourceButton,1,Qt.AlignRight)
        self.layout.addWidget(self.bottomBox)
        self.setLayout(self.layout)
        self.adjustSize()

    def on_addsourceButton_clicked(self):
        """Adds a new Horizontal Source Box below the existing ones.
        Trigger:
            User clicks the "+" button of the dialog.
        """
        self.sourcesCounter = self.sourcesCounter+1
        sourceHBox = SourceHBox(self)
        self.sources.append(sourceHBox)
        self.layout.insertWidget(self.sourcesCounter-1,sourceHBox)

    def add_source(self,option,value):
        """ Adds a source Horizontal Box.
        Args:
            option(int): 0: Web-url, 1: Local File
            value(str): The url or the local file path of the pgn.
        """
        if(self.sourceHBox.get_value() == ""):
            self.sourceHBox.set_source(option)
            self.sourceHBox.set_value(value)
        else:
            self.sourcesCounter = self.sourcesCounter+1
            sourceHBox = SourceHBox(self)
            sourceHBox.set_source(option)
            sourceHBox.set_value(value)
            self.sources.append(sourceHBox)
            self.layout.insertWidget(self.sourcesCounter-1,sourceHBox)

    def set_slots(self, slots):
        """ Connect the Slots """
        self.slots = slots

    def get_remember_option(self):
        return self.bottomBox.rememberOption

class SourceHBox(QWidget):
    """ Provide a Horizontal Box with a Combo Box a Line Edit for user input,
    a Choose File Button in case of the Local File Option, a Status Image
    and a Delete Button.

    Attributes:
        dialog: The Source Dialog with the Horizontal Box is located on.
    """
    def __init__(self,dialog):
        super().__init__()
        self.dialog = dialog

        # Create the Combo Box with 2 options.
        self.selectSource = QComboBox()
        self.selectSource.addItems(["Web(url)","Local"])
        self.selectSource.currentIndexChanged.connect(self.select_change)

        # Create the Line Edit for user input.
        self.sourceValue = QLineEdit()
        self.sourceValue.textChanged.connect(self.line_edit_change)
        self.sourceValue.setPlaceholderText("http://example.com/pgn/games.pgn")

        # Choose File Button in case of the Local File Option
        self.chooseButton = QPushButton("Choose File")
        self.chooseButton.clicked.connect(self.on_chooseButton_clicked)
        self.chooseButton.setHidden(True)

        # Create the Status Image
        self.statusImage = QLabel()
        self.ok_pixmap = QPixmap(resource_path("check_icon.png"))
        self.error_pixmap = QPixmap(resource_path("error_icon.png"))

        # Create the Delete Button
        deleteButton = QPushButton("")
        deleteButton.setIcon(QIcon(resource_path("delete_icon.png")))
        deleteButton.setIconSize(QSize(self.dialog.iconsSize,self.dialog.iconsSize))
        deleteButton.setObjectName('DeleteSource')
        deleteButton.clicked.connect(partial(self.dialog.slots.on_deleteButton_clicked,self))

        # Add all the above elements to layout.
        layout = QHBoxLayout()
        layout.addWidget(self.selectSource)
        layout.addWidget(self.sourceValue)
        layout.addWidget(self.chooseButton)
        layout.addWidget(self.statusImage)
        layout.addWidget(deleteButton)

        self.setLayout(layout)
        self.adjustSize()

    def set_value(self,text):
        self.sourceValue.setText(text)

    def set_source(self,index):
        self.selectSource.setCurrentIndex(index)

    def get_value(self):
        return self.sourceValue.text()

    def get_source_index(self):
        return self.selectSource.currentIndex()

    def line_edit_change(self):
        self.statusImage.clear()

    def select_change(self,index):
        """ Actions when the user select a different option at the Combo Box.
        Args:
            index: The index of the option. 0: Web Url, 1: Local File
        """
        self.statusImage.clear()
        if(index == 0): # Web download option
            self.chooseButton.setHidden(True)
            self.sourceValue.setText("")
            self.sourceValue.setPlaceholderText("http://example.com/pgn/games.pgn")
        elif(index == 1): # Local source option
            self.chooseButton.setHidden(False)
            self.sourceValue.setText("")
            self.sourceValue.setPlaceholderText("")

    def set_status(self,status):
        """ Adds the Status Image.
        Args:
            status(str): The validity of the source. It has two states:
                         "ok": The source is valid.
                         "error": The source is invalid.
        """
        if (status == "ok"):
            self.statusImage.setPixmap(self.ok_pixmap.scaled(self.dialog.iconsSize,self.dialog.iconsSize,transformMode=Qt.SmoothTransformation))
        elif (status == "error"):
            self.statusImage.setPixmap(self.error_pixmap.scaled(self.dialog.iconsSize,self.dialog.iconsSize,transformMode=Qt.SmoothTransformation))

    def on_chooseButton_clicked(self):
        """ Opens a file explorer for the user to choose a file.
        Trigger: User clicks the "Choose File" button of the Horizontal Box.
        """
        fileName,_= QFileDialog.getOpenFileName(self,"Select File", "","PGN Files (*.pgn)")
        if fileName: self.sourceValue.setText(fileName)

class BottomBox(QWidget):
    """ Provides a Horizontal Box with two Buttons and a Check Box.
    Attributes:
        dialog: The Source Dialog with the Horizontal Box is located on.
    """

    def __init__(self,dialog):
        super().__init__()
        self.dialog = dialog

        # Create the Apply and Ok Buttons.
        applyButton = QPushButton("Apply")
        okButton = QPushButton("ΟΚ")
        applyButton.setObjectName("apply")
        okButton.setObjectName("ok")
        applyButton.clicked.connect(self.dialog.slots.on_applyButton_clicked)
        okButton.clicked.connect(self.dialog.slots.on_okButton_clicked)

        # Create the Check Box
        self.rememberOption = QCheckBox("Remember Sources")
        self.rememberOption.setLayoutDirection(Qt.RightToLeft)
        self.rememberOption.setChecked(1)

        # Add all the above elements to layout.
        layout = QHBoxLayout()
        layout.setSpacing(30)
        layout.addWidget(applyButton)
        layout.addWidget(okButton)
        layout.addWidget(self.rememberOption)

        self.setLayout(layout)
