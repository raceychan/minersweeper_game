from src.domain.minesweeper import MinesweeperGame
from src.domain.model import GameState, CellState


def main():
    # Example usage with user authentication
    try:
        username = input("Enter your username: ").strip()
        if not username:
            username = "anonymous"
    except EOFError:
        username = "testuser"  # Default for testing
    
    game = MinesweeperGame(size=8, difficulty=0.15, username=username)
    
    print(f"\nWelcome, {username}!")
    print("Minesweeper Game Created!")
    print(f"Board size: {game.size}x{game.size}")
    print(f"Mine count: {game.mine_count}")
    print(f"Game state: {game.game_state.value}")
    
    # Show user stats if available
    user_stats = game.get_user_stats()
    if user_stats:
        print(f"\nYour Stats:")
        print(f"Total games: {user_stats['total_games']}")
        print(f"Won games: {user_stats['won_games']}")
        print(f"Win rate: {user_stats['win_rate']}%")
    
    # Show saved games
    saved_games = game.get_saved_games()
    if saved_games:
        print(f"\nSaved games: {', '.join(saved_games)}")
    
    # Example moves
    print("\nMaking first move at (3, 3)...")
    game.reveal_cell(3, 3)
    
    print(f"Revealed cells: {game.revealed_count}")
    print(f"Game state: {game.game_state.value}")
    
    # Flag a cell
    print("\nFlagging cell at (0, 0)...")
    game.toggle_flag(0, 0)
    
    stats = game.get_game_stats()
    print(f"Flags used: {stats.flag_count}")
    print(f"Remaining mines: {stats.remaining_mines}")
    
    # Demo save game functionality
    print("\nSaving game as 'demo_game'...")
    if game.save_game("demo_game"):
        print("Game saved successfully!")
    else:
        print("Failed to save game.")


if __name__ == "__main__":
    main()
