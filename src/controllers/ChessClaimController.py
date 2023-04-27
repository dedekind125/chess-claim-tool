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

import sys, os.path
from PyQt5.QtWidgets import QApplication
from src.views.ChessClaimView import ChessClaimView
from src.callbacks.ChessClaimCallbacks import ChessClaimCallbacks
from src.Claims import Claims
from src.helpers import get_appdata_path


class ChessClaimController(QApplication):
    """ The Controller of the whole application.

    Attributes:
        model: Object of the Claims Class.
        view: The main views(GUI) of the application.
    """
    __callbacks__ = ["callbacks", "view", "model"]

    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.callbacks = None
        self.view = None
        self.model = Claims()

    def set_view(self, view: ChessClaimView):
        self.view = view

    def do_start(self) -> None:
        """ Perform startup operations and shows the dialog.
        Called once, on application startup. """

        app_path = get_appdata_path()
        if not os.path.exists(app_path):
            os.makedirs(app_path)

        self.callbacks = ChessClaimCallbacks(self.model, self.view)
        self.view.set_callbacks(self.callbacks)

        self.view.set_gui()
        self.view.show()
