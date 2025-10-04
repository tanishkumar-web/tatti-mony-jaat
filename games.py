import random
from config import HANGMAN_WORDS

class TicTacToe:
    """Tic Tac Toe game implementation"""
    
    def __init__(self):
        self.board = self.initialize_board()
        self.current_player = "X"  # User is X, bot is O
        self.game_over = False
    
    def initialize_board(self):
        """Initialize Tic Tac Toe board"""
        return [
            ['_', '_', '_'],
            ['_', '_', '_'],
            ['_', '_', '_']
        ]
    
    def display_board(self):
        """Display Tic Tac Toe board"""
        board_str = "🎮 Tic Tac Toe\n\n"
        for i, row in enumerate(self.board):
            board_str += " | ".join(row) + "\n"
            if i < 2:
                board_str += "---------\n"
        return board_str
    
    def make_move(self, position):
        """Make a move in Tic Tac Toe"""
        # Convert position to row and column
        row = (position - 1) // 3
        col = (position - 1) % 3
        
        # Check if position is valid and empty
        if row < 0 or row > 2 or col < 0 or col > 2 or self.board[row][col] != "_":
            return self.display_board() + "\nInvalid move! Choose an empty position."
        
        # Make user move
        self.board[row][col] = "X"
        
        # Check for win or tie
        result = self.check_winner()
        if result:
            self.game_over = True
            return self.display_board() + f"\n{result}"
        
        # Bot's turn
        bot_move = self.get_bot_move()
        if bot_move:
            self.board[bot_move[0]][bot_move[1]] = "O"
            result = self.check_winner()
            if result:
                self.game_over = True
                return self.display_board() + f"\n{result}"
        
        return self.display_board()
    
    def check_winner(self):
        """Check for Tic Tac Toe winner"""
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != "_":
                return f"{'You win!' if row[0] == 'X' else 'I win!'} 🎉"
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != "_":
                return f"{'You win!' if self.board[0][col] == 'X' else 'I win!'} 🎉"
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "_":
            return f"{'You win!' if self.board[0][0] == 'X' else 'I win!'} 🎉"
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "_":
            return f"{'You win!' if self.board[0][2] == 'X' else 'I win!'} 🎉"
        
        # Check for tie
        if all(cell != "_" for row in self.board for cell in row):
            return "It's a tie! 🤝"
        
        return None
    
    def get_bot_move(self):
        """Get bot move for Tic Tac Toe (simple AI)"""
        # Try to win
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == "_":
                    self.board[i][j] = "O"
                    if self.check_winner():
                        self.board[i][j] = "_"
                        return (i, j)
                    self.board[i][j] = "_"
        
        # Try to block player
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == "_":
                    self.board[i][j] = "X"
                    if self.check_winner():
                        self.board[i][j] = "_"
                        return (i, j)
                    self.board[i][j] = "_"
        
        # Take center if available
        if self.board[1][1] == "_":
            return (1, 1)
        
        # Take corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        available_corners = [corner for corner in corners if self.board[corner[0]][corner[1]] == "_"]
        if available_corners:
            return random.choice(available_corners)
        
        # Take any available spot
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == "_":
                    return (i, j)
        
        return None

class Hangman:
    """Hangman game implementation"""
    
    def __init__(self):
        self.word = random.choice(HANGMAN_WORDS)
        self.guessed_letters = set()
        self.incorrect_guesses = 0
        self.max_incorrect = 6
    
    def display_game(self):
        """Display current hangman game state"""
        display_word = " ".join([letter if letter in self.guessed_letters else "_" for letter in self.word])
        return f"🎮 Hangman\n\nWord: {display_word}\nIncorrect guesses: {self.incorrect_guesses}/{self.max_incorrect}"
    
    def make_guess(self, guess):
        """Process a letter guess"""
        guess = guess.upper()
        
        if guess in self.guessed_letters:
            return self.display_game() + f"\n\nYou already guessed '{guess}'!"
        
        self.guessed_letters.add(guess)
        
        if guess in self.word:
            # Correct guess
            if all(letter in self.guessed_letters for letter in self.word):
                # Won
                return f"🎉 Congratulations! You won!\n\nThe word was: {self.word}"
        else:
            # Incorrect guess
            self.incorrect_guesses += 1
            if self.incorrect_guesses >= self.max_incorrect:
                # Lost
                return f"😢 Game Over!\n\nThe word was: {self.word}\nBetter luck next time!"
        
        # Display current state
        return self.display_game() + f"\n\nGuess a letter:"

def coin_toss(user_choice=None):
    """Head or Tails game"""
    choices = ["Heads", "Tails"]
    result = random.choice(choices)
    
    if user_choice is None:
        return "🎮 Head or Tails\n\nChoose your side:"
    
    if user_choice == result:
        outcome = "You win! 🎉"
    else:
        outcome = "I win! 😎"
    
    return f"🎮 Head or Tails\n\nYou chose: {user_choice}\nResult: {result}\n\n{outcome}"

def rock_paper_scissors(user_choice=None):
    """Rock Paper Scissors game"""
    choices = ["Rock", "Paper", "Scissors"]
    bot_choice = random.choice(choices)
    
    if user_choice is None:
        return "🎮 Rock Paper Scissors\n\nChoose your weapon:"
    
    # Determine winner
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == "Rock" and bot_choice == "Scissors") or \
         (user_choice == "Paper" and bot_choice == "Rock") or \
         (user_choice == "Scissors" and bot_choice == "Paper"):
        result = "You win! 🎉"
    else:
        result = "I win! 😎"
    
    emojis = {"Rock": "✊", "Paper": "✋", "Scissors": "✌️"}
    
    return f"🎮 Rock Paper Scissors\n\nYou: {emojis[user_choice]} {user_choice}\nMe: {emojis[bot_choice]} {bot_choice}\n\n{result}"

def dice_roll():
    """Dice rolling simulator"""
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    dice_emojis = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅"
    }
    
    return f"🎲 Dice Roll\n\n{dice_emojis[dice1]} + {dice_emojis[dice2]} = {total}\n\nRoll again?"