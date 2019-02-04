"""
Chess Claim Tool: download

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

import urllib.request

class DownloadPgn():
    """ Provide the methods to check and download a pgn file from the web
    Attributes:
        status(str): The status of the download.
                     "ok": The file downloaded successfully.
                     "error": The download failed.
    """
    def check_download(self,url):
        """ Checks if the url points to an existing pgn file.
        Args:
            url(str): The location of the file to check.
        Returns:
            bool: True if successful, False otherwise.
        """
        if not(url.endswith(".pgn")):
            return False
        try:
            urllib.request.urlopen(url,timeout=4)
            return True
        except:
            return False

    def download(self,url):
        """ Downloads the pgn and sets the status accordingly.
        Args:
            url(str): The location of the pgn file.
        Returns:
            pgn(str): On success, the contents of the pgn file.
        """
        try:
            response = urllib.request.urlopen(url,timeout=10)
            pgn = response.read()
            self.set_status("ok")
            return pgn
        except:
            self.set_status("error")

    def set_status(self,status):
        self.status = status

    def get_status(self):
        return self.status
