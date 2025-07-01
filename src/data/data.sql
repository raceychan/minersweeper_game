-- Minesweeper Game Data Schema
-- This file contains the SQL schema for recording minesweeper game data

-- Table to store users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table to store individual game sessions
CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    board_size INTEGER NOT NULL,
    mine_count INTEGER NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'expert', 'custom')),
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    duration_seconds REAL,
    result TEXT CHECK (result IN ('won', 'lost', 'quit')),
    cells_revealed INTEGER DEFAULT 0,
    flags_used INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Table to store saved games
CREATE TABLE IF NOT EXISTS saved_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_name TEXT NOT NULL,
    board_size INTEGER NOT NULL,
    mine_count INTEGER NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'expert', 'custom')),
    game_state TEXT NOT NULL CHECK (game_state IN ('playing', 'won', 'lost')),
    board_data TEXT NOT NULL,  -- JSON serialized board state
    revealed_count INTEGER DEFAULT 0,
    flag_count INTEGER DEFAULT 0,
    first_click BOOLEAN DEFAULT 1,
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, game_name)
);

-- Indexes for faster queries on common filters
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_id ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_difficulty ON game_sessions(difficulty);
CREATE INDEX IF NOT EXISTS idx_game_sessions_result ON game_sessions(result);
CREATE INDEX IF NOT EXISTS idx_game_sessions_completed ON game_sessions(is_completed);
CREATE INDEX IF NOT EXISTS idx_game_sessions_start_time ON game_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_saved_games_user_id ON saved_games(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_games_user_game ON saved_games(user_id, game_name);

-- Sample data for testing (optional)
-- INSERT INTO game_sessions (board_size, mine_count, difficulty, result, duration_seconds, cells_revealed, flags_used, is_completed)
-- VALUES 
--     (9, 10, 'beginner', 'won', 45.5, 71, 10, 1),
--     (16, 40, 'intermediate', 'lost', 120.3, 89, 15, 1),
--     (22, 99, 'expert', 'won', 300.8, 387, 99, 1);

-- Query examples for game statistics
-- Get overall win rate:
-- SELECT 
--     COUNT(*) as total_games,
--     SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as won_games,
--     ROUND(SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate
-- FROM game_sessions 
-- WHERE is_completed = 1;

-- Get best times by difficulty:
-- SELECT difficulty, MIN(duration_seconds) as best_time
-- FROM game_sessions 
-- WHERE result = 'won' AND is_completed = 1
-- GROUP BY difficulty;

-- Get recent games:
-- SELECT difficulty, result, duration_seconds, start_time
-- FROM game_sessions 
-- WHERE is_completed = 1
-- ORDER BY start_time DESC
-- LIMIT 10;