"""
Chess Claim Tool: SourceDialogController

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

import os.path, json
from PyQt5.QtWidgets import QApplication
from SourceDialogSlots import SourceDialogSlots
from download import DownloadPgn
from helpers import get_appData_path

class SourceDialogController():
    """ The Controller of sources Dialog.

    Attributes:
        downloadModel: Object of the Download Class.
        view: The view(GUI) of the dialog.
    """
    def __init__(self):
        self.downloadModel = DownloadPgn()

    def set_view(self,view):
        self.view = view

    def do_start(self):
        """ Perform startup operations and shows the dialog.
        Called once, on dialog startup."""

        #Connect the signals from the View to the Slots
        self.dialogSlots = SourceDialogSlots(self.downloadModel,self.view)
        self.view.set_slots(self.dialogSlots)

        # Initialize the GUI
        self.view.set_GUI()

        # Load values from JSON if the user choosed the Remember Sources Option last time
        appPath = get_appData_path()
        try:
            file = open(os.path.join(appPath,"sources.json"),"r")
            data = json.load(file)
            file.close()
            for entry in data:
                self.view.add_source(entry["option"],entry["value"])

        except FileNotFoundError:
            pass

        except json.decoder.JSONDecodeError:
            file.close()

        # Show the GUI
        self.view.show()

    def do_resume(self):
        """ Shows the dialog from the previous state the user left itself.
        That means that do_start has been preceded."""
        self.view.show()

    def get_filepathList(self):
        return self.dialogSlots.filepathList

    def get_validSources(self):
        return self.dialogSlots.validSources

    def get_downloadList(self):
        return self.dialogSlots.downloadList
