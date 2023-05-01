"""
Chess Claim Tool: ChessClaimController

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

import sys
import os.path
import json
from threading import Thread, Lock
from typing import List

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThreadPool

from src.views.dialog_view import SourceHBox
from src.views.main_view import ChessClaimView
from src.views.dialog_view import AddSourceDialog
from src.models.claims import Claims
from src.models.workers import DownloadGames, MakePgn, Scan, Stop
from src.helpers import get_appdata_path, Status


class ChessClaimController(QApplication):
    """ The Controller of the whole application.

    Attributes:
        model: Object of the Claims Class.
        view: The main views(GUI) of the application.
    """
    # __slots__ = ["view", "model", "sources_dialog"]

    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.view = ChessClaimView(self)
        self.model = Claims()
        self.sources_dialog = None

        self.make_pgn_worker = None
        self.stop_worker = None
        self.download_worker = None
        self.scan_worker = None

    def do_start(self) -> None:
        """ Perform startup operations and shows the dialog.
        Called once, on application startup. """

        app_path = get_appdata_path()
        if not os.path.exists(app_path):
            os.makedirs(app_path)

        self.view.set_gui()
        self.view.show()

    def on_sources_button_clicked(self) -> None:
        """ Initialize the Source Dialog MVC model and opens the Source Dialog.

        trigger: User clicks the "Add Sources" Button on the Main Window.
        """
        if not self.sources_dialog:
            self.sources_dialog = SourceDialogController()
            self.sources_dialog.view.accepted.connect(
                self.update_status_bar_sources)
            self.sources_dialog.do_start()
            return

        self.on_stop_button_clicked()
        self.sources_dialog.do_resume()

    def on_scan_button_clicked(self) -> None:
        """ Creates the necessary thread(workers) in order to scan the pgn(s)
        for the draw claims.

        trigger: User clicks the "Start Scan" Button on the Main Window.
        """
        if not self.sources_dialog or not self.sources_dialog.has_valid_sources():
            sources_warning()
            return

        """ If the scan thread is alive it means the scan button is already
        clicked before. So if the user click it again nothing should happen."""
        if self.scan_worker and self.scan_worker.is_running:
            return

        self.view.clear_table()
        self.view.change_scan_button_text(Status.WAIT)

        download_list = self.sources_dialog.get_download_list()
        if download_list:
            self.start_download_worker(download_list)

        games_pgn_mutex = Lock()
        self.start_make_png_worker(games_pgn_mutex)
        self.start_scan_worker(games_pgn_mutex)

    def on_stop_button_clicked(self) -> None:
        """ Creates a thread in order to stop all the other running Threads(
        downloadWorker, makePgnWorker,scanWorker)

        trigger: User clicks the "Stop" Button on the Main Window.
        """
        if self.scan_worker and not self.scan_worker.is_running:
            return

        if self.download_worker:
            self.stop_worker = Stop(
                self.model, self.make_pgn_worker, self.scan_worker, self.download_worker)
        else:
            self.stop_worker = Stop(
                self.model, self.make_pgn_worker, self.scan_worker)

        self.stop_worker.enable_signal.connect(self.on_stop_enable_status)
        self.stop_worker.disable_signal.connect(self.on_stop_disable_status)
        self.stop_worker.start()

    def on_about_clicked(self) -> None:
        """ Calls the views in order to display the About Dialog.
        trigger: User clicked the About section in the menu.
        """
        self.view.load_about_dialog()

    def on_stop_disable_status(self) -> None:
        """ Disables the "Scan" & "Stop" Buttons and the statusBar.
        Also changes the status of the scanButton.

        trigger: By the disableSignal(pyqtSignal)
        """
        self.view.change_scan_button_text(Status.WAIT)
        self.view.disable_buttons()
        self.view.disable_status_bar()

    def on_stop_enable_status(self) -> None:
        """ Enables the "Scan" & "Stop" Buttons and the statusBar.
        Also changes the status of the scanButton, download and scan info at the
        statusBar.

        trigger: By the enableSignal(pyqtSignal)
        """
        self.view.change_scan_button_text(Status.STOP)
        self.update_download_status(Status.STOP)
        self.update_bar_scan_status(Status.STOP)

        self.view.enable_buttons()
        self.view.enable_status_bar()

    def update_status_bar_sources(self) -> None:
        valid_sources = self.sources_dialog.get_valid_sources()
        if valid_sources:
            self.view.set_sources_status(Status.OK, valid_sources)
        else:
            self.view.set_sources_status(Status.ERROR)

    def update_claims_table(self, entry: list) -> None:
        self.view.add_item_to_table(entry)

    def update_download_status(self, status: Status) -> None:
        self.view.set_download_status(status)

    def update_bar_scan_status(self, status: Status) -> None:
        self.view.set_scan_status(status)

    def start_download_worker(self, downloads: List[str]) -> None:
        if not downloads:
            return
        self.download_worker = DownloadGames(downloads, True)
        self.download_worker.status_signal.connect(self.update_download_status)
        self.download_worker.start()

    def start_make_png_worker(self, lock: Lock) -> None:
        filepaths = self.sources_dialog.get_filepath_list()
        self.make_pgn_worker = MakePgn(filepaths, True, lock)
        self.make_pgn_worker.start()

    def start_scan_worker(self, lock: Lock) -> None:
        app_path = get_appdata_path()
        filename = os.path.join(app_path, "games.pgn")

        self.scan_worker = Scan(
            self.model, filename, lock, self.view.live_pgn_option)
        self.scan_worker.add_entry_signal.connect(self.update_claims_table)
        self.scan_worker.status_signal.connect(self.update_bar_scan_status)
        self.scan_worker.start()


class SourceDialogController:
    """ Handles user interaction with the GUI of the dialog. """
    # __slots__ = ['view']

    def __init__(self) -> None:
        self.view = AddSourceDialog(self)
        self.app_path = get_appdata_path()
        self.threadPool = QThreadPool()
        self.filepaths = []
        self.downloads = dict()
        self.apply_mutex_lock = Lock()

    def do_start(self) -> None:
        """ Perform startup operations and shows the dialog.
        Called once, on dialog startup.
        """

        self.view.set_gui()
        self.restore()
        self.view.show()

    def do_resume(self) -> None:
        """ Shows the dialog from the previous state the user left itself.
        That means that do_start has been preceded.
        """
        self.view.show()

    def get_filepath_list(self) -> List[str]:
        return self.filepaths

    def get_valid_sources(self) -> List[SourceHBox]:
        return self.view.sources

    def get_download_list(self) -> List[str]:
        return self.downloads

    def has_valid_sources(self) -> bool:
        return len(self.filepaths) > 0

    def restore(self) -> None:
        app_path = get_appdata_path()
        try:
            with open(os.path.join(app_path, "sources.json"), "r") as file:
                data = json.load(file)
                if not data:
                    self.view.add_default_source()
                for entry in data:
                    self.view.add_source(entry["option"], entry["value"])
        except json.decoder.JSONDecodeError:
            self.view.add_default_source()
        except FileNotFoundError:
            self.view.add_default_source()

    def on_delete_button_clicked(self, source_hbox) -> None:
        """ Removes a source.
        Args:
            source_hbox: The source to be deleted.

        Trigger: User clicks the "Delete" Button(Trash Icon) on the Source Dialog.
        """
        self.apply_mutex_lock.acquire()
        self.remove_hbox_refs(source_hbox)
        self.view.remove_hbox(source_hbox)
        self.apply_mutex_lock.release()

    def remove_hbox_refs(self, hbox: SourceHBox) -> None:
        """ Removes the entries (values) of the target sourceHbox from the downloads and filepaths structures
        Args:
            hbox: The SourceHbox for which the values are removed.
        """
        value = hbox.get_value()
        if hbox.has_url() and value in self.downloads:
            filepath = self.downloads[value]
            self.filepaths.remove(filepath)
            del self.downloads[value]
        elif hbox.has_local() and value in self.filepaths:
            self.filepaths.remove(value)

    def on_apply_button_clicked(self) -> None:
        """ Checks validity of all sources. Creates all the
        list(filepathList,downloadList,validSources) and sets the status of each source.

        Trigger: User clicks the "Apply" Button on the Source Dialog.
        """
        self.apply_mutex_lock.acquire()

        self.filepaths = []
        self.downloads = dict()

        # Create a Thread to complete the operations.
        apply_thread = Thread(target=self.on_apply_thread)
        apply_thread.daemon = True
        apply_thread.start()

    def on_ok_button_clicked(self) -> None:
        """ Closes the Source Dialog and performs all the necessary operations depending on
        the user input. These operations are:
            1) Download the pgn files, if any
            2) Make the games.pgn from all the sources, if there are valid sources.

        Trigger: User clicks the "OK" Button of the Source Dialog.
        """

        # Create a Thread to complete the operations.
        exit_thread = Thread(target=self.on_exit_thread)
        exit_thread.daemon = True
        exit_thread.start()

        # Close the Dialog
        self.view.accept()
        self.view.close()

    def on_apply_thread(self) -> None:
        """ Function called by Thread to perform the operations of the on_applyButton_clicked."""
        download_id = 0
        for source_hbox in self.view.sources:
            if source_hbox.has_url():
                self.threadPool.start(CheckDownload(
                    self, source_hbox, download_id))
                download_id += 1
            elif source_hbox.has_local():
                filepath = source_hbox.get_value()
                if os.path.exists(filepath):
                    source_hbox.set_status(Status.OK)
                    if filepath not in self.filepaths:
                        self.filepaths.append(filepath)
                else:
                    source_hbox.set_status(Status.ERROR)

        self.threadPool.waitForDone()
        self.apply_mutex_lock.release()

        if self.filepaths:
            self.view.enable_ok_button()

    def on_exit_thread(self) -> None:
        """ Function called by Thread to perform the operations of the on_okButton_clicked."""

        # Download the pgn files
        download_list_worker = DownloadGames(self.downloads)
        download_list_worker.start()
        download_list_worker.wait()

        #  Make the games.pgn
        make_pgn_worker = MakePgn(self.filepaths)
        make_pgn_worker.start()
        make_pgn_worker.join()

        self.save_sources()

    def save_sources(self) -> None:
        """ Saves the valid sources to the JSON file """
        data = [{"option": source.get_source_index(), "value": source.get_value()}
                for source in self.view.sources]
        with open(os.path.join(self.app_path, 'sources.json'), 'w') as file:
            json.dump(data, file, indent=4)

    def add_valid_url(self, url: str, download_id: int) -> None:
        """ Adds an already valid url into the downloads and filepath structures
        Args:
            url: The valid url to be added
            download_id: A unique id that will be used to map the url to the local downloaded file.
        """
        filepath = os.path.join(self.app_path, f"games{download_id}.pgn")
        if url not in self.downloads:
            self.downloads[url] = filepath

        if filepath not in self.filepaths:
            self.filepaths.append(filepath)
