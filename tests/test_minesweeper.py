import pytest
from src.domain.minesweeper import MinesweeperGame
from src.domain.model import GameState, CellState


def test_game_initialization():
    game = MinesweeperGame(5, 0.2)
    assert game.size == 5
    assert game.mine_count == 5  # 5*5*0.2 = 5
    assert game.game_state == GameState.PLAYING
    assert game.first_click == True
    assert game.revealed_count == 0
    assert game.flag_count == 0


def test_invalid_board_size():
    with pytest.raises(ValueError):
        MinesweeperGame(2, 0.2)


def test_invalid_difficulty():
    with pytest.raises(ValueError):
        MinesweeperGame(5, 0)
    with pytest.raises(ValueError):
        MinesweeperGame(5, 1)


def test_flag_toggle():
    game = MinesweeperGame(5, 0.2)
    
    # Flag a cell
    assert game.toggle_flag(0, 0) == True
    cell_info = game.get_cell_info(0, 0)
    assert cell_info.state == CellState.FLAGGED
    assert game.flag_count == 1
    
    # Unflag the cell
    assert game.toggle_flag(0, 0) == True
    cell_info = game.get_cell_info(0, 0)
    assert cell_info.state == CellState.HIDDEN
    assert game.flag_count == 0


def test_reveal_cell():
    game = MinesweeperGame(5, 0.1)  # Low mine density
    
    # First click should place mines and reveal cells
    result = game.reveal_cell(2, 2)
    assert result == True
    assert game.first_click == False
    assert game.revealed_count > 0


def test_invalid_positions():
    game = MinesweeperGame(5, 0.2)
    
    # Test out of bounds positions
    assert game.reveal_cell(-1, 0) == False
    assert game.reveal_cell(0, -1) == False
    assert game.reveal_cell(5, 0) == False
    assert game.reveal_cell(0, 5) == False
    
    assert game.toggle_flag(-1, 0) == False
    assert game.toggle_flag(5, 5) == False


def test_game_stats():
    game = MinesweeperGame(5, 0.2)
    stats = game.get_game_stats()
    
    assert stats.size == 5
    assert stats.mine_count == 5
    assert stats.flag_count == 0
    assert stats.revealed_count == 0
    assert stats.game_state == GameState.PLAYING
    assert stats.remaining_mines == 5


def test_reset_game():
    game = MinesweeperGame(5, 0.2)
    
    # Make some moves
    game.toggle_flag(0, 0)
    game.reveal_cell(2, 2)
    
    # Reset
    game.reset()
    
    assert game.game_state == GameState.PLAYING
    assert game.first_click == True
    assert game.revealed_count == 0
    assert game.flag_count == 0


def test_cannot_flag_revealed_cell():
    game = MinesweeperGame(10, 0.1)  # Large board, low mine density
    
    # Reveal a cell first
    game.reveal_cell(5, 5)
    
    # Try to flag the revealed cell - should fail
    assert game.toggle_flag(5, 5) == False