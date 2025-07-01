class MinesweeperWeb {
    constructor() {
        this.gameBoard = document.getElementById('game-board');
        this.flagCountEl = document.getElementById('flag-count');
        this.timerEl = document.getElementById('timer');
        this.mineCountEl = document.getElementById('mine-count');
        this.overlay = document.getElementById('game-overlay');
        this.overlayTitle = document.getElementById('overlay-title');
        this.overlayMessage = document.getElementById('overlay-message');
        this.winIcon = document.getElementById('win-icon');
        this.loseIcon = document.getElementById('lose-icon');
        
        // Login elements
        this.loginSection = document.getElementById('login-section');
        this.gameSection = document.getElementById('game-section');
        this.usernameInput = document.getElementById('username-input');
        this.currentUsernameEl = document.getElementById('current-username');
        
        // User stats elements
        this.totalGamesEl = document.getElementById('total-games');
        this.wonGamesEl = document.getElementById('won-games');
        this.winRateEl = document.getElementById('win-rate');
        
        // Modal elements
        this.saveModal = document.getElementById('save-modal');
        this.loadModal = document.getElementById('load-modal');
        this.saveNameInput = document.getElementById('save-name');
        this.savedGamesList = document.getElementById('saved-games-list');
        
        this.gameId = null;
        this.gameState = 'playing';
        this.startTime = null;
        this.timerInterval = null;
        this.currentUsername = null;
        
        this.initializeEventListeners();
        this.showLoginSection();
    }
    
    initializeEventListeners() {
        // Login functionality
        document.getElementById('login-btn').addEventListener('click', () => this.handleLogin());
        this.usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
        
        // Logout functionality
        document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());
        
        // Difficulty buttons
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.difficulty-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const size = parseInt(e.target.dataset.size);
                const mines = parseInt(e.target.dataset.mines);
                this.newGame(size, mines);
            });
        });
        
        // New game buttons
        document.getElementById('new-game-btn').addEventListener('click', () => {
            const activeBtn = document.querySelector('.difficulty-btn.active');
            const size = parseInt(activeBtn.dataset.size);
            const mines = parseInt(activeBtn.dataset.mines);
            this.newGame(size, mines);
        });
        
        document.getElementById('overlay-new-game').addEventListener('click', () => {
            const activeBtn = document.querySelector('.difficulty-btn.active');
            const size = parseInt(activeBtn.dataset.size);
            const mines = parseInt(activeBtn.dataset.mines);
            this.newGame(size, mines);
        });
        
        // Save/Load functionality
        document.getElementById('save-game-btn').addEventListener('click', () => this.showSaveModal());
        document.getElementById('load-game-btn').addEventListener('click', () => this.showLoadModal());
        document.getElementById('save-confirm-btn').addEventListener('click', () => this.handleSaveGame());
        
        // Modal close functionality
        document.querySelectorAll('.modal-close, .modal-btn.secondary').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modalId = e.target.dataset.modal || e.target.closest('.modal').id;
                this.hideModal(modalId);
            });
        });
        
        // Close modals when clicking outside
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });
        
        // Save name input enter key
        this.saveNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSaveGame();
        });
    }
    
    showLoginSection() {
        this.loginSection.classList.remove('hidden');
        this.gameSection.classList.add('hidden');
        this.usernameInput.focus();
    }
    
    showGameSection() {
        this.loginSection.classList.add('hidden');
        this.gameSection.classList.remove('hidden');
    }
    
    async handleLogin() {
        const username = this.usernameInput.value.trim();
        if (!username) {
            alert('Please enter a username');
            return;
        }
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentUsername = data.username;
                this.currentUsernameEl.textContent = this.currentUsername;
                this.showGameSection();
                await this.loadUserStats();
                this.newGame(9, 10); // Start with beginner game
            } else {
                alert('Login failed. Please try again.');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed. Please try again.');
        }
    }
    
    handleLogout() {
        this.currentUsername = null;
        this.usernameInput.value = '';
        this.gameId = null;
        this.resetTimer();
        this.showLoginSection();
    }
    
    async loadUserStats() {
        if (!this.currentUsername) return;
        
        try {
            const response = await fetch(`/api/user_stats/${this.currentUsername}`);
            if (response.ok) {
                const stats = await response.json();
                this.totalGamesEl.textContent = stats.total_games;
                this.wonGamesEl.textContent = stats.won_games;
                this.winRateEl.textContent = `${stats.win_rate}%`;
            }
        } catch (error) {
            console.error('Error loading user stats:', error);
        }
    }
    
    async newGame(size, mines) {
        if (!this.currentUsername) {
            alert('Please login first');
            return;
        }
        
        try {
            const response = await fetch('/api/new_game_with_user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ size, mines, username: this.currentUsername })
            });
            
            const data = await response.json();
            this.gameId = data.game_id;
            this.gameState = 'playing';
            
            this.hideOverlay();
            this.resetTimer();
            this.createBoard(size);
            this.updateStats(data.stats);
            
        } catch (error) {
            console.error('Error creating new game:', error);
        }
    }
    
    showSaveModal() {
        if (!this.gameId || this.gameState !== 'playing') {
            alert('No active game to save');
            return;
        }
        this.saveModal.classList.remove('hidden');
        this.saveNameInput.focus();
    }
    
    async showLoadModal() {
        if (!this.currentUsername) {
            alert('Please login first');
            return;
        }
        
        await this.loadSavedGamesList();
        this.loadModal.classList.remove('hidden');
    }
    
    async loadSavedGamesList() {
        try {
            const response = await fetch(`/api/saved_games/${this.currentUsername}`);
            if (response.ok) {
                const savedGames = await response.json();
                this.renderSavedGamesList(savedGames);
            }
        } catch (error) {
            console.error('Error loading saved games:', error);
        }
    }
    
    renderSavedGamesList(savedGames) {
        if (savedGames.length === 0) {
            this.savedGamesList.innerHTML = '<p class="no-saves">No saved games found</p>';
            return;
        }
        
        this.savedGamesList.innerHTML = savedGames.map(game => `
            <div class="saved-game-item">
                <div class="saved-game-info">
                    <h4>${game.game_name}</h4>
                    <p>${game.difficulty} - ${game.game_state} - ${new Date(game.saved_at).toLocaleDateString()}</p>
                </div>
                <div class="saved-game-actions">
                    <button class="load-btn" onclick="minesweeperGame.handleLoadGame('${game.game_name}')">Load</button>
                    <button class="delete-btn" onclick="minesweeperGame.handleDeleteSavedGame('${game.game_name}')">Delete</button>
                </div>
            </div>
        `).join('');
    }
    
    async handleSaveGame() {
        const gameName = this.saveNameInput.value.trim();
        if (!gameName) {
            alert('Please enter a game name');
            return;
        }
        
        try {
            const response = await fetch('/api/save_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game_id: this.gameId, game_name: gameName })
            });
            
            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                this.hideModal('save-modal');
                this.saveNameInput.value = '';
            } else {
                const error = await response.json();
                alert(`Save failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error saving game:', error);
            alert('Failed to save game');
        }
    }
    
    async handleLoadGame(gameName) {
        try {
            const response = await fetch('/api/load_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: this.currentUsername, game_name: gameName })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Extract all the data we need
                this.gameId = data.game_id;
                this.gameState = data.game_state;
                
                // Calculate board size from the board data
                const size = data.board.length;
                
                // Create board and update with loaded state
                this.createBoard(size);
                this.updateBoard(data.board);
                this.updateStats(data.stats);
                
                this.hideModal('load-modal');
                this.resetTimer();
                
                // If the game was already finished, show the overlay
                if (this.gameState !== 'playing') {
                    this.endGame(this.gameState);
                }
                
                alert(`Game "${gameName}" loaded successfully!`);
                
            } else {
                const error = await response.json();
                alert(`Load failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error loading game:', error);
            alert('Failed to load game');
        }
    }
    
    async handleDeleteSavedGame(gameName) {
        if (!confirm(`Are you sure you want to delete "${gameName}"?`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/delete_saved_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: this.currentUsername, game_name: gameName })
            });
            
            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                await this.loadSavedGamesList(); // Refresh the list
            } else {
                const error = await response.json();
                alert(`Delete failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error deleting saved game:', error);
            alert('Failed to delete game');
        }
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    }
    
    createBoard(size) {
        this.gameBoard.innerHTML = '';
        this.gameBoard.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
        
        for (let row = 0; row < size; row++) {
            for (let col = 0; col < size; col++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.row = row;
                cell.dataset.col = col;
                
                cell.addEventListener('click', (e) => this.handleCellClick(e));
                cell.addEventListener('contextmenu', (e) => this.handleRightClick(e));
                
                this.gameBoard.appendChild(cell);
            }
        }
    }
    
    async handleCellClick(event) {
        if (this.gameState !== 'playing') return;
        
        const row = parseInt(event.target.dataset.row);
        const col = parseInt(event.target.dataset.col);
        
        if (!this.startTime) {
            this.startTimer();
        }
        
        try {
            const response = await fetch('/api/reveal_cell', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game_id: this.gameId, row, col })
            });
            
            const data = await response.json();
            this.updateBoard(data.board);
            this.updateStats(data.stats);
            
            if (data.game_state !== 'playing') {
                this.endGame(data.game_state);
                await this.loadUserStats(); // Refresh stats after game ends
            }
            
        } catch (error) {
            console.error('Error revealing cell:', error);
        }
    }
    
    async handleRightClick(event) {
        event.preventDefault();
        
        if (this.gameState !== 'playing') return;
        
        const row = parseInt(event.target.dataset.row);
        const col = parseInt(event.target.dataset.col);
        
        try {
            const response = await fetch('/api/toggle_flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game_id: this.gameId, row, col })
            });
            
            const data = await response.json();
            this.updateBoard(data.board);
            this.updateStats(data.stats);
            
        } catch (error) {
            console.error('Error toggling flag:', error);
        }
    }
    
    updateBoard(boardData) {
        boardData.forEach(row => {
            row.forEach(cellData => {
                const cell = document.querySelector(`[data-row="${cellData.row}"][data-col="${cellData.col}"]`);
                
                // Reset classes
                cell.className = 'cell';
                cell.textContent = '';
                cell.removeAttribute('data-count');
                
                if (cellData.state === 'revealed') {
                    cell.classList.add('revealed');
                    if (cellData.is_mine) {
                        cell.classList.add('mine');
                        if (cellData.mine_hit) {
                            cell.classList.add('mine-hit');
                        }
                    } else if (cellData.adjacent_mines > 0) {
                        cell.textContent = cellData.adjacent_mines;
                        cell.setAttribute('data-count', cellData.adjacent_mines);
                    }
                } else if (cellData.state === 'flagged') {
                    cell.classList.add('flagged');
                }
            });
        });
    }
    
    updateStats(stats) {
        this.flagCountEl.textContent = stats.flag_count;
        this.mineCountEl.textContent = stats.remaining_mines;
    }
    
    startTimer() {
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            this.timerEl.textContent = elapsed.toString().padStart(3, '0');
        }, 1000);
    }
    
    resetTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        this.startTime = null;
        this.timerEl.textContent = '000';
    }
    
    endGame(gameState) {
        this.gameState = gameState;
        this.resetTimer();
        
        if (gameState === 'won') {
            this.overlayTitle.textContent = 'Congratulations!';
            this.overlayMessage.textContent = 'You found all the mines!';
            this.winIcon.style.display = 'block';
            this.loseIcon.style.display = 'none';
        } else {
            this.overlayTitle.textContent = 'Game Over';
            this.overlayMessage.textContent = 'You hit a mine! Try again.';
            this.winIcon.style.display = 'none';
            this.loseIcon.style.display = 'block';
        }
        
        this.showOverlay();
    }
    
    showOverlay() {
        this.overlay.classList.remove('hidden');
    }
    
    hideOverlay() {
        this.overlay.classList.add('hidden');
    }
}

// Global variable for accessing from onclick handlers
let minesweeperGame;

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    minesweeperGame = new MinesweeperWeb();
});