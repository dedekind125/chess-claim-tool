"""
Chess Claim Tool: SourceDialogSlots

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

import os.path
from threading import Lock
from PyQt5.QtCore import QThreadPool
from SourceDialogController import SourceDialogController
from SourceDialogView import AddSourceDialog
from workers import DownloadGames, MakePgn, Scan, Stop
from helpers import get_appdata_path

class ChessClaimSlots:
    def __init__(self,model,view):
        """ Handles user interaction with the GUI of the Main Window. Each function
        is called when a specific action is performed by the user, to fulfill
        the request that corresponds to that action model and view wise.

        Attributes:
            model: Object of the Claims class.
            view:  The view of the Main Window.
            dialogFirstTime(bool): True if the user haven't cliced the "Add Source" Button,
            False otherwise.
            self.hasDownloadWorker(bool): True if there is a downloadWorker
            (at least one source from the web), False otherwise.
        """
        self.model = model
        self.view = view

        self.dialogFirstTime = True
        self.hasDownloadWorker = False

    def on_sourcesButton_clicked(self):
        """ Initialize the Source Dialog MVC model and opens the Source Dialog.
        Attributes:
            dialog: The Controller of the Source Dialog

        trigger: User clicks the "Add Sources" Button on the Main Window.
        """
        if (self.dialogFirstTime) :
            self.dialog = SourceDialogController()
            dialog_view = AddSourceDialog()

            """ When the view of the dialog is closed(with the accepted Signal)
            update the statusBar accordingly."""
            dialog_view.accepted.connect(self.update_statusBar_sources)

            self.dialog.set_view(dialog_view)
            self.dialog.do_start()

            self.dialogFirstTime = False

        else:
            self.on_stopButton_clicked()
            self.dialog.do_resume()

    def on_scanButton_clicked(self):
        """ Creates the necessary thread(workers) in order to scan the pgn(s)
        for the draw claims.

        trigger: User clicks the "Start Scan" Button on the Main Window.
        """

        """ If the scan thread is alive it means the scan button is already
        clicked before. So if the user click it again nothing should happen."""

        try:
            if (self.scanWorker.is_running): return
        except:
            pass

        """ Check if there any valid sources before the start of the scan.
        If there aren't any valid sources raire the warning dialog and return."""

        if (self.dialogFirstTime):
            self.view.load_warning()
            return
        filepathList = self.dialog.get_filepath_list()
        if not filepathList:
            self.view.load_warning()
            return

        self.view.clear_table() # Clear the table of the output in the case of a previous scan.
        self.view.change_scanButton_text("active")

        """ If at least one of the sources is from the web we create a download
        therad(downloadWorker) to continuously download the web source(s). """

        self.hasDownloadWorker = False
        downloadList = self.dialog.get_download_list()
        if downloadList:
            self.downloadWorker = DownloadGames(downloadList, True)
            self.downloadWorker.status_signal.connect(self.update_statusBar_download)
            self.hasDownloadWorker = True
            self.downloadWorker.start()

        """ We create a thread(makePgnWorker) to continuously making the
        combined pgn from all the pgn's that were set as sources
        Also, a pyqt Signals is connected to this thread in order to update
        the downloadLabel in the statusBar.

        fileLock: Is a Lock Object. Both makePgnWorker thread and scanWorker
        thread (see below) access the combined games.pgn for writing and reading.
        Thus to avoid any conflict, with the use of fileLock, we make sure that
        only one thread per time uses the game.pgn. """

        fileLock = Lock()
        self.makePgnWorker = MakePgn(filepathList,True,fileLock)
        self.makePgnWorker.start()

        appPath = get_appdata_path()
        filename = os.path.join(appPath,"games.pgn")

        """ Create a thread(scanWorker) to scan the combined pgn using the Model.
        Also, two pyqt Signals are connected to this thread in order to update
        the claimsTable and the statusBar in the GUI. """

        livePgnOption = self.view.livePgnOption
        self.scanWorker = Scan(self.model,filename,fileLock,livePgnOption)
        self.scanWorker.addEntrySignal.connect(self.update_claimsTable)
        self.scanWorker.statusSignal.connect(self.update_statusBar_scan)
        self.scanWorker.start()

    def on_stopButton_clicked(self):
        """ Creates a thread in order to stop all the other running Threads(
        downloadWorker, makePgnWorker,scanWorker)

        trigger: User clicks the "Stop" Button on the Main Window.
        """

        # If the scan thread isn't active there is nothing to stop.
        try:
            if not(self.scanWorker.isRunning):
                return
        except:
            return

        """ We create a thead(stopWorker) in order to stop all the other running threads.
        Also two pyqt Signals are connected to this thread in order to update the GUI
        during the stop process."""

        if(self.hasDownloadWorker):
            self.stopWorker = Stop(self.model,self.makePgnWorker,self.scanWorker,self.downloadWorker)
        else:
            self.stopWorker = Stop(self.model,self.makePgnWorker,self.scanWorker)

        self.stopWorker.enableSignal.connect(self.on_stop_enable_status)
        self.stopWorker.disableSignal.connect(self.on_stop_disable_status)
        self.stopWorker.start()

    def on_about_clicked(self):
        """ Calls the view in order to display the About Dialog.
        trigger: User clicked the About section in the menu.
        """
        self.view.load_about_dialog()

    def on_stop_disable_status(self):
        """ Disables the "Scan" & "Stop" Buttons and the statusBar.
        Also changes the status of the scanButton.

        trigger: By the disableSignal(pyqtSignal)
        """
        self.view.change_scanButton_text("wait")
        self.view.disable_buttons()
        self.view.disable_statusBar()

    def on_stop_enable_status(self):
        """ Enables the "Scan" & "Stop" Buttons and the statusBar.
        Also changes the status of the scanButton, download and scan info at the
        statusBar.

        trigger: By the enableSignal(pyqtSignal)
        """
        self.view.change_scanButton_text("stop")
        self.update_statusBar_download("stop")
        self.update_statusBar_scan("stop")
        
        self.view.enable_buttons()
        self.view.enable_statusBar()

    def update_statusBar_sources(self):
        validSources = self.dialog.get_valid_sources()
        if (len(validSources) == 0):
            self.view.set_sources_status("error")
        else:
            self.view.set_sources_status("ok",validSources)

    """ Functions to update the GUI. Triggered by pyqt Signals."""

    def update_claimsTable(self,entry):
        self.view.add_to_table(entry)

    def update_statusBar_download(self,status):
        self.view.set_download_status(status)

    def update_statusBar_scan(self,status):
        self.view.set_scan_status(status)
