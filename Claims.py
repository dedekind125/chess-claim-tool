"""
Chess Claim Tool: Claims

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

import chess.pgn
from math import ceil

def is_threefold_repetition(self):
    """ Checks if a threefold repetition occured in the game.
    This is an extension method of Class Board class from chess module.
    """
    transposition_key = self._transposition_key()
    repetitions = 1
    switchyard = []

    while self.move_stack and repetitions < 3:
        move = self.pop()
        switchyard.append(move)

        if self.is_irreversible(move):
            break

        if self._transposition_key() == transposition_key:
            repetitions += 1

    while switchyard:
        self.push(switchyard.pop())

    return repetitions >= 3

def is_fifty_moves(self):
    """ Checks if the 50 Move Draw Rule occured in the game.
    This is an extension method of Class Board class from chess module.
    """
    if self.halfmove_clock >= 100:
        if any(self.generate_legal_moves()):
            return True
    return False

chess.Board.is_threefold_repetition = is_threefold_repetition
chess.Board.is_fifty_moves = is_fifty_moves

class Claims:
    """ Provides the methods to read and scan a game for any type of draw claim.

    Attributes:
        dontCheck(list): Is a list of player's names who's their game shall not
        be checked again. This list is used for games that a 5 Fold Repetition
        or 75 Moves Rule occured.
        entries(list): The list of entries. Each element of entries list
        is a list ([str,str,str,str]).
    """
    def __init__(self):
        self.dontCheck = []
        self.entries = []

    def read_game(self,pgn):
        """ Returns: The parsed game or None if the end of file is reached.
        Args:
            pgn: The pgn file from which we parse the game.
        """
        return chess.pgn.read_game(pgn)

    def check_game(self,game):
        """ Checks the game for 3 Fold Repetitions, 5 Fold Repetitions,
        50 Move Draw Rule and for the 75 Move Draw Rule.
        Args:
            game: The game to be checked.
        """
        move_counter = 0
        board = game.board()
        players = self.get_players(game)
        bo_number = self.get_boNumber(game)

        # Loop to go through of all the moves of the game.
        for move in game.mainline_moves():

            sanMove = str(board.san(move))
            board.push(move)
            move_counter = move_counter+1
            move = self.get_move(move_counter,sanMove)

            # Check for 5 Fold Repetition
            if(board.is_fivefold_repetition()):
                self.entries.append(["5 Fold Repetition",bo_number,players,move])
                self.dontCheck.append(players)
                break
            # Check for 75 Moves Rule
            if(board.is_seventyfive_moves()):
                self.entries.append(["75 Moves Rule",bo_number,players,move])
                self.dontCheck.append(players)
                break
            # Check for 50 Moves Rule
            if(board.is_fifty_moves()):
                if ["50 Moves Rule",bo_number,players,move] not in self.entries:
                    self.entries.append(["50 Moves Rule",bo_number,players,move])
            # Check for 3 Fold Repetition
            if (board.is_threefold_repetition()):
                if ["3 Fold Repetition",bo_number,players,move] not in self.entries:
                    self.entries.append(["3 Fold Repetition",bo_number,players,move])

    def get_move(self,move_counter,sanMove):
        """ Returns: The move as its been displayed in the claimsTable.
        Args:
            move_counter: The number of the moves played in the game.
            sanMove: The SAN representation of the move
        """
        move_num = ceil(move_counter/2)

        if (move_counter%2==0):
            move = str(move_num)+"..."+sanMove
        else:
            move = str(move_num)+"."+sanMove

        return move

    def get_entries(self):
        return self.entries

    def get_boNumber(self,game):
        try:
            return str(game.headers["Board"])
        except:
            return str(game.headers["Round"])

    def get_players(self,game):
        white = game.headers["White"][:22]
        black = game.headers["Black"][:22]
        return (white+" - "+black)

    def empty_dontCheck(self):
        self.dontCheck = []

    def empty_entries(self):
        self.entries = []
