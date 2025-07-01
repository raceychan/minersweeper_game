from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static, DataTable
from textual.reactive import reactive
from textual import on
from textual.coordinate import Coordinate

from ..minesweeper import MinesweeperGame, GameState, CellState


class MineCell(Button):
    """A single cell in the minesweeper grid."""
    
    def __init__(self, row: int, col: int, **kwargs):
        super().__init__("", **kwargs)
        self.row = row
        self.col = col
        self.is_revealed = False
        self.is_flagged = False
        self.is_mine = False
        self.adjacent_mines = 0
        self.mine_hit = False
        
    def update_display(self, cell_state: CellState, is_mine: bool, adjacent_mines: int, mine_hit: bool = False):
        """Update the cell display based on game state."""
        self.is_mine = is_mine
        self.adjacent_mines = adjacent_mines
        self.mine_hit = mine_hit
        
        if cell_state == CellState.FLAGGED:
            self.label = "🚩"
            self.is_flagged = True
            self.is_revealed = False
            self.add_class("flagged")
            self.remove_class("revealed", "mine", "mine-hit")
        elif cell_state == CellState.REVEALED:
            self.is_revealed = True
            self.is_flagged = False
            self.remove_class("flagged")
            self.add_class("revealed")
            
            if is_mine:
                if mine_hit:
                    self.label = "💥"
                    self.add_class("mine-hit")
                else:
                    self.label = "💣"
                    self.add_class("mine")
            else:
                self.label = str(adjacent_mines) if adjacent_mines > 0 else " "
                if adjacent_mines > 0:
                    self.add_class(f"number-{adjacent_mines}")
        else:  # HIDDEN
            self.label = " "
            self.is_revealed = False
            self.is_flagged = False
            self.remove_class("flagged", "revealed", "mine", "mine-hit")
            for i in range(1, 9):
                self.remove_class(f"number-{i}")


class GameBoard(Container):
    """The minesweeper game board."""
    
    def __init__(self, size: int = 9):
        super().__init__()
        self.board_size = size
        self.cells = []
        
    def compose(self) -> ComposeResult:
        """Compose the game board with cells."""
        with Vertical():
            for row in range(self.board_size):
                cell_row = []
                with Horizontal():
                    for col in range(self.board_size):
                        cell = MineCell(row, col, id=f"cell-{row}-{col}")
                        cell_row.append(cell)
                        yield cell
                self.cells.append(cell_row)
    
    def update_board(self, game: MinesweeperGame, hit_row: int = None, hit_col: int = None):
        """Update all cells based on the current game state."""
        for row in range(self.board_size):
            for col in range(self.board_size):
                cell = self.cells[row][col]
                game_cell = game.board[row][col]
                
                # Determine if this cell should show as a mine
                show_mine = game_cell.is_mine and (
                    game_cell.state == CellState.REVEALED or 
                    game.game_state == GameState.LOST
                )
                
                # Check if this is the mine that was hit
                mine_hit = (hit_row is not None and hit_col is not None and 
                           row == hit_row and col == hit_col and game_cell.is_mine)
                
                cell.update_display(
                    game_cell.state, 
                    show_mine, 
                    game_cell.adjacent_mines,
                    mine_hit
                )


class GameStats(Static):
    """Display game statistics."""
    
    def __init__(self):
        super().__init__()
        self.mines_remaining = 0
        self.flags_placed = 0
        
    def update_stats(self, game: MinesweeperGame):
        """Update the statistics display."""
        stats = game.get_game_stats()
        self.mines_remaining = stats.remaining_mines
        self.flags_placed = stats.flag_count
        
        status_text = "🎮 Playing"
        if game.game_state == GameState.WON:
            status_text = "🏆 You Won!"
        elif game.game_state == GameState.LOST:
            status_text = "💥 Game Over"
            
        self.update(f"Status: {status_text} | Mines: {self.mines_remaining} | Flags: {self.flags_placed}")


class MinesweeperApp(App):
    """A Textual app for Minesweeper."""
    
    CSS = """
    Screen {
        background: $background;
    }
    
    GameBoard {
        align: center middle;
        width: auto;
        height: auto;
        margin: 1;
    }
    
    MineCell {
        width: 3;
        height: 1;
        margin: 0;
        padding: 0;
        min-width: 3;
        min-height: 1;
    }
    
    .flagged {
        background: $warning;
        color: $text;
    }
    
    .revealed {
        background: $surface;
        color: $text;
    }
    
    .mine {
        background: $error;
        color: $text;
    }
    
    .mine-hit {
        background: $error;
        color: $warning;
    }
    
    .number-1 { color: blue; }
    .number-2 { color: green; }
    .number-3 { color: red; }
    .number-4 { color: purple; }
    .number-5 { color: maroon; }
    .number-6 { color: turquoise; }
    .number-7 { color: black; }
    .number-8 { color: gray; }
    
    GameStats {
        dock: top;
        height: 1;
        text-align: center;
        background: $boost;
    }
    
    .controls {
        dock: bottom;
        height: 3;
        text-align: center;
    }
    
    .difficulty-buttons {
        align: center middle;
        height: 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.game = None
        self.board = None
        self.stats = None
        self.board_size = 9
        self.difficulty = 0.1  # 10% mines
        
    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        self.stats = GameStats()
        yield self.stats
        
        self.board = GameBoard(self.board_size)
        yield self.board
        
        with Container(classes="controls"):
            with Horizontal(classes="difficulty-buttons"):
                yield Button("Beginner (9x9)", id="beginner")
                yield Button("Intermediate (16x16)", id="intermediate") 
                yield Button("Expert (22x22)", id="expert")
            yield Button("New Game", id="new-game", variant="primary")
        
        yield Footer()
    
    def on_mount(self):
        """Initialize game after mounting."""
        self.start_new_game()
    
    def start_new_game(self):
        """Start a new game with current settings."""
        self.game = MinesweeperGame(self.board_size, self.difficulty)
        if self.board:
            self.board.update_board(self.game)
        if self.stats:
            self.stats.update_stats(self.game)
    
    @on(Button.Pressed, "#new-game")
    def new_game_pressed(self):
        """Handle new game button press."""
        self.start_new_game()
    
    @on(Button.Pressed, "#beginner")
    def beginner_pressed(self):
        """Set beginner difficulty."""
        self.board_size = 9
        self.difficulty = 10 / (9 * 9)  # 10 mines
        self.restart_with_new_size()
    
    @on(Button.Pressed, "#intermediate") 
    def intermediate_pressed(self):
        """Set intermediate difficulty."""
        self.board_size = 16
        self.difficulty = 40 / (16 * 16)  # 40 mines
        self.restart_with_new_size()
    
    @on(Button.Pressed, "#expert")
    def expert_pressed(self):
        """Set expert difficulty."""
        self.board_size = 22
        self.difficulty = 99 / (22 * 22)  # 99 mines
        self.restart_with_new_size()
    
    def restart_with_new_size(self):
        """Restart the app with a new board size."""
        # Remove current board
        if self.board:
            self.board.remove()
        
        # Create new board with new size
        self.board = GameBoard(self.board_size)
        self.mount(self.board, after=self.stats)
        
        # Start new game
        self.start_new_game()
    
    @on(Button.Pressed, "MineCell")
    def cell_pressed(self, event: Button.Pressed):
        """Handle cell button press."""
        if not self.game or self.game.game_state != GameState.PLAYING:
            return
            
        cell = event.button
        if hasattr(cell, 'row') and hasattr(cell, 'col'):
            success = self.game.reveal_cell(cell.row, cell.col)
            if success:
                hit_row = cell.row if self.game.board[cell.row][cell.col].is_mine else None
                hit_col = cell.col if self.game.board[cell.row][cell.col].is_mine else None
                self.board.update_board(self.game, hit_row, hit_col)
                self.stats.update_stats(self.game)
    
    def on_key(self, event):
        """Handle key press events."""
        if event.key == "f" and self.focused and isinstance(self.focused, MineCell):
            # Flag/unflag the focused cell
            cell = self.focused
            if hasattr(cell, 'row') and hasattr(cell, 'col'):
                if self.game and self.game.game_state == GameState.PLAYING:
                    success = self.game.toggle_flag(cell.row, cell.col)
                    if success:
                        self.board.update_board(self.game)
                        self.stats.update_stats(self.game)


def run_tui():
    """Run the TUI version of Minesweeper."""
    app = MinesweeperApp()
    app.run()


if __name__ == "__main__":
    run_tui()