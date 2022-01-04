"""
Chess Claim Tool

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
import sys
from ChessClaimController import ChessClaimController
from ChessClaimView import ChessClaimView
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from helpers import resource_path

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    app = ChessClaimController()
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(resource_path("logo.png")))

    css = "main.css"
    with open(resource_path(css), 'r') as css_file:
        css = css_file.read().replace('\n', '')
    app.setStyleSheet(css)

    view = ChessClaimView()
    app.set_view(view)

    app.do_start()
    sys.exit(app.exec_())
