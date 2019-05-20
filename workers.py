"""
Chess Claim Tool: workers

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
import os.path, time, chess.pgn
from threading import Thread
from PyQt5.QtCore import QRunnable, QThread, pyqtSignal
from DownloadPgn import DownloadPgn
from helpers import get_appData_path

class CheckDownload(QRunnable):
    """ Checks if the web sources are valid. (Used by Source Dialog)
    Attributes:
        slots: Object of ChessClaimSlots.
        source: The web source to be checked.
    """
    def __init__(self,slots,source):
        super().__init__()
        self.slots = slots
        self.source = source

    def run(self):
        url = self.source.get_value()
        if(self.slots.model.check_download(url)):
            self.source.set_status("ok")
            if url not in self.slots.downloadList:
                self.slots.downloadList.append(url)
                self.slots.validSources.append(self.source)
        else:
            self.source.set_status("error")

class DownloadList(QThread):
    """ Downloads a list of sources from the web. It has 2 modes, either downloading
    continuously or just download once.

    Attributes:
        downloadList: The list of urls to download.
        isLoop(bool): True if downloading continously, else download once.
        statusSignal: Signal to update GUI.
    """
    statusSignal = pyqtSignal(str)

    def __init__(self,downloadList,isLoop):
        super().__init__()
        self.downloadList = downloadList
        self.isLoop = isLoop
        self.isRunning = False

        self.appPath = get_appData_path()
        self.download = DownloadPgn()

    def run(self):
        self.isRunning = True
        if (self.isLoop):
            self.download_loop()
        else:
            self.download_once()

    def download_loop(self):
        while (self.isRunning):
            count = 0
            for entry in self.downloadList:
                data = self.download.download(entry)

                status = self.download.get_status()
                self.statusSignal.emit(status)

                filename = os.path.join(self.appPath,"games"+str(count)+".pgn")
                file = open(filename,"wb")
                try:
                    file.write(data)
                except TypeError:
                    file.close()
                    break
                file.close()
                count = count+1

            time.sleep(4)

    def download_once(self):
        count = 0
        for entry in self.downloadList:
            data = self.download.download(entry)
            filename = os.path.join(self.appPath,"games"+str(count)+".pgn")

            file = open(filename,"wb")
            file.write(data)
            file.close()

            count = count+1

    def stop(self):
        self.isRunning = False

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

    def __init__(self,model,filename,lock,livePgnOption):
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

        time.sleep(1.2) # For synchronization purposes.

        while(self.isRunning):
            try:
                size_of_pgn = os.path.getsize(self.filename)
            except FileNotFoundError:
                size_of_pgn = 0

            if (size_of_pgn != 0 and last_size != size_of_pgn):
                self.statusSignal.emit("active")

                self.checkPgnWorker = CheckPgn(self.model,self.filename,self.lock,self.livePgnOption)
                self.checkPgnWorker.start()

                """ While the pgn is being check here we take the entries and
                append it to the eventTable. This create a real time update
                experience for the user when the pgn has a lot of entries """

                while (self.checkPgnWorker.isAlive() or entries != alreadyEntry):
                    time.sleep(1)
                    entries = self.model.get_entries()

                    if not (self.isRunning): break

                    for entry in entries:
                        if (entry in alreadyEntry): continue
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

    def __init__(self,model,makePgnWorker,scanWorker,downloadWorker=None):
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
        filePathList: A list that contains all the files path(or url) which are valid.
        isLoop: True if making the pgn continously, else makes the pgn once.
        lock: The fileLock for the games.pgn between CheckPgn and MakePgn threads.
    """

    def __init__(self,filePathList,isLoop,lock=None):
        super().__init__()
        self.filePathList = filePathList
        self.isLoop = isLoop
        self.isRunning = False
        self.lock = lock
        self.daemon = True

        appPath = get_appData_path()
        self.filename = os.path.join(appPath,"games.pgn")

    def run(self):
        self.isRunning = True
        if (self.isLoop):
            self.makePgn_loop()
        else:
            self.makePgn_once()

    def makePgn_loop(self):
        while(self.isRunning):
            data = bytes()
            for filepath in self.filePathList:
                try:
                    in_file = open(filepath, "rb")
                    data = data+"\n\n".encode("utf-8")+in_file.read()
                    in_file.close()
                except FileNotFoundError:
                    continue

            self.lock.acquire()
            file = open(self.filename,"wb")
            file.write(data)
            file.close()
            self.lock.release()

            time.sleep(4)

    def makePgn_once(self):
        data = bytes()
        for filepath in self.filePathList:
            in_file = open(filepath, "rb")
            data = data+"\n\n".encode("utf-8")+in_file.read()
            in_file.close()

        file = open(self.filename,"wb")
        file.write(data)
        file.close()

    def stop(self):
        self.isRunning = False

class CheckPgn(Thread):
    """ Checks all the games of the pgn file.
    Attributes:
        filename: The path of the combined pgn file.
        model: An Object of Claims Class.
        lock: The fileLock for the games.pgn between CheckPgn and MakePgn threads.
        livePgnOption: The checkbox object on the menu.
        isRunning(bool): True if the thread is running, false otherwise.
    """
    def __init__(self,model,filename,lock,livePgnOption):
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

            #Loop to go through all of the games of the pgn.
            while (self.isRunning):
                try:
                    game = self.model.read_game(pgn)
                except:
                    continue
                if (game == None): # There aren't any games left in the pgn.
                    break
                if (self.livePgnOption.isChecked() and game.headers["Result"] != "*"):
                    continue
                if(self.model.get_players(game) in self.model.dontCheck): continue
                self.model.check_game(game)

        self.lock.release()

    def stop(self):
        self.isRunning = False
