import pygame
import numpy as np

class PawnGame:
    def __init__(self, board_size=8):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=int)
        self.init_board()

    def init_board(self):
        """Initialize the board with pawns."""
        self.board[1, :] = 1  # Player 1 pawns
        self.board[self.board_size - 2, :] = -1  # Player 2 pawns

    def is_terminal(self):
        """Check if the game has reached a terminal state."""
        if 1 in self.board[-1, :] or -1 in self.board[0, :]:
            return True  # A player has reached the opposite side.
        if not np.any(self.board == 1) or not np.any(self.board == -1):
            return True  # A player has no pawns left.
        return False

    def evaluate(self):
        """Evaluate the board from Player 1's perspective."""
        return np.sum(self.board)

    def get_valid_moves(self, player):
        """Generate all valid moves for the current player."""
        moves = []
        direction = 1 if player == 1 else -1
        for x in range(self.board_size):
            for y in range(self.board_size):
                if self.board[x, y] == player:
                    # Forward move
                    if 0 <= x + direction < self.board_size and self.board[x + direction, y] == 0:
                        moves.append(((x, y), (x + direction, y)))
                    # Capture moves
                    for dy in [-1, 1]:
                        if 0 <= x + direction < self.board_size and 0 <= y + dy < self.board_size:
                            if self.board[x + direction, y + dy] == -player:
                                moves.append(((x, y), (x + direction, y + dy)))
        return moves

    def make_move(self, move):
        """Apply a move to the board."""
        start, end = move
        self.board[end] = self.board[start]
        self.board[start] = 0

# Pygame Visualization
class PawnGameGUI:
    def __init__(self, game):
        self.game = game
        self.cell_size = 80
        self.width = self.cell_size * game.board_size
        self.height = self.cell_size * game.board_size
        self.colors = [(238, 238, 210), (118, 150, 86)]  # Chessboard colors
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pawn Game")
        self.font = pygame.font.SysFont(None, 50)

    def draw_board(self):
        for x in range(self.game.board_size):
            for y in range(self.game.board_size):
                color = self.colors[(x + y) % 2]
                pygame.draw.rect(self.screen, color, (y * self.cell_size, x * self.cell_size, self.cell_size, self.cell_size))

                # Draw pawns
                piece = self.game.board[x, y]
                if piece == 1:  # Player 1
                    pygame.draw.circle(self.screen, (255, 255, 255), (y * self.cell_size + self.cell_size // 2, x * self.cell_size + self.cell_size // 2), self.cell_size // 3)
                elif piece == -1:  # Player 2
                    pygame.draw.circle(self.screen, (0, 0, 0), (y * self.cell_size + self.cell_size // 2, x * self.cell_size + self.cell_size // 2), self.cell_size // 3)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.fill((0, 0, 0))
            self.draw_board()
            pygame.display.flip()

        pygame.quit()

# Run the game with GUI
game = PawnGame()
gui = PawnGameGUI(game)
gui.run()
