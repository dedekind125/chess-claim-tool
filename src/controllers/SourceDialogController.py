"""
Chess Claim Tool: SourceDialogController

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

import json
import os.path
from typing import List

from src.controllers.SourceDialogSlots import SourceDialogSlots
from src.views.SourceDialogView import SourceHBox
from src.helpers import get_appdata_path


class SourceDialogController:
    """ The Controller of sources Dialog.

    Attributes:
        view: The views(GUI) of the dialog.
    """
    __slots__ = ['dialogSlots', 'view']

    def __init__(self) -> None:
        self.dialogSlots = None
        self.view = None

    def set_view(self, view) -> None:
        self.view = view

    def do_start(self) -> None:
        """ Perform startup operations and shows the dialog.
        Called once, on dialog startup."""

        self.dialogSlots = SourceDialogSlots(self.view)
        self.view.set_slots(self.dialogSlots)

        self.view.set_gui()

        # Load values from JSON
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

        self.view.show()

    def do_resume(self) -> None:
        """ Shows the dialog from the previous state the user left itself.
        That means that do_start has been preceded."""
        self.view.show()

    def get_filepath_list(self) -> List[str]:
        return self.dialogSlots.filepaths

    def get_valid_sources(self) -> List[SourceHBox]:
        return self.view.sources

    def get_download_list(self) -> List[str]:
        return self.dialogSlots.downloads

    def has_valid_sources(self) -> bool:
        return len(self.dialogSlots.filepaths) > 0
