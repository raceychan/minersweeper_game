import json
from typing import Dict, List, Optional
from openai import OpenAI
from .minesweeper import MinesweeperGame
from .model import CellState


class MinesweeperAIAssistant:
    """AI Assistant for Minesweeper game using OpenAI's GPT models."""
    
    def __init__(self, api_key: str):
        """Initialize AI assistant with OpenAI API key.
        
        Args:
            api_key: OpenAI API key for authentication
        """
        self.client = OpenAI(api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
    
    def get_game_state_prompt(self, game: MinesweeperGame) -> str:
        """Generate a detailed prompt with current game state information."""
        
        # Build board representation with complete information
        board_info = []
        for row in range(game.size):
            row_info = []
            for col in range(game.size):
                cell = game.board[row][col]
                cell_info = {
                    "position": f"({row},{col})",
                    "state": cell.state.value,
                    "is_mine": cell.is_mine,
                    "adjacent_mines": cell.adjacent_mines if not cell.is_mine else None,
                    "visible_to_user": cell.state == CellState.REVEALED
                }
                row_info.append(cell_info)
            board_info.append(row_info)
        
        # Get game statistics
        stats = game.get_game_stats()
        
        # Build the comprehensive prompt
        prompt = f"""You are an AI assistant helping a player with Minesweeper strategy. You have complete knowledge of the game board including mine locations, but the player does not know where the mines are.

CURRENT GAME STATE:
- Board size: {game.size}x{game.size}
- Total mines: {game.mine_count}
- Mines remaining: {stats.remaining_mines}
- Flags placed: {stats.flag_count}
- Cells revealed: {stats.revealed_count}
- Game status: {game.game_state.value}

COMPLETE BOARD INFORMATION (HIDDEN FROM PLAYER):
{json.dumps(board_info, indent=2)}

INSTRUCTIONS FOR AI ASSISTANT:
1. You can see all mine locations and safe cells, but the player cannot
2. Provide strategic advice without directly revealing mine locations
3. Suggest safe moves when possible
4. Help with logical deduction based on visible numbers
5. Explain Minesweeper rules and strategies when asked
6. Be encouraging and helpful
7. Never directly state "there is a mine at position (x,y)" - instead guide them to discover patterns
8. You can suggest safe cells to click or good areas to explore
9. Help them understand number patterns and probability

The player will ask you questions about their next move or strategy. Provide helpful guidance while keeping the game challenging and educational.

Player's question: """
        
        return prompt
    
    async def get_assistance(self, game: MinesweeperGame, user_question: str) -> str:
        """Get AI assistance for the current game state and user question.
        
        Args:
            game: Current MinesweeperGame instance
            user_question: The user's question or request for help
            
        Returns:
            AI assistant's response
        """
        try:
            # Build the full prompt with game state
            system_prompt = self.get_game_state_prompt(game)
            full_prompt = system_prompt + user_question
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_question
            })
            
            # Prepare messages for OpenAI API
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_question
                }
            ]
            
            # Add recent conversation history (last 6 messages to keep context)
            if len(self.conversation_history) > 2:
                recent_history = self.conversation_history[-6:]
                messages.extend(recent_history)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            return assistant_response
            
        except Exception as e:
            return f"Sorry, I encountered an error while processing your request: {str(e)}"
    
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []


# In-memory storage for API keys and AI assistants per session
AI_ASSISTANTS: Dict[str, MinesweeperAIAssistant] = {}


def get_or_create_assistant(session_id: str, api_key: str) -> MinesweeperAIAssistant:
    """Get existing AI assistant for session or create new one.
    
    Args:
        session_id: Unique session identifier
        api_key: OpenAI API key
        
    Returns:
        MinesweeperAIAssistant instance
    """
    if session_id not in AI_ASSISTANTS:
        AI_ASSISTANTS[session_id] = MinesweeperAIAssistant(api_key)
    return AI_ASSISTANTS[session_id]


def remove_assistant(session_id: str):
    """Remove AI assistant for session (clears API key from memory).
    
    Args:
        session_id: Unique session identifier
    """
    if session_id in AI_ASSISTANTS:
        del AI_ASSISTANTS[session_id]