import itertools
import json
import random
from typing import List, Optional, Set, Tuple

from ..data.models import GameDatabase
from .model import Cell, CellInfo, CellState, GameState, GameStats


class MinesweeperGame:
    def __init__(
        self,
        size: int,
        difficulty: float = 0.15,
        username: str = "anonymous",
        db: GameDatabase | None = None,
    ):
        if size < 3:
            raise ValueError("Board size must be at least 3")
        if not 0 < difficulty < 1:
            raise ValueError("Difficulty must be between 0 and 1")

        self.size = size
        self.difficulty = difficulty
        self.mine_count = max(1, int(size * size * difficulty))
        self.board: List[List[Cell]] = []
        self.game_state = GameState.PLAYING
        self.first_click = True
        self.revealed_count = 0
        self.flag_count = 0

        # Database integration
        self.db = db or GameDatabase()
        self.user = None
        self.session_id = None

        if username:
            self.user = self.db.get_or_create_user(username)
            self.session_id = self._create_game_session()

        self._initialize_board()

    def _initialize_board(self):
        self.board = [[Cell() for _ in range(self.size)] for _ in range(self.size)]

    def _place_mines(self, exclude_row: int, exclude_col: int):
        available_positions = [
            (row, col)
            for row, col in itertools.product(range(self.size), repeat=2)
            if row != exclude_row or col != exclude_col
        ]

        mine_positions = random.sample(
            available_positions, min(self.mine_count, len(available_positions))
        )

        for row, col in mine_positions:
            self.board[row][col].is_mine = True

        self._calculate_adjacent_mines()

    def _calculate_adjacent_mines(self):
        for row, col in itertools.product(range(self.size), repeat=2):
            if not self.board[row][col].is_mine:
                count = sum(
                    1
                    for dr, dc in itertools.product([-1, 0, 1], repeat=2)
                    if not (dr == 0 and dc == 0)
                    and 0 <= row + dr < self.size
                    and 0 <= col + dc < self.size
                    and self.board[row + dr][col + dc].is_mine
                )
                self.board[row][col].adjacent_mines = count

    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        return [
            (row + dr, col + dc)
            for dr, dc in itertools.product([-1, 0, 1], repeat=2)
            if not (dr == 0 and dc == 0)
            and 0 <= row + dr < self.size
            and 0 <= col + dc < self.size
        ]

    def reveal_cell(self, row: int, col: int) -> bool:
        if not self._is_valid_position(row, col):
            return False

        cell = self.board[row][col]

        if cell.state != CellState.HIDDEN:
            return False

        if self.first_click:
            self._place_mines(row, col)
            self.first_click = False

        if cell.is_mine:
            cell.state = CellState.REVEALED
            self.game_state = GameState.LOST
            self._finish_game_session()
            return True

        self._reveal_cells_flood_fill(row, col)
        self._check_win_condition()
        self._update_session_stats()

        if self.game_state == GameState.WON:
            self._finish_game_session()

        return True

    def _reveal_cells_flood_fill(self, row: int, col: int):
        if not self._is_valid_position(row, col):
            return

        cell = self.board[row][col]
        if cell.state != CellState.HIDDEN or cell.is_mine:
            return

        cell.state = CellState.REVEALED
        self.revealed_count += 1

        if cell.adjacent_mines == 0:
            for nr, nc in self._get_neighbors(row, col):
                self._reveal_cells_flood_fill(nr, nc)

    def toggle_flag(self, row: int, col: int) -> bool:
        if not self._is_valid_position(row, col):
            return False

        cell = self.board[row][col]

        if cell.state == CellState.REVEALED:
            return False

        if cell.state == CellState.HIDDEN:
            cell.state = CellState.FLAGGED
            self.flag_count += 1
        elif cell.state == CellState.FLAGGED:
            cell.state = CellState.HIDDEN
            self.flag_count -= 1

        self._update_session_stats()
        return True

    def _is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def _check_win_condition(self):
        total_cells = self.size * self.size
        if self.revealed_count == total_cells - self.mine_count:
            self.game_state = GameState.WON

    def get_cell_info(self, row: int, col: int) -> CellInfo | None:
        if not self._is_valid_position(row, col):
            return None

        cell = self.board[row][col]
        return CellInfo(
            state=cell.state,
            is_mine=cell.is_mine,
            adjacent_mines=cell.adjacent_mines,
            row=row,
            col=col,
        )

    def get_game_stats(self) -> GameStats:
        return GameStats(
            size=self.size,
            mine_count=self.mine_count,
            flag_count=self.flag_count,
            revealed_count=self.revealed_count,
            game_state=self.game_state,
            remaining_mines=self.mine_count - self.flag_count,
        )

    def reset(self):
        if self.session_id and self.game_state != GameState.PLAYING:
            # Finish the current session before resetting
            result = "won" if self.game_state == GameState.WON else "lost"
            self.db.finish_game_session(
                self.session_id, result, self.revealed_count, self.flag_count
            )

        self.board = []
        self.game_state = GameState.PLAYING
        self.first_click = True
        self.revealed_count = 0
        self.flag_count = 0

        # Create new session if user is logged in
        if self.user:
            self.session_id = self._create_game_session()

        self._initialize_board()

    def _create_game_session(self):
        if self.user:
            difficulty_name = self._get_difficulty_name()
            session = self.db.create_game_session(
                user_id=self.user.id,
                board_size=self.size,
                mine_count=self.mine_count,
                difficulty=difficulty_name,
            )
            return session.id
        return None

    def _get_difficulty_name(self) -> str:
        if self.size == 9 and self.mine_count == 10:
            return "beginner"
        elif self.size == 16 and self.mine_count == 40:
            return "intermediate"
        elif self.size == 22 and self.mine_count == 99:
            return "expert"
        else:
            return "custom"

    def _update_session_stats(self):
        if self.session_id:
            self.db.update_game_session(
                self.session_id,
                cells_revealed=self.revealed_count,
                flags_used=self.flag_count,
            )

    def _finish_game_session(self):
        if self.session_id and self.game_state != GameState.PLAYING:
            result = "won" if self.game_state == GameState.WON else "lost"
            self.db.finish_game_session(
                self.session_id, result, self.revealed_count, self.flag_count
            )

    def save_game(self, game_name: str) -> bool:
        if not self.user:
            return False

        # Serialize board state
        board_data = {
            "board": [
                [
                    {
                        "is_mine": cell.is_mine,
                        "state": cell.state.value,
                        "adjacent_mines": cell.adjacent_mines,
                    }
                    for cell in row
                ]
                for row in self.board
            ]
        }

        self.db.save_game(
            user_id=self.user.id,
            game_name=game_name,
            board_size=self.size,
            mine_count=self.mine_count,
            difficulty=self._get_difficulty_name(),
            game_state=self.game_state.value,
            board_data=board_data,
            revealed_count=self.revealed_count,
            flag_count=self.flag_count,
            first_click=self.first_click,
        )
        return True

    def load_game(self, game_name: str) -> bool:
        if not self.user:
            return False

        saved_game = self.db.load_game(self.user.id, game_name)
        if not saved_game:
            return False

        # Load game state
        self.size = saved_game.board_size
        self.mine_count = saved_game.mine_count
        self.difficulty = self.mine_count / (self.size * self.size)
        self.game_state = GameState(saved_game.game_state)
        self.revealed_count = saved_game.revealed_count
        self.flag_count = saved_game.flag_count
        self.first_click = saved_game.first_click

        # Deserialize board state
        board_data = json.loads(saved_game.board_data)
        self.board = []
        for row_data in board_data["board"]:
            row = []
            for cell_data in row_data:
                cell = Cell(
                    is_mine=cell_data["is_mine"],
                    state=CellState(cell_data["state"]),
                    adjacent_mines=cell_data["adjacent_mines"],
                )
                row.append(cell)
            self.board.append(row)

        # Create new session for loaded game
        if self.game_state == GameState.PLAYING:
            self.session_id = self._create_game_session()

        return True

    def get_saved_games(self) -> List[str]:
        if not self.user:
            return []

        saved_games = self.db.get_user_saved_games(self.user.id)
        return [game.game_name for game in saved_games]

    def delete_saved_game(self, game_name: str) -> bool:
        if not self.user:
            return False

        return self.db.delete_saved_game(self.user.id, game_name)

    def get_user_stats(self):
        if not self.user:
            return None

        return self.db.get_user_stats(self.user.id)

    def cheat(self) -> Tuple[int, int] | None:
        """Reveal a safe cell (guaranteed not to be a mine).
        
        Returns:
            Tuple of (row, col) of the revealed cell, or None if no safe cells available
        """
        if self.game_state != GameState.PLAYING:
            return None

        # Find all hidden cells that are not mines
        safe_hidden_cells = []
        for row in range(self.size):
            for col in range(self.size):
                cell = self.board[row][col]
                if cell.state == CellState.HIDDEN and not cell.is_mine:
                    safe_hidden_cells.append((row, col))

        if not safe_hidden_cells:
            return None

        # If this is the first click, place mines first
        if self.first_click:
            # Choose a random safe cell and place mines excluding that cell
            row, col = random.choice(safe_hidden_cells)
            self._place_mines(row, col)
            self.first_click = False
            
            # Update safe_hidden_cells after placing mines
            safe_hidden_cells = []
            for r in range(self.size):
                for c in range(self.size):
                    cell = self.board[r][c]
                    if cell.state == CellState.HIDDEN and not cell.is_mine:
                        safe_hidden_cells.append((r, c))

        if not safe_hidden_cells:
            return None

        # Choose a random safe cell to reveal
        row, col = random.choice(safe_hidden_cells)
        
        # Reveal the cell using flood fill
        self._reveal_cells_flood_fill(row, col)
        self._check_win_condition()
        self._update_session_stats()

        if self.game_state == GameState.WON:
            self._finish_game_session()

        return (row, col)
