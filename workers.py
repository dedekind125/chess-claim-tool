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

from DownloadPgn import check_download, download_pgn
from helpers import get_appdata_path, Status


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
            self.source.set_status(Status.ok)
            if url not in self.slots.downloads:
                self.slots.add_valid_url(url, self.download_id)
        else:
            self.source.set_status(Status.error)


class DownloadGames(QThread):
    """ Downloads a list of sources from the web. It has 2 modes, either downloading
    continuously or just download once.

    Attributes:
        downloads: The list of urls to download.
        is_loop(bool): True if downloading continously, else download once.
        status_signal: Signal to update GUI.
    """
    status_signal = pyqtSignal(Status)
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
                status = Status.ok

                data = download_pgn(url)
                if not data:
                    status = Status.error

                self.status_signal.emit(status)

                filename = self.downloads[url]
                try:
                    with open(filename, "wb") as file:
                        file.write(data)
                except (FileNotFoundError, TypeError):
                    self.status_signal.emit(Status.error)
                    break
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
        model: An Object of Claims Class.
        lock: The fileLock for the games.pgn between CheckPgn and MakePgn threads.
        livePgnOption: The checkbox object on the menu.
        isRunning(bool): True if the thread is running, false otherwise.
        addEntrySignal: Signal to update the GUI.
        statusSignal: Signal to update the GUI.
    """
    addEntrySignal = pyqtSignal(list)
    statusSignal = pyqtSignal(str)

    def __init__(self, model, filename, lock, livePgnOption):
        super().__init__()
        self.filename = filename
        self.model = model
        self.isRunning = False
        self.lock = lock
        self.livePgnOption = livePgnOption

    def run(self):
        self.isRunning = True

        last_size = 0
        alreadyEntry = []
        entries = []

        time.sleep(1.2)  # For synchronization purposes.

        while (self.isRunning):
            try:
                size_of_pgn = os.path.getsize(self.filename)
            except FileNotFoundError:
                size_of_pgn = 0

            if (size_of_pgn != 0 and last_size != size_of_pgn):
                self.statusSignal.emit("active")

                self.checkPgnWorker = CheckPgn(self.model, self.filename, self.lock, self.livePgnOption)
                self.checkPgnWorker.start()

                """ While the pgn is being check here we take the entries and
                append it to the eventTable. This create a real time update
                experience for the user when the pgn has a lot of entries """

                while (self.checkPgnWorker.isAlive() or entries != alreadyEntry):
                    time.sleep(1)
                    entries = self.model.get_entries()

                    if not (self.isRunning): break

                    for entry in entries:
                        if (entry in alreadyEntry):
                            continue
                        else:
                            self.addEntrySignal.emit(entry)
                            alreadyEntry.append(entry)

                    entries = self.model.get_entries()

                last_size = size_of_pgn
                self.statusSignal.emit("wait")

            time.sleep(4)

    def stop(self):
        self.isRunning = False
        self.checkPgnWorker.stop()
        self.checkPgnWorker.join()


class Stop(QThread):
    """ Stops all the other running Threads(downloadWorker, makePgnWorker,scanWorker)
    and resets the model for the next scan.

    Attributes:
        model: Object of Claims Class.
        downloadWorker: Running thread, object of Download Class.
        makePgnWorker: Running thread, object of makePgn Class.
        scanWorker: Running thread, object of Scan Class.
        enableSignal: Signal to update the GUI.
        disableSignal: Signal to update the GUI.
    """

    enableSignal = pyqtSignal()
    disableSignal = pyqtSignal()

    def __init__(self, model, makePgnWorker, scanWorker, downloadWorker=None):
        super().__init__()
        self.model = model
        self.downloadWorker = downloadWorker
        self.makePgnWorker = makePgnWorker
        self.scanWorker = scanWorker

    def run(self):
        self.disableSignal.emit()

        # Stop all the treads
        try:
            self.downloadWorker.stop()
            self.downloadWorker.wait()
        except AttributeError:
            pass
        try:
            self.makePgnWorker.stop()
            self.scanWorker.stop()
            self.scanWorker.wait()
            self.makePgnWorker.join()
        except AttributeError:
            pass

        self.enableSignal.emit()

        """ Clear all the variables storing information from the model
        in order to be ready for the new scan. """

        self.model.empty_dontCheck()
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


class CheckPgn(Thread):
    """ Checks all the games of the pgn file.
    Attributes:
        filename: The path of the combined pgn file.
        model: An Object of Claims Class.
        lock: The fileLock for the games.pgn between CheckPgn and MakePgn threads.
        livePgnOption: The checkbox object on the menu.
        isRunning(bool): True if the thread is running, false otherwise.
    """

    def __init__(self, model, filename, lock, livePgnOption):
        super().__init__()
        self.model = model
        self.filename = filename
        self.lock = lock
        self.isRunning = True
        self.daemon = True
        self.livePgnOption = livePgnOption

    def run(self):
        self.lock.acquire()

        with open(self.filename) as pgn:

            # Loop to go through all of the games of the pgn.
            while (self.isRunning):
                try:
                    game = self.model.read_game(pgn)
                except:
                    continue
                if (game == None):  # There aren't any games left in the pgn.
                    break
                if (self.livePgnOption.isChecked() and game.headers["Result"] != "*"):
                    continue
                if (self.model.get_players(game) in self.model.dontCheck): continue
                self.model.check_game(game)

        self.lock.release()

    def stop(self):
        self.isRunning = False
