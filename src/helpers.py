"""
Chess Claim Tool: helpers

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
import enum
import os.path
import platform
import sys


def resource_path(relative_path: str) -> str:
    """ Get absolute path to a resource, works for running the program from the
    terminal and for PyInstaller.

    Args:
        relative_path(str): The relative path of a resource.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): # Pyinstaller
        base_path = sys._MEIPASS
    else:
        if relative_path.endswith(".css"):
            base_path = os.path.abspath(os.path.join("src", "views"))
        else:
            base_path = os.path.abspath("icons")

    return os.path.join(base_path, relative_path)


def get_appdata_path() -> str:
    """Get the right directories for the different OS in which the app will store data """
    if platform.system() == "Darwin":
        base_path = os.path.join(os.getenv("HOME"), "Library/Application Support")
    elif platform.system() == "Windows":
        base_path = os.getenv('APPDATA')
    return os.path.join(base_path, "Chess Claim Tool")


class Status(enum.Enum):
    OK = 1
    ERROR = 2
    STOP = 3
    ACTIVE = 4
    WAIT = 5