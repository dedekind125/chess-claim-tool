"""
Chess Claim Tool: workers

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
import time
from threading import Thread

from PyQt5.QtCore import QRunnable, QThread, pyqtSignal
from chess.pgn import read_game

from src.Claims import get_players
from src.DownloadPgn import check_download, download_pgn
from src.helpers import get_appdata_path, Status


class CheckDownload(QRunnable):
    """ Checks if the web sources are valid. (Used by Source Dialog)
    Attributes:
        slots: Object of ChessClaimSlots.
        source: The web source to be checked.
    """
    __slots__ = ["slots", "source", "download_id"]

    def __init__(self, slots, source, download_id):
        super().__init__()
        self.slots = slots
        self.source = source
        self.download_id = download_id

    def run(self):
        url = self.source.get_value()
        if check_download(url):
            self.source.set_status(Status.OK)
            if url not in self.slots.downloads:
                self.slots.add_valid_url(url, self.download_id)
        else:
            self.source.set_status(Status.ERROR)


class DownloadGames(QThread):
    """ Downloads a list of sources from the web. It has 2 modes, either downloading
    continuously or just download once.

    Attributes:
        downloads: The list of urls to download.
        is_loop(bool): True if downloading continuously, else download once.
    """
    status_signal = pyqtSignal(Status)  # Signal to update GUI.
    INTERVAL = 4
    __slots__ = ["downloads", "is_loop", "is_running", "app_path"]

    def __init__(self, downloads, is_loop=False):
        super().__init__()
        self.downloads = downloads
        self.is_loop = is_loop
        self.is_running = False
        self.app_path = get_appdata_path()

    def run(self) -> None:
        self.is_running = True
        while self.is_running:
            for url in self.downloads:
                status = Status.OK
                data = download_pgn(url)
                if not data:
                    status = Status.ERROR

                self.status_signal.emit(status)
                filename = self.downloads[url]
                try:
                    with open(filename, "wb") as file:
                        file.write(data)
                except (FileNotFoundError, TypeError):
                    self.status_signal.emit(Status.ERROR)
                    continue
            if not self.is_loop:
                break
            time.sleep(self.INTERVAL)

    def stop(self):
        self.is_running = False


class Scan(QThread):
    """ Continuously looks for a new games.pgn to scan. It creates another thread
    to check the new pgn while it updates the GUI(claimsTable) with new entries.

    Attributes:
        filename: The path of the combined pgn file.
        claims: An Object of Claims Class.
        lock: The fileLock for the games.pgn between CheckPgn and MakePgn threads.
        live_pgn_option: The checkbox object on the menu.
        is_running(bool): True if the thread is running, false otherwise.
    """
    __slots__ = ["is_running", "filename", "claims", "lock", "live_pgn_option"]

    add_entry_signal = pyqtSignal(tuple)    # Signal to update the GUI.
    status_signal = pyqtSignal(Status)      # Signal to update the GUI.
    INTERVAL = 4

    def __init__(self, claims, filename, lock, live_pgn_option):
        super().__init__()
        self.is_running = False
        self.filename = filename
        self.claims = claims
        self.lock = lock
        self.live_pgn_option = live_pgn_option

    def run(self):
        self.is_running = True
        last_size = 0
        time.sleep(1.2)  # For synchronization purposes.

        while self.is_running:
            try:
                size_of_pgn = os.path.getsize(self.filename)
            except FileNotFoundError:
                size_of_pgn = 0

            if self.is_file_updated(last_size, size_of_pgn):
                self.status_signal.emit(Status.ACTIVE)
                self.check_pgn()

            self.status_signal.emit(Status.WAIT)
            last_size = size_of_pgn

            if not self.is_running:
                break
            time.sleep(self.INTERVAL)

    def check_pgn(self):
        self.lock.acquire()
        with open(self.filename) as pgn:
            while self.is_running:
                game = read_game(pgn)
                if not game:
                    break
                if self.live_pgn_option.isChecked() and game.headers["Result"] != "*":
                    continue
                if get_players(game) in self.claims.dont_check:
                    continue
                entries = self.claims.check_game(game)
                for entry in entries:
                    self.add_entry_signal.emit(entry)

        self.lock.release()

    @staticmethod
    def is_file_updated(last_size, current_size):
        return current_size != 0 and last_size != current_size

    def stop(self):
        self.is_running = False


class Stop(QThread):
    """ Stops all the other running Threads(downloadWorker, makePgnWorker,scanWorker)
    and resets the model for the next scan.

    Attributes:
        model: Object of Claims Class.
        download_worker: Running thread, object of Download Class.
        make_pgn_worker: Running thread, object of makePgn Class.
        scan_worker: Running thread, object of Scan Class.
    """

    enable_signal = pyqtSignal()  # Signal to update the GUI.
    disable_signal = pyqtSignal()  # Signal to update the GUI.

    def __init__(self, model, make_pgn_worker, scan_worker, download_worker=None):
        super().__init__()
        self.model = model
        self.download_worker = download_worker
        self.make_pgn_worker = make_pgn_worker
        self.scan_worker = scan_worker

    def run(self):
        self.disable_signal.emit()

        # Stop all the treads
        try:
            self.download_worker.stop()
            self.download_worker.wait()
        except AttributeError:
            pass
        try:
            self.make_pgn_worker.stop()
            self.scan_worker.stop()
            self.scan_worker.wait()
            self.make_pgn_worker.join()
        except AttributeError:
            pass

        self.enable_signal.emit()

        """ Clear all the variables storing information from the model
        in order to be ready for the new scan. """
        self.model.empty_dont_check()
        self.model.empty_entries()


class MakePgn(Thread):
    """ Makes a combined pgn of all the sources available (using the filePathList).
    It has 2 modes, either make a new pgn continuously or just once.

    Attributes:
        filepaths: A list that contains all the files path(or url) which are valid.
        is_loop: True if making the pgn continously, else makes the pgn once.
        lock: The fileLock for the games.pgn between CheckPgn and MakePgn threads.
    """
    INTERVAL = 4
    __slots__ = ["filepaths", "is_loop", "is_running", "lock", "daemon"]

    def __init__(self, filepaths, is_loop=False, lock=None):
        super().__init__()
        self.filepaths = filepaths
        self.is_loop = is_loop
        self.is_running = False
        self.lock = lock
        self.daemon = True

        app_path = get_appdata_path()
        self.filename = os.path.join(app_path, "games.pgn")

    def run(self) -> None:
        self.is_running = True
        while self.is_running:
            data = bytes()
            for filepath in self.filepaths:
                try:
                    with open(filepath, "rb") as in_file:
                        data += "\n\n".encode("utf-8") + in_file.read()
                except FileNotFoundError:
                    continue

            if self.lock:
                self.lock.acquire()
            with open(self.filename, "wb") as file:
                file.write(data)
            if self.lock:
                self.lock.release()

            if not self.is_loop:
                break
            time.sleep(self.INTERVAL)

    def stop(self):
        self.is_running = False
