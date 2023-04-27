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
from typing import Optional, Callable

from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QStandardItemModel, QPixmap, QMovie, QStandardItem, QColor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QTreeView, QPushButton, QDesktopWidget,
                             QAbstractItemView, QHBoxLayout, QVBoxLayout, QLabel, QStatusBar, QMessageBox, QAction,
                             QDialog)

from src.Claims import ClaimType
from src.helpers import resource_path, Status

if platform.system() == "Darwin":
    from src.MacNotification import Notification as Notification
elif platform.system() == "Windows":
    from win10toast import ToastNotifier as Notification


def sources_warning():
    """ Displays a Warning Dialog. """
    warning_dialog = QMessageBox()
    warning_dialog.setIcon(warning_dialog.Warning)
    warning_dialog.setWindowTitle("Warning")
    warning_dialog.setText("PGN File(s) Not Found")
    warning_dialog.setInformativeText(
        "Please enter at least one valid PGN source.")
    warning_dialog.exec()


class ChessClaimView(QMainWindow):
    ICON_SIZE = 16
    __slots__ = ["callbacks", "claims_table", "live_pgn_option", "claims_table_model", "button_box", "ok_pixmap",
                 "error_pixmap", "source_label", "source_image", "download_label", "download_image", "scan_label",
                 "scan_image", "spinner", "status_bar", "about_dialog", "notification"]

    def __init__(self) -> None:
        super().__init__()

        self.callbacks = None
        self.resize(720, 275)
        self.setWindowTitle('Chess Claim Tool')
        self.center()

        self.claims_table = QTreeView()
        self.live_pgn_option = QAction('Live PGN', self)
        self.claims_table_model = QStandardItemModel()
        self.button_box = ButtonBox()
        self.ok_pixmap = QPixmap(resource_path("check_icon.png"))
        self.error_pixmap = QPixmap(resource_path("error_icon.png"))
        self.source_label = QLabel()
        self.source_image = QLabel()
        self.download_label = QLabel()
        self.download_image = QLabel()
        self.scan_label = QLabel()
        self.scan_image = QLabel()
        self.spinner = QMovie(resource_path("spinner.gif"))
        self.status_bar = QStatusBar()
        self.about_dialog = AboutDialog()

        self.notification = Notification()

    def center(self) -> None:
        """ Centers the window on the screen """
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2))

    def set_gui(self) -> None:
        """ Initialize GUI components. """

        self.create_menu()
        self.create_claims_table()
        self.create_status_bar()

        self.button_box.set_scan_button_callback(
            self.callbacks.on_scan_button_clicked)
        self.button_box.set_stop_button_callback(
            self.callbacks.on_stop_button_clicked)

        container_layout = QVBoxLayout()
        container_layout.setSpacing(0)
        container_layout.addWidget(self.claims_table)
        container_layout.addWidget(self.button_box)

        container_widget = QWidget()
        container_widget.setLayout(container_layout)

        self.setCentralWidget(container_widget)
        self.setStatusBar(self.status_bar)

    def create_menu(self) -> None:
        self.live_pgn_option.setCheckable(True)
        about_action = QAction('About', self)

        menu_bar = self.menuBar()

        options_menu = menu_bar.addMenu('&Options')
        options_menu.addAction(self.live_pgn_option)

        about_menu = menu_bar.addMenu('&Help')
        about_menu.addAction(about_action)
        about_action.triggered.connect(self.callbacks.on_about_clicked)

    def create_claims_table(self) -> None:
        self.claims_table.setFocusPolicy(Qt.NoFocus)
        self.claims_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.claims_table.header().setDefaultAlignment(Qt.AlignCenter)
        self.claims_table.setSortingEnabled(True)
        self.claims_table.setIndentation(0)
        self.claims_table.setUniformRowHeights(True)

        labels = ["#", "Timestamp", "Type", "Board", "Players", "Move"]
        self.claims_table_model.setHorizontalHeaderLabels(labels)
        self.claims_table.setModel(self.claims_table_model)

    def create_status_bar(self) -> None:
        sources_button = QPushButton("Add Sources")
        sources_button.setObjectName("sources")
        sources_button.clicked.connect(
            self.callbacks.on_sources_button_clicked)

        self.source_image.setObjectName("source-image")
        self.download_image.setObjectName("download-image")
        self.scan_image.setObjectName("scan-image")

        self.spinner.setScaledSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.spinner.start()

        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.addWidget(self.source_label)
        self.status_bar.addWidget(self.source_image)
        self.status_bar.addWidget(self.download_label)
        self.status_bar.addWidget(self.download_image)
        self.status_bar.addWidget(self.scan_label)
        self.status_bar.addWidget(self.scan_image)
        self.status_bar.addPermanentWidget(sources_button)
        self.status_bar.setContentsMargins(10, 5, 9, 5)

    def resize_claims_table(self) -> None:
        """ Resize the table (if needed) after the insertion of a new element. """
        for index in range(0, 6):
            self.claims_table.resizeColumnToContents(index)

    def set_callbacks(self, callbacks) -> None:
        """ Connect the Slots """
        self.callbacks = callbacks

    def add_item_to_table(self, entry: list) -> None:
        """ Add new row to the claimsTable
        Args:

        """
        claim_type, board_number, players, move = entry[:4]

        self.remove_rows_by_claim_type(claim_type, players)

        timestamp = str(datetime.now().strftime('%H:%M:%S'))
        row = []
        count = str(self.claims_table_model.rowCount() + 1)
        items = [count, timestamp, claim_type.value,
                 board_number, players, move]

        """ Convert each item(str) to QStandardItem, make the necessary stylistic
        additions and append it to row."""
        for idx, item in enumerate(items):
            standard_item = self.create_standard_item(item, idx)
            row.append(standard_item)

        self.claims_table_model.appendRow(row)
        self.resize_claims_table()

        # Always the last row(the bottom of the table) should be visible.
        self.claims_table.scrollToBottom()
        self.notify(claim_type, players, move)

    @staticmethod
    def create_standard_item(item: list, idx: int) -> QStandardItem:
        item = QStandardItem(item)
        item.setTextAlignment(Qt.AlignCenter)

        if idx == 2:
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        if item == ClaimType.FIVEFOLD.value or item == ClaimType.SEVENTYFIVE_MOVES.value:
            item.setData(QColor(255, 0, 0), Qt.ForegroundRole)

        return item

    def notify(self, claim_type: ClaimType, players: str, move: str) -> None:
        """ Send notification depending on the OS.
        Args:
            claim_type: The type of the draw (3 Fold Repetition, 5 Fold Repetition,
                                        50 Moves Rule, 75 Moves Rule).
            players: The names of the players.
            move: With which move the draw is valid.
        """
        if platform.system() == "Darwin":
            self.notification.clearNotifications()
            self.notification.notify(claim_type.value, players, move)
        elif platform.system() == "Windows":
            self.notification.show_toast(claim_type.value,
                                         f"{players} \n {move}",
                                         icon_path=resource_path("logo.ico"),
                                         duration=5,
                                         threaded=True)

    def remove_row_by_index(self, index: int) -> None:
        """ Remove element from the claimsTable.
        Args:
            index: The index of the row we want to remove. First row has index=0.
        """
        self.claims_table_model.removeRow(index)

    def remove_rows_by_claim_type(self, claim_type: ClaimType, players: str) -> None:
        """ Removes a existing row from the Claims Table when same players made
        the same type of draw with a new move - or they made 5-Fold Repetition
        over the 3-Fold or 75 Moves Rule over 50 moves Rule.

        Args:
            claim_type: The type of the draw (3-Fold Repetition, 5-Fold Repetition,
                                        50 Moves Rule, 75 Moves Rule).
            players: The names of the players.
        """
        for index in range(self.claims_table_model.rowCount()):
            try:
                model_type = self.claims_table_model.item(index, 2).text()
                model_players = self.claims_table_model.item(index, 4).text()
            except AttributeError:
                model_type = ""
                model_players = ""

            if model_type == claim_type.value and model_players == players:
                self.remove_row_by_index(index)
                self.reset_column_count()
                break
            elif (claim_type is ClaimType.FIVEFOLD and
                  model_type == ClaimType.THREEFOLD.value and
                  model_players == players):
                self.remove_row_by_index(index)
                self.reset_column_count()
                break
            elif (claim_type is ClaimType.SEVENTYFIVE_MOVES and
                  model_type == ClaimType.FIFTY_MOVES.value and
                  model_players == players):
                self.remove_row_by_index(index)
                self.reset_column_count()
                break

    def reset_column_count(self) -> None:
        """ Re-index the numbers in the first column of Claims Table
        (the "#" column) after the removal of rows (see remove_rows()).
        """
        row_count = self.claims_table_model.rowCount()
        for index in range(row_count):
            standard_item = QStandardItem(str(index + 1))
            standard_item.setTextAlignment(Qt.AlignCenter)
            self.claims_table_model.setItem(index, 0, standard_item)

    def clear_table(self):
        """ Clear all the elements off the Claims Table. """
        for index in range(self.claims_table_model.rowCount()):
            self.claims_table_model.removeRow(0)

    def set_sources_status(self, status: Status, valid_sources: Optional[str] = None):
        """ Adds the sources in the statusBar.
        Args:
            status(str): The status of the validity of the sources.
                "ok": At least one source is valid.
                "error": None of the sources are valid.
            valid_sources(list): The list of valid sources, if there is any.
                This list is used here to display the ToolTip.
        """
        if valid_sources is None:
            valid_sources = []
        self.source_label.setText("Sources:")

        # Set the ToolTip if there are sources.
        try:
            text = ""
            for idx, source in enumerate(valid_sources):
                text += f"{idx + 1}) {source.get_value()}"
                if idx != len(valid_sources) - 1:
                    text += "\n"
            self.source_label.setToolTip(text)
        except TypeError:
            pass

        self.set_pixmap(self.source_image, status)

    def set_download_status(self, status: Status) -> None:
        """ Adds download status in the statusBar.
        Args:
            status(str): The status of the download(s).
                "ok": The download of the sources is successful.
                "error": The download of the sources failed.
                "stop": The download process stopped.
        """
        timestamp = str(datetime.now().strftime('%H:%M:%S'))
        self.download_label.setText(f"{timestamp} Download:")

        self.set_pixmap(self.download_image, status)

        if status is Status.STOP:
            self.download_image.clear()
            self.download_label.clear()

    def set_scan_status(self, status: Status) -> None:
        """ Adds the scan status in the statusBar. """
        timestamp = str(datetime.now().strftime('%H:%M:%S'))
        self.scan_label.setText(f"{timestamp} Scan:")
        self.set_pixmap(self.scan_image, status)

        if status is Status.ACTIVE:
            self.scan_image.clear()
            self.scan_image.setMovie(self.spinner)
        elif status is Status.STOP:
            self.scan_label.clear()
            self.scan_image.clear()

    def change_scan_button_text(self, status: Status) -> None:
        """ Changes the text of the scanButton depending on the status of the application.
        Args:
            status(str): The status of the scan process.
                "active": The scan process is active.
                "wait": The scan process is being terminated
                "stop": The scan process stopped.
        """
        if status is Status.ACTIVE:
            self.button_box.scan_button.setText("Scanning PGN...")
        elif status is Status.STOP:
            self.button_box.scan_button.setText("Start Scan")
        elif status is Status.WAIT:
            self.button_box.scan_button.setText("Please Wait")

    def set_pixmap(self, image: QLabel, status: Status):
        if status is Status.OK or status is Status.WAIT:
            image.setPixmap(
                self.ok_pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, transformMode=Qt.SmoothTransformation))
        elif status is Status.ERROR:
            image.setPixmap(
                self.error_pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, transformMode=Qt.SmoothTransformation))

    def enable_buttons(self):
        self.button_box.scan_button.setEnabled(True)
        self.button_box.stop_button.setEnabled(True)

    def disable_buttons(self):
        self.button_box.scan_button.setEnabled(False)
        self.button_box.stop_button.setEnabled(False)

    def enable_status_bar(self):
        """ Show download and scan status messages - if they were previously
        hidden (by disable_statusBar) - from the statusBar."""
        self.download_label.setVisible(True)
        self.scan_label.setVisible(True)
        self.download_image.setVisible(True)
        self.scan_image.setVisible(True)

    def disable_status_bar(self):
        """ Hide download and scan status messages from the statusBar. """
        self.download_label.setVisible(False)
        self.download_image.setVisible(False)
        self.scan_label.setVisible(False)
        self.scan_image.setVisible(False)

    def closeEvent(self, event: QEvent):
        """ Reimplement the close button
        If the program is actively scanning a pgn a warning dialog shall be raised
        in order to make sure that the user didn't clicked the close Button accidentally.
        Args:
            event: The exit QEvent.
        """
        try:
            if self.callbacks.scan_worker.is_running:
                exit_dialog = QMessageBox()
                exit_dialog.setWindowTitle("Warning")
                exit_dialog.setText("Scanning in Progress")
                exit_dialog.setInformativeText("Do you want to quit?")
                exit_dialog.setIcon(exit_dialog.Warning)
                exit_dialog.setStandardButtons(
                    QMessageBox.Yes | QMessageBox.Cancel)
                exit_dialog.setDefaultButton(QMessageBox.Cancel)
                replay = exit_dialog.exec()

                if replay == QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()
        except:
            event.accept()

    def load_about_dialog(self):
        """ Displays the About Dialog."""
        self.about_dialog.set_gui()
        self.about_dialog.show()


class ButtonBox(QWidget):
    """ Provides a Horizontal Box with two Buttons.
    Attributes:
        scan_button: The scan Button
        stop_button: The stop Button
    """
    __callbacks__ = ["scan_button", "stop_button"]

    def __init__(self):
        super().__init__()

        # Create the Buttons
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.setObjectName("Scan")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("Stop")

        # Add all the above elements to layout.
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.scan_button)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def set_scan_button_callback(self, on_clicked: Callable) -> None:
        self.scan_button.clicked.connect(on_clicked)

    def set_stop_button_callback(self, on_clicked: Callable) -> None:
        self.stop_button.clicked.connect(on_clicked)


class AboutDialog(QDialog):
    """ About dialog's GUI. """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowFlags(self.windowFlags() ^
                            Qt.WindowContextHelpButtonHint)

    def set_gui(self) -> None:
        """ Initialize GUI components. """

        # Create the logo
        logo = QLabel()
        logo_pixmap = QPixmap(resource_path("logo.png"))
        logo.setPixmap(logo_pixmap)

        # Create the information labels
        appname = QLabel("Chess Claim Tool")
        appname.setObjectName("appname")
        version = QLabel("Version 0.2.1")
        version.setObjectName("version")
        copyright = QLabel("Serntedakis Athanasios 2022 © All Rights Reserved")
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
