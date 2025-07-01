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
        
        // AI Chat elements
        this.apiKeyModal = document.getElementById('api-key-modal');
        this.chatModal = document.getElementById('chat-modal');
        this.apiKeyInput = document.getElementById('api-key-input');
        this.chatInput = document.getElementById('chat-input');
        this.chatMessages = document.getElementById('chat-messages');
        
        this.gameId = null;
        this.gameState = 'playing';
        this.startTime = null;
        this.timerInterval = null;
        this.currentUsername = null;
        this.aiSessionId = null;
        
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
        
        // Cheat functionality
        document.getElementById('cheat-btn').addEventListener('click', () => this.handleCheat());
        
        // AI Chat functionality
        document.getElementById('ai-chat-btn').addEventListener('click', () => this.showAIChat());
        document.getElementById('api-key-confirm-btn').addEventListener('click', () => this.handleSetAPIKey());
        document.getElementById('send-chat-btn').addEventListener('click', () => this.handleSendMessage());
        document.getElementById('clear-chat-btn').addEventListener('click', () => this.handleClearChat());
        document.getElementById('remove-api-key-btn').addEventListener('click', () => this.handleRemoveAPIKey());
        
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
        
        // API key input enter key
        this.apiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSetAPIKey();
        });
        
        // Chat input enter key
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSendMessage();
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
    
    async handleCheat() {
        if (this.gameState !== 'playing') {
            alert('No active game to cheat in');
            return;
        }
        
        if (!this.gameId) {
            alert('No game in progress');
            return;
        }
        
        if (!this.startTime) {
            this.startTimer();
        }
        
        try {
            const response = await fetch('/api/cheat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game_id: this.gameId })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateBoard(data.board);
                this.updateStats(data.stats);
                
                if (data.game_state !== 'playing') {
                    this.endGame(data.game_state);
                    await this.loadUserStats();
                }
            } else {
                const error = await response.json();
                alert(`Cheat failed: ${error.detail}`);
            }
            
        } catch (error) {
            console.error('Error using cheat:', error);
            alert('Failed to use cheat');
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
    
    // AI Assistant Methods
    showAIChat() {
        if (!this.aiSessionId) {
            this.showAPIKeyModal();
        } else {
            this.chatModal.classList.remove('hidden');
            this.chatInput.focus();
        }
    }
    
    showAPIKeyModal() {
        this.apiKeyModal.classList.remove('hidden');
        this.apiKeyInput.focus();
    }
    
    async handleSetAPIKey() {
        const apiKey = this.apiKeyInput.value.trim();
        
        if (!apiKey) {
            alert('Please enter an API key');
            return;
        }
        
        if (!apiKey.startsWith('sk-')) {
            alert('Please enter a valid OpenAI API key (starts with sk-)');
            return;
        }
        
        try {
            const response = await fetch('/api/set_api_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.aiSessionId = data.session_id;
                this.hideModal('api-key-modal');
                this.apiKeyInput.value = '';
                this.chatModal.classList.remove('hidden');
                this.chatInput.focus();
            } else {
                const error = await response.json();
                alert(`Failed to set API key: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error setting API key:', error);
            alert('Failed to set API key');
        }
    }
    
    async handleSendMessage() {
        const message = this.chatInput.value.trim();
        
        if (!message) {
            return;
        }
        
        if (!this.gameId) {
            alert('Please start a game first');
            return;
        }
        
        if (!this.aiSessionId) {
            alert('Please set up your API key first');
            return;
        }
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        this.chatInput.value = '';
        
        // Show loading message
        const loadingId = this.addChatMessage('Thinking...', 'assistant', true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_id: this.gameId,
                    message: message,
                    session_id: this.aiSessionId
                })
            });
            
            const data = await response.json();
            
            // Remove loading message
            this.removeChatMessage(loadingId);
            
            if (data.success) {
                this.addChatMessage(data.response, 'assistant');
            } else {
                this.addChatMessage(`Error: ${data.response}`, 'assistant');
            }
            
        } catch (error) {
            this.removeChatMessage(loadingId);
            this.addChatMessage(`Error: ${error.message}`, 'assistant');
            console.error('Chat error:', error);
        }
    }
    
    addChatMessage(message, sender, isLoading = false) {
        const messageDiv = document.createElement('div');
        const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        messageDiv.id = messageId;
        messageDiv.className = `chat-message ${sender}-message`;
        
        if (isLoading) {
            messageDiv.classList.add('loading');
        }
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (sender === 'user') {
            content.innerHTML = `<strong>You:</strong> ${message}`;
        } else {
            content.innerHTML = `<strong>AI Assistant:</strong> ${message}`;
        }
        
        messageDiv.appendChild(content);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return messageId;
    }
    
    removeChatMessage(messageId) {
        const messageEl = document.getElementById(messageId);
        if (messageEl) {
            messageEl.remove();
        }
    }
    
    handleClearChat() {
        // Keep only the initial assistant message
        const messages = this.chatMessages.querySelectorAll('.chat-message');
        for (let i = 1; i < messages.length; i++) {
            messages[i].remove();
        }
    }
    
    async handleRemoveAPIKey() {
        if (!this.aiSessionId) {
            return;
        }
        
        if (!confirm('Remove API key from memory? You will need to enter it again to use the AI assistant.')) {
            return;
        }
        
        try {
            await fetch('/api/remove_api_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: this.aiSessionId })
            });
            
            this.aiSessionId = null;
            this.hideModal('chat-modal');
            this.handleClearChat();
            
        } catch (error) {
            console.error('Error removing API key:', error);
        }
    }
}

// Global variable for accessing from onclick handlers
let minesweeperGame;

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    minesweeperGame = new MinesweeperWeb();
});