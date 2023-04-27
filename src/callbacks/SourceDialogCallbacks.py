"""
Chess Claim Tool: SourceDialogSlots

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

import os.path
import json
from threading import Thread, Lock
from PyQt5.QtCore import QThreadPool

from src.views.SourceDialogView import SourceHBox
from src.workers import CheckDownload, DownloadGames, MakePgn
from src.helpers import get_appdata_path, Status


class SourceDialogCallbacks:
    """ Handles user interaction with the GUI of the dialog. Each function
    is called when a specific action is performed by the user, to fulfill
    the request that corresponds to that action.

    Attributes:
        view:  The views of the Source Dialog.
        app_path(str): The path where the application will store & fetch data.
        filepaths(list[str]): A list that contains local files paths (from local and url sources) which are valid.
        downloads(dict): A dictionary containing the mappings of urls to local filepath that are valid.
    """

    def __init__(self, view) -> None:
        super().__init__()
        self.view = view

        self.app_path = get_appdata_path()
        self.threadPool = QThreadPool()
        self.filepaths = []
        self.downloads = dict()
        self.apply_mutex_lock = Lock()

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
