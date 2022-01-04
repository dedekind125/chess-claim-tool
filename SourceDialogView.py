"""
Chess Claim Tool: SourceDialogView

Copyright (C) 2022 Serntedakis Athanasios <thanserd@hotmail.com>

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

from functools import partial

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QDialog, QWidget, QComboBox, QLineEdit, QPushButton,
                             QLabel, QHBoxLayout, QVBoxLayout, QFileDialog)

from helpers import resource_path, Status


class AddSourceDialog(QDialog):
    """ The dialog's GUI.
    Attributes:
        sources(list of SourceHBox): A list of all the sources
        sources_cnt(int): The number of the sources in the dialog.
    """
    ICON_SIZE = 20
    __slots__ = ['slots', 'layout', 'bottomBox', 'sources', 'source_cnt']

    def __init__(self):
        super().__init__()
        self.setModal(True)
        self.setMinimumWidth(420)
        self.resize(420, 100)
        self.setWindowTitle("PGN Sources")

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.slots = None
        self.layout = None
        self.bottomBox = None
        self.sources = []
        self.sources_cnt = 0

    def set_gui(self) -> None:
        """ Initialize GUI components. """

        # Create the Apply & Ok Button Box.
        self.bottomBox = BottomBox(self)

        # Create the Add New Source Icon.
        add_source_button = QPushButton("")
        add_source_button.setIcon(QIcon(resource_path("add_icon.png")))
        add_source_button.setIconSize(QSize(self.ICON_SIZE + 4, self.ICON_SIZE + 4))
        add_source_button.setObjectName('AddSource')
        add_source_button.clicked.connect(self.on_add_source_button_clicked)

        # Add all the above elements to layout.
        self.layout = QVBoxLayout()
        self.layout.addWidget(add_source_button, 1, Qt.AlignRight)
        self.layout.addWidget(self.bottomBox)
        self.setLayout(self.layout)
        self.adjustSize()

    def on_add_source_button_clicked(self) -> None:
        """Adds a new Horizontal Source Box below the existing ones.
        Trigger:
            User clicks the "+" button of the dialog.
        """
        self.add_default_source()

    def add_source(self, option: int, value: str) -> None:
        """ Adds a source Horizontal Box.
        Args:
            option(int): 0: Web-url, 1: Local File
            value(str): The url or the local file path of the pgn.
        """
        self.sources_cnt = self.sources_cnt + 1
        source_hbox = SourceHBox(self)
        source_hbox.set_source(option)
        source_hbox.set_value(value)
        self.sources.append(source_hbox)
        self.layout.insertWidget(self.sources_cnt - 1, source_hbox)

    def add_default_source(self) -> None:
        self.add_source(0, "")

    def set_slots(self, slots) -> None:
        self.slots = slots

    def enable_ok_button(self) -> None:
        self.bottomBox.change_ok_status(True)

    def disable_ok_button(self) -> None:
        self.bottomBox.change_ok_status(False)

    def remove_hbox(self, hbox) -> None:
        self.layout.removeWidget(hbox)
        self.sources.remove(hbox)
        self.sources_cnt -= 1

        hbox.deleteLater()
        self.adjustSize()


class SourceHBox(QWidget):
    """ Provide a Horizontal Box with a Combo Box a Line Edit for user input,
    a Choose File Button in case of the Local File Option, a Status Image
    and a Delete Button.

    Attributes:
        dialog: The Source Dialog with the Horizontal Box is located on.
    """
    __slots__ = ['dialog', 'select_source', 'source_value', 'choose_button', 'status_image', 'ok_pixmap',
                 'error_pixmap']

    def __init__(self, dialog: AddSourceDialog) -> None:
        super().__init__()
        self.dialog = dialog

        # Create the Combo Box with 2 options.
        self.select_source = QComboBox()
        self.select_source.addItems(["Web(url)", "Local"])
        self.select_source.currentIndexChanged.connect(self.select_change)

        # Create the Line Edit for user input.
        self.source_value = QLineEdit()
        self.source_value.textChanged.connect(self.line_edit_changed)
        self.source_value.setPlaceholderText("https://example.com/pgn/games.pgn")

        # Choose File Button in case of the Local File Option
        self.choose_button = QPushButton("Choose File")
        self.choose_button.clicked.connect(self.on_choose_button_clicked)
        self.choose_button.setHidden(True)

        # Create the Status Image
        self.status_image = QLabel()
        self.ok_pixmap = QPixmap(resource_path("check_icon.png"))
        self.error_pixmap = QPixmap(resource_path("error_icon.png"))

        # Create the Delete Button
        delete_button = QPushButton("")
        delete_button.setIcon(QIcon(resource_path("delete_icon.png")))
        delete_button.setIconSize(QSize(self.dialog.ICON_SIZE, self.dialog.ICON_SIZE))
        delete_button.setObjectName('DeleteSource')
        delete_button.clicked.connect(partial(self.dialog.slots.on_delete_button_clicked, self))

        # Add all the above elements to layout.
        layout = QHBoxLayout()
        layout.addWidget(self.select_source)
        layout.addWidget(self.source_value)
        layout.addWidget(self.choose_button)
        layout.addWidget(self.status_image)
        layout.addWidget(delete_button)

        self.setLayout(layout)
        self.adjustSize()

    def set_value(self, text: str) -> None:
        self.source_value.setText(text)

    def set_source(self, index: int) -> None:
        self.select_source.setCurrentIndex(index)

    def get_value(self) -> str:
        return self.source_value.text()

    def get_source_index(self) -> int:
        return self.select_source.currentIndex()

    def has_url(self) -> bool:
        return self.select_source.currentIndex() == 0

    def has_local(self) -> bool:
        return self.select_source.currentIndex() == 1

    def line_edit_changed(self) -> None:
        self.dialog.disable_ok_button()
        self.status_image.clear()

    def select_change(self, index: int) -> None:
        """ Actions when the user selects a different option at the Combo Box.
        Args:
            index: The index of the option. 0: Web Url, 1: Local File
        """
        self.line_edit_changed()
        if index == 0:  # Web download option
            self.choose_button.setHidden(True)
            self.source_value.setText("")
            self.source_value.setPlaceholderText("https://example.com/pgn/games.pgn")
        elif index == 1:  # Local source option
            self.choose_button.setHidden(False)
            self.source_value.setText("")
            self.source_value.setPlaceholderText("")

    def set_status(self, status: Status) -> None:
        """ Adds the Status Image.
        Args:
            status(str): The validity of the source. It has two states:
                         "ok": The source is valid.
                         "error": The source is invalid.
        """
        if status is Status.ok:
            self.status_image.setPixmap(self.ok_pixmap.scaled(self.dialog.ICON_SIZE, self.dialog.ICON_SIZE,
                                                              transformMode=Qt.SmoothTransformation))
        elif status is Status.error:
            self.status_image.setPixmap(self.error_pixmap.scaled(self.dialog.ICON_SIZE, self.dialog.ICON_SIZE,
                                                                 transformMode=Qt.SmoothTransformation))

    def on_choose_button_clicked(self) -> None:
        """ Opens a file explorer for the user to choose a file.
        Trigger: User clicks the "Choose File" button of the Horizontal Box.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "Select File", "", "PGN Files (*.pgn)")
        if filename:
            self.source_value.setText(filename)


class BottomBox(QWidget):
    """ Provides a Horizontal Box with two Buttons and a checkbox.
    Attributes:
        dialog: The Source Dialog with the Horizontal Box is located on.
    """
    __slots__ = ['dialog', 'ok_button']

    def __init__(self, dialog: AddSourceDialog) -> None:
        super().__init__()
        self.dialog = dialog

        # Create the Apply and Ok Buttons.
        apply_button = QPushButton("Apply")
        self.ok_button = QPushButton("ΟΚ")
        apply_button.setObjectName("apply")
        self.ok_button.setObjectName("ok")
        apply_button.clicked.connect(self.dialog.slots.on_apply_button_clicked)
        self.ok_button.clicked.connect(self.dialog.slots.on_ok_button_clicked)
        self.ok_button.setEnabled(False)

        # Add all the above elements to layout.
        layout = QHBoxLayout()
        layout.setSpacing(30)
        layout.addWidget(apply_button)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def change_ok_status(self, status: bool) -> None:
        self.ok_button.setEnabled(status)
