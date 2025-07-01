import uuid
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from lihil import HTTPException, Lihil, Route
from starlette.responses import FileResponse, HTMLResponse

from ..domain.minesweeper import MinesweeperGame
from ..domain.model import GameState, GameStats
from ..domain.ai_assistant import get_or_create_assistant, remove_assistant


class FileNotFoundError(HTTPException):
    status_code = 404
    detail = "File not found"


class GameNotFoundError(HTTPException):
    status_code = 404
    detail = "Game not found"


class InvalidMoveError(HTTPException):
    status_code = 400
    detail = "Invalid move"


@dataclass
class NewGameRequest:
    size: int = 9
    mines: int = 10


@dataclass
class CellActionRequest:
    game_id: str
    row: int
    col: int


@dataclass
class LoginRequest:
    username: str


@dataclass
class SaveGameRequest:
    game_id: str
    game_name: str


@dataclass
class LoadGameRequest:
    username: str
    game_name: str


@dataclass
class CheatRequest:
    game_id: str


@dataclass
class SetAPIKeyRequest:
    api_key: str


@dataclass
class ChatRequest:
    game_id: str
    message: str
    session_id: str


@dataclass
class ChatResponse:
    response: str
    success: bool


@dataclass
class UserStatsResponse:
    total_games: int
    won_games: int
    win_rate: float


@dataclass
class SavedGameInfo:
    game_name: str
    difficulty: str
    saved_at: str
    game_state: str


@dataclass
class CellData:
    row: int
    col: int
    state: str
    is_mine: bool
    adjacent_mines: int
    mine_hit: bool = False


@dataclass
class GameResponse:
    game_id: str
    stats: dict


@dataclass
class LoadGameResponse:
    game_id: str
    stats: dict
    board: List[List[CellData]]
    game_state: str


@dataclass
class BoardResponse:
    board: List[List[CellData]]
    stats: GameStats
    game_state: str


def get_board_data(
    game: MinesweeperGame, hit_row: int | None = None, hit_col: int | None = None
) -> List[List[CellData]]:
    board_data = []
    for row in range(game.size):
        row_data = []
        for col in range(game.size):
            cell = game.board[row][col]

            state = cell.state.value
            # If game is lost, reveal all mines
            if game.game_state == GameState.LOST and cell.is_mine:
                state = "revealed"

            cell_data = CellData(
                row=row,
                col=col,
                state=state,
                is_mine=cell.is_mine,
                adjacent_mines=cell.adjacent_mines,
                mine_hit=(
                    hit_row is not None
                    and hit_col is not None
                    and row == hit_row
                    and col == hit_col
                    and cell.is_mine
                ),
            )

            row_data.append(cell_data)
        board_data.append(row_data)
    return board_data


def get_game_stats(game: MinesweeperGame):
    return game.get_game_stats()


# Static files - serve CSS and JS directly
STATIC_PATH = Path(__file__).parent / "static"
GAMES: Dict[str, MinesweeperGame] = {}
USER_GAMES: Dict[str, str] = {}  # Maps game_id to username
API_KEYS: Dict[str, str] = {}  # Maps session_id to API key (in memory only)

# Static file routes
static_routes = Route("/static")


@static_routes.sub("/css/{filename}").get(to_thread=False)
def serve_css(filename: str):
    css_path = STATIC_PATH / "css" / filename
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    raise FileNotFoundError()


@static_routes.sub("/js/{filename}").get(to_thread=False)
def serve_js(filename: str):
    js_path = STATIC_PATH / "js" / filename
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    raise FileNotFoundError()


root = Route()


# Main page
@root.get(to_thread=False)
def index():
    template_path = Path(__file__).parent / "templates" / "index.html"
    with open(template_path, "r") as f:
        content = f.read()
    return HTMLResponse(content)


# API routes
api = Route("/api")


@api.sub("/login").post(to_thread=False)
def login(request: LoginRequest) -> dict:
    username = request.username.strip()
    if not username:
        raise HTTPException(problem_status=400, detail="Username cannot be empty")

    return {"success": True, "username": username}


@api.sub("/user_stats/{username}").get(to_thread=False)
def get_user_stats(username: str) -> UserStatsResponse:
    # Create a temporary game instance to access database
    game = MinesweeperGame(size=9, difficulty=0.15, username=username)
    stats = game.get_user_stats()
    game.db.close()

    if stats:
        return UserStatsResponse(
            total_games=stats["total_games"],
            won_games=stats["won_games"],
            win_rate=stats["win_rate"],
        )
    else:
        return UserStatsResponse(total_games=0, won_games=0, win_rate=0.0)


@api.sub("/saved_games/{username}").get(to_thread=False)
def get_saved_games(username: str) -> List[SavedGameInfo]:
    # Create a temporary game instance to access database
    game = MinesweeperGame(size=9, difficulty=0.15, username=username)
    saved_games = game.db.get_user_saved_games(game.user.id)
    game.db.close()

    return [
        SavedGameInfo(
            game_name=sg.game_name,
            difficulty=sg.difficulty,
            saved_at=sg.saved_at.isoformat(),
            game_state=sg.game_state,
        )
        for sg in saved_games
    ]


@api.sub("/new_game").post(to_thread=False)
def new_game(request: NewGameRequest) -> GameResponse:
    size = request.size
    mines = request.mines

    # Calculate difficulty from mines and size
    difficulty = mines / (size * size)

    game_id = str(uuid.uuid4())
    game = MinesweeperGame(size, difficulty)

    # Override mine count to match exactly what was requested
    game.mine_count = mines

    GAMES[game_id] = game

    return GameResponse(game_id=game_id, stats=get_game_stats(game))


@api.sub("/new_game_with_user").post(to_thread=False)
def new_game_with_user(request: dict) -> GameResponse:
    size = request.get("size", 9)
    mines = request.get("mines", 10)
    username = request.get("username", "")

    if not username:
        raise HTTPException(problem_status=400, detail="Username is required")

    # Calculate difficulty from mines and size
    difficulty = mines / (size * size)

    game_id = str(uuid.uuid4())
    game = MinesweeperGame(size, difficulty, username=username)

    # Override mine count to match exactly what was requested
    game.mine_count = mines

    GAMES[game_id] = game
    USER_GAMES[game_id] = username

    return GameResponse(game_id=game_id, stats=get_game_stats(game))


@api.sub("/reveal_cell").post(to_thread=False)
def reveal_cell(request: CellActionRequest) -> BoardResponse:
    game_id = request.game_id
    row = request.row
    col = request.col

    if game_id not in GAMES:
        raise GameNotFoundError()

    game = GAMES[game_id]
    success = game.reveal_cell(row, col)

    if not success:
        raise InvalidMoveError()

    board_data = get_board_data(game, row, col)

    return BoardResponse(
        board=board_data,
        stats=get_game_stats(game),
        game_state=game.game_state.value,
    )


@api.sub("/toggle_flag").post(to_thread=False)
def toggle_flag(request: CellActionRequest) -> BoardResponse:
    game_id = request.game_id
    row = request.row
    col = request.col

    if game_id not in GAMES:
        raise GameNotFoundError()

    game = GAMES[game_id]
    success = game.toggle_flag(row, col)

    if not success:
        raise InvalidMoveError()

    board_data = get_board_data(game)

    return BoardResponse(
        board=board_data,
        stats=get_game_stats(game),
        game_state=game.game_state.value,
    )


@api.sub("/save_game").post(to_thread=False)
def save_game(request: SaveGameRequest) -> dict:
    game_id = request.game_id
    game_name = request.game_name

    if game_id not in GAMES:
        raise GameNotFoundError()

    game = GAMES[game_id]

    # Only allow saving if game has a user
    if not game.user:
        raise HTTPException(problem_status=400, detail="Game must have a user to save")

    success = game.save_game(game_name)

    if success:
        return {"success": True, "message": f"Game '{game_name}' saved successfully"}
    else:
        raise HTTPException(problem_status=500, detail="Failed to save game")


@api.sub("/load_game").post(to_thread=False)
def load_game(request: LoadGameRequest) -> LoadGameResponse:
    username = request.username
    game_name = request.game_name

    # Create a temporary game instance to load the game
    temp_game = MinesweeperGame(size=9, difficulty=0.15, username=username)
    success = temp_game.load_game(game_name)

    if not success:
        temp_game.db.close()
        raise HTTPException(problem_status=404, detail="Saved game not found")

    # Create a new game session with loaded state
    game_id = str(uuid.uuid4())
    GAMES[game_id] = temp_game
    USER_GAMES[game_id] = username

    # Get board data immediately
    board_data = get_board_data(temp_game)

    return LoadGameResponse(
        game_id=game_id,
        stats=get_game_stats(temp_game),
        board=board_data,
        game_state=temp_game.game_state.value,
    )


@api.sub("/get_board/{game_id}").get(to_thread=False)
def get_board(game_id: str) -> BoardResponse:
    if game_id not in GAMES:
        raise GameNotFoundError()

    game = GAMES[game_id]
    board_data = get_board_data(game)

    return BoardResponse(
        board=board_data,
        stats=get_game_stats(game),
        game_state=game.game_state.value,
    )


@api.sub("/delete_saved_game").post(to_thread=False)
def delete_saved_game(request: dict) -> dict:
    username = request.get("username", "")
    game_name = request.get("game_name", "")

    if not username or not game_name:
        raise HTTPException(
            problem_status=400, detail="Username and game name are required"
        )

    # Create a temporary game instance to access database
    game = MinesweeperGame(size=9, difficulty=0.15, username=username)
    success = game.delete_saved_game(game_name)
    game.db.close()

    if success:
        return {"success": True, "message": f"Game '{game_name}' deleted successfully"}
    else:
        raise HTTPException(problem_status=404, detail="Saved game not found")


@api.sub("/cheat").post(to_thread=False)
def cheat(request: CheatRequest) -> BoardResponse:
    game_id = request.game_id

    if game_id not in GAMES:
        raise GameNotFoundError()

    game = GAMES[game_id]
    result = game.cheat()

    if result is None:
        raise HTTPException(problem_status=400, detail="No safe cells available or game not in progress")

    revealed_row, revealed_col = result
    board_data = get_board_data(game)

    return BoardResponse(
        board=board_data,
        stats=get_game_stats(game),
        game_state=game.game_state.value,
    )


@api.sub("/set_api_key").post(to_thread=False)
def set_api_key(request: SetAPIKeyRequest) -> dict:
    api_key = request.api_key.strip()
    
    if not api_key:
        raise HTTPException(problem_status=400, detail="API key cannot be empty")
    
    if not api_key.startswith("sk-"):
        raise HTTPException(problem_status=400, detail="Invalid OpenAI API key format")
    
    # Generate a session ID for this API key
    session_id = str(uuid.uuid4())
    API_KEYS[session_id] = api_key
    
    return {"success": True, "session_id": session_id, "message": "API key set successfully"}


@api.sub("/remove_api_key").post(to_thread=False)
def remove_api_key(request: dict) -> dict:
    session_id = request.get("session_id", "")
    
    if session_id in API_KEYS:
        del API_KEYS[session_id]
        remove_assistant(session_id)
        return {"success": True, "message": "API key removed successfully"}
    
    return {"success": False, "message": "Session not found"}


@api.sub("/chat").post()
async def chat(request: ChatRequest) -> ChatResponse:
    game_id = request.game_id
    message = request.message.strip()
    session_id = request.session_id
    
    if not message:
        raise HTTPException(problem_status=400, detail="Message cannot be empty")
    
    if game_id not in GAMES:
        raise GameNotFoundError()
    
    if session_id not in API_KEYS:
        raise HTTPException(problem_status=400, detail="No API key found for this session")
    
    try:
        game = GAMES[game_id]
        api_key = API_KEYS[session_id]
        
        # Get or create AI assistant for this session
        assistant = get_or_create_assistant(session_id, api_key)
        
        # Get AI response
        response = await assistant.get_assistance(game, message)
        
        return ChatResponse(response=response, success=True)
        
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}", success=False)


def create_minesweeper_app() -> Lihil:
    app = Lihil(root)

    app.include_routes(api)
    app.include_routes(static_routes)
    return app


def start_web_server(host="127.0.0.1", port=5000, debug=False):
    import uvicorn

    app = create_minesweeper_app()
    print(f"🎮 Starting Minesweeper Web Server...")
    print(f"🌐 Server running at http://{host}:{port}")
    print(f"🚀 Opening browser...")

    uvicorn.run(
        app, host=host, port=port
    )  # , log_level="info" if debug else "warning")
