from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with game sessions
    game_sessions = relationship("GameSession", back_populates="user")
    saved_games = relationship("SavedGame", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class GameSession(Base):
    __tablename__ = 'game_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    board_size = Column(Integer, nullable=False)
    mine_count = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False)  # beginner, intermediate, expert
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    result = Column(String(10), nullable=True)  # won, lost, quit
    cells_revealed = Column(Integer, default=0)
    flags_used = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    
    # Relationship with user
    user = relationship("User", back_populates="game_sessions")
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, user_id={self.user_id}, difficulty='{self.difficulty}', result='{self.result}')>"

class SavedGame(Base):
    __tablename__ = 'saved_games'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    game_name = Column(String(100), nullable=False)
    board_size = Column(Integer, nullable=False)
    mine_count = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False)
    game_state = Column(String(20), nullable=False)  # playing, won, lost
    board_data = Column(Text, nullable=False)  # JSON serialized board state
    revealed_count = Column(Integer, default=0)
    flag_count = Column(Integer, default=0)
    first_click = Column(Boolean, default=True)
    saved_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with user
    user = relationship("User", back_populates="saved_games")
    
    def __repr__(self):
        return f"<SavedGame(id={self.id}, user_id={self.user_id}, name='{self.game_name}')>"

class GameDatabase:
    def __init__(self, db_path: str = "src/data/minesweeper.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    # User management
    def create_user(self, username: str) -> User:
        user = User(username=username)
        self.session.add(user)
        self.session.commit()
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter_by(username=username).first()
    
    def get_or_create_user(self, username: str) -> User:
        user = self.get_user_by_username(username)
        if not user:
            user = self.create_user(username)
        return user
    
    # Game session management
    def create_game_session(self, user_id: int, board_size: int, mine_count: int, difficulty: str) -> GameSession:
        session = GameSession(
            user_id=user_id,
            board_size=board_size,
            mine_count=mine_count,
            difficulty=difficulty
        )
        self.session.add(session)
        self.session.commit()
        return session
    
    def update_game_session(self, session_id: int, **kwargs) -> Optional[GameSession]:
        session = self.session.query(GameSession).filter_by(id=session_id).first()
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            self.session.commit()
        return session
    
    def finish_game_session(self, session_id: int, result: str, cells_revealed: int, flags_used: int):
        end_time = datetime.utcnow()
        session = self.session.query(GameSession).filter_by(id=session_id).first()
        if session and session.start_time:
            duration = (end_time - session.start_time).total_seconds()
            self.update_game_session(
                session_id=session_id,
                end_time=end_time,
                duration_seconds=duration,
                result=result,
                cells_revealed=cells_revealed,
                flags_used=flags_used,
                is_completed=True
            )
    
    # Saved game management
    def save_game(self, user_id: int, game_name: str, board_size: int, mine_count: int, 
                  difficulty: str, game_state: str, board_data: dict, revealed_count: int, 
                  flag_count: int, first_click: bool) -> SavedGame:
        # Check if a saved game with this name already exists for the user
        existing_game = self.session.query(SavedGame).filter_by(
            user_id=user_id, game_name=game_name
        ).first()
        
        if existing_game:
            # Update existing saved game
            existing_game.board_size = board_size
            existing_game.mine_count = mine_count
            existing_game.difficulty = difficulty
            existing_game.game_state = game_state
            existing_game.board_data = json.dumps(board_data)
            existing_game.revealed_count = revealed_count
            existing_game.flag_count = flag_count
            existing_game.first_click = first_click
            existing_game.saved_at = datetime.utcnow()
            saved_game = existing_game
        else:
            # Create new saved game
            saved_game = SavedGame(
                user_id=user_id,
                game_name=game_name,
                board_size=board_size,
                mine_count=mine_count,
                difficulty=difficulty,
                game_state=game_state,
                board_data=json.dumps(board_data),
                revealed_count=revealed_count,
                flag_count=flag_count,
                first_click=first_click
            )
            self.session.add(saved_game)
        
        self.session.commit()
        return saved_game
    
    def load_game(self, user_id: int, game_name: str) -> Optional[SavedGame]:
        return self.session.query(SavedGame).filter_by(
            user_id=user_id, game_name=game_name
        ).first()
    
    def get_user_saved_games(self, user_id: int) -> List[SavedGame]:
        return self.session.query(SavedGame).filter_by(user_id=user_id).all()
    
    def delete_saved_game(self, user_id: int, game_name: str) -> bool:
        saved_game = self.session.query(SavedGame).filter_by(
            user_id=user_id, game_name=game_name
        ).first()
        if saved_game:
            self.session.delete(saved_game)
            self.session.commit()
            return True
        return False
    
    # Statistics
    def get_user_stats(self, user_id: int):
        total_games = self.session.query(GameSession).filter_by(
            user_id=user_id, is_completed=True
        ).count()
        won_games = self.session.query(GameSession).filter_by(
            user_id=user_id, result='won'
        ).count()
        win_rate = (won_games / total_games * 100) if total_games > 0 else 0
        
        return {
            'total_games': total_games,
            'won_games': won_games,
            'lost_games': total_games - won_games,
            'win_rate': round(win_rate, 2)
        }
    
    def get_game_stats(self):
        total_games = self.session.query(GameSession).filter_by(is_completed=True).count()
        won_games = self.session.query(GameSession).filter_by(result='won').count()
        win_rate = (won_games / total_games * 100) if total_games > 0 else 0
        
        return {
            'total_games': total_games,
            'won_games': won_games,
            'lost_games': total_games - won_games,
            'win_rate': round(win_rate, 2)
        }
    
    def close(self):
        self.session.close()