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

import os.path, json, time
from threading import Thread
from PyQt5.QtCore import QThreadPool
from workers import CheckDownload, DownloadList, MakePgn
from helpers import get_appData_path

class SourceDialogSlots():
    """ Handles user interaction with the GUI of the dialog. Each function
    is called when a specific action is performed by the user, to fulfill
    the request that corresponds to that action.

    Attributes:
        model: Object of the Download Class.
        view:  The view of the Source Dialog.
        appPath(str): The path where the application will store & fetch data.
        filepathList(list of str): A list that contains all the files path(or url) which are valid.
        downloadList(list of str): A list that contains all the urls which are valid.
        validSources(list of SourceHBox): A list that contains all the sources which are valid.
    """
    def __init__(self,model,view):
        super().__init__()
        self.model = model
        self.view = view
        self.appPath = get_appData_path()

        self.threadPool = QThreadPool()
        self.filepathList = []
        self.downloadList = []
        self.validSources = []

    def on_deleteButton_clicked(self,sourceHBox):
        """ Removes a source.
        Args:
            sourceHBox: The source to be deleted.

        Trigger: User clicks the "Delete" Button(Trash Icon) on the Source Dialog.
        """

        # Remove sourceHBox from the sourcesList
        self.view.sources.remove(sourceHBox)
        self.view.sourcesCounter = self.view.sourcesCounter-1

        # Remove Source Horizontal Box from View
        self.view.layout.removeWidget(sourceHBox)
        sourceHBox.deleteLater()
        sourceHBox = None

        # Fix GUI after the removal of the sourceHBox
        self.view.adjustSize()

    def on_applyButton_clicked(self):
        """ Checks validity of all of the sources. Creates all the
        list(filepathList,downloadList,validSources) and sets the status of each source.

        Trigger: User clicks the "Apply" Button on the Source Dialog.
        """

        #Empty Lists
        self.filepathList = []
        self.downloadList = []
        self.validSources = []

        # Create a Thread to complete the operations.
        applyThread = Thread(target=self.apply_thread)
        applyThread.daemon = True
        applyThread.start()

    def on_okButton_clicked(self):
        """ Closes the Source Dialog and performs all the necessary operations depending
        the user input. These operations are:
            1) Download the pgn files, if any
            2) Make the games.pgn from all the sources, if there are valid sources.
            3) If the rememberOption is checked save the valid sources to the JSON file.

        Trigger: User clicks the "OK" Button of the Source Dialog.
        """

        # Create a Thread to complete the operations.
        exitThread = Thread(target=self.on_exit_thread)
        exitThread.daemon = True
        exitThread.start()

        # Close the Dialog
        self.view.accept()
        self.view.close()

    def apply_thread(self):
        """ Function called by Thread to perform the operations of the on_applyButton_clicked."""

        # Loop to check the validity of all the sources.
        for source in self.view.sources:
            if (source.get_source_index() == 0): # Web Download Option
                checkDownloadWorker = CheckDownload(self,source)
                self.threadPool.start(checkDownloadWorker)
            else: # Local File Option
                filepath = source.get_value()
                if os.path.exists(filepath):
                    source.set_status("ok")
                    if filepath not in self.filepathList:
                        self.filepathList.append(filepath)
                        self.validSources.append(source)
                else:
                    source.set_status("error")

        # Wait until all the sources are checked.
        self.threadPool.waitForDone()

        # Add the valid urls to the filepathList
        for index in range(0,len(self.downloadList)):
            filepath = os.path.join(self.appPath,"games"+str(index)+".pgn")
            if filepath not in self.filepathList:
                self.filepathList.append(filepath)

        self.view.enable_okButton()

    def on_exit_thread(self):
        """ Function called by Thread to perform the operations of the on_okButton_clicked."""

        # Download the pgn files
        downloadListWorker = DownloadList(self.downloadList,False)
        downloadListWorker.start()
        downloadListWorker.wait()

        #  Make the games.pgn
        makePgnWorker = MakePgn(self.filepathList,False)
        makePgnWorker.start()

        # If the rememberOption is checked save the valid sources to the JSON file.
        rememberOption = self.view.get_remember_option()
        if (rememberOption.isChecked()):
            self.save_sources()
        else:
            os.remove(os.path.join(self.appPath,'sources.json'))

    def save_sources(self):
        """ Saves the valid sources to the JSON file """
        data = []
        for source in self.validSources:
            data.append({"option":source.get_source_index(),"value":source.get_value()})

        file = open(os.path.join(self.appPath,'sources.json'), 'w')
        json.dump(data,file,indent=4)
        file.close()
