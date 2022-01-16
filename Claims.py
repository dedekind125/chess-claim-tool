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
from enum import Enum
from typing import Any

import chess.pgn
from math import ceil


def is_threefold_repetition(self) -> bool:
    """ Checks if a threefold repetition occurred in the game.
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


def is_fifty_moves(self) -> bool:
    """ Checks if the 50 Move Draw Rule occurred in the game.
    This is an extension method of Class Board class from chess module.
    """
    if self.halfmove_clock >= 100:
        if any(self.generate_legal_moves()):
            return True
    return False


chess.Board.is_threefold_repetition = is_threefold_repetition
chess.Board.is_fifty_moves = is_fifty_moves


def get_move(move_counter: int, san_move: str) -> str:
    """ Returns: The move as it's been displayed in the claimsTable.
    Args:
        move_counter: The number of the moves played in the game.
        san_move: The SAN representation of the move
    """
    move_num = ceil(move_counter / 2)

    if move_counter % 2 == 0:
        move = f"{move_num}...{san_move}"
    else:
        move = f"{move_num}.{san_move}"
    return move


def get_board_number(game: Any) -> str:
    try:
        return str(game.headers["Board"])
    except KeyError:
        return str(game.headers["Round"])


def get_players(game: Any) -> str:
    white = game.headers["White"][:22]
    black = game.headers["Black"][:22]
    return f"{white} - {black}"


class Claims:
    """ Provides the methods to read and scan a game for any type of draw claim.

    Attributes:
        dont_check(list): Is a list of player's names who's their game shall not
        be checked again. This list is used for games that a 5 Fold Repetition
        or 75 Moves Rule occurred.
        entries(list): The list of entries. Each element of entries lists
        is a list ([str,str,str,str]).
    """

    def __init__(self):
        self.dont_check = set()
        self.entries = set()

    def check_game(self, game: Any) -> set:
        """ Checks the game for 3 Fold Repetitions, 5 Fold Repetitions,
        50 Move Draw Rule and for the 75 Move Draw Rule.
        Args:
            game: The game to be checked.
        """
        move_counter = 0
        board = game.board()
        players = get_players(game)
        board_number = get_board_number(game)
        game_entries = set()

        # Loop to go through of all the moves of the game.
        for move in game.mainline_moves():
            san_move = str(board.san(move))
            board.push(move)
            move_counter += 1
            move = get_move(move_counter, san_move)

            if board.is_fivefold_repetition():
                game_entries.add((ClaimType.FIVEFOLD, board_number, players, move))
                self.dont_check.add(players)
                break
            if board.is_seventyfive_moves():
                game_entries.add((ClaimType.SEVENTYFIVE_MOVES, board_number, players, move))
                self.dont_check.add(players)
                break
            if board.is_fifty_moves():
                game_entries.add((ClaimType.FIFTY_MOVES, board_number, players, move))
            if board.is_threefold_repetition():
                game_entries.add((ClaimType.THREEFOLD, board_number, players, move))

        game_entries = game_entries - self.entries
        self.entries.update(game_entries)
        return game_entries

    def empty_dont_check(self) -> None:
        self.dont_check.clear()

    def empty_entries(self) -> None:
        self.entries.clear()


class ClaimType(Enum):
    THREEFOLD = "3 Fold Repetition"
    FIVEFOLD = "5 Fold Repetition"
    FIFTY_MOVES = "50 Moves Rule"
    SEVENTYFIVE_MOVES = "75 Moves Rule"
