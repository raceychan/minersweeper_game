import argparse
import sys
from .domain.minesweeper import MinesweeperGame


def main():
    parser = argparse.ArgumentParser(description='Minesweeper Game')
    parser.add_argument('--web', action='store_true', help='Launch web interface')
    parser.add_argument('--host', default='127.0.0.1', help='Host for web server (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port for web server (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for web server')
    
    args = parser.parse_args()
    
    if args.web:
        try:
            from .web.server import start_web_server
            start_web_server(host=args.host, port=args.port, debug=args.debug)
        except ImportError as e:
            print(f"Error: Could not import web server dependencies: {e}")
            print("Make sure Flask is installed: pip install flask")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down web server...")
            sys.exit(0)
        except Exception as e:
            print(f"Error starting web server: {e}")
            sys.exit(1)
    else:
        # Default behavior - show example usage
        print("🎮 Minesweeper Game")
        print()
        print("Usage:")
        print("  python -m src --web          # Launch web interface")
        print("  python -m src --web --port 8080  # Launch on custom port")
        print()
        print("Example game creation:")
        game = MinesweeperGame(size=8, difficulty=0.15)
        print(f"Created {game.size}x{game.size} board with {game.mine_count} mines")
        print(f"Game state: {game.game_state.value}")
        print()
        print("To play the web version, run: python -m src --web")


if __name__ == "__main__":
    main()