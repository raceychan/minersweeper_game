from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Set


class CellState(Enum):
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"


class GameState(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass
class Cell:
    is_mine: bool = False
    state: CellState = CellState.HIDDEN
    adjacent_mines: int = 0


@dataclass
class CellInfo:
    state: CellState
    is_mine: bool
    adjacent_mines: int
    row: int
    col: int


@dataclass
class GameStats:
    size: int
    mine_count: int
    flag_count: int
    revealed_count: int
    game_state: GameState
    remaining_mines: int


@dataclass
class User:
    username: str
    id: int = None