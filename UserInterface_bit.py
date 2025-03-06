# UserInterface.py

import pygame

# Define colors
WHITE = (238, 238, 200)
BLACK = (118, 150, 86)
HIGHLIGHT_COLOR = (0, 255, 0)
SQUARE_SIZE = 75

class UserInterface:
    def __init__(self, surface, chessboard , player_color):
        self.surface = surface
        self.chessboard = chessboard
        self.selected_square = None
        self.playerColor = player_color  # Dynamically assigned
        self.firstgame = True
        self.server_time = 0
        self.client_time = 0

# UserInterface.py Updates

    def draw_timer(self):
        """Display the remaining time for both server and client dynamically in seconds."""
        font = pygame.font.Font(None, 36)
        server_timer_text = font.render(f"Server Time: {int(self.server_time)} sec", True, (0, 0, 0))
        client_timer_text = font.render(f"Client Time: {int(self.client_time)} sec", True, (0, 0, 0))
        
        # Clear timer area
        pygame.draw.rect(self.surface, (255, 255, 255), (0, 0, 600, 40))
        
        # Display timers side by side
        self.surface.blit(server_timer_text, (10, 10))  # Top-left corner
        self.surface.blit(client_timer_text, (300, 10))  # Right of the server time
        
    
    def drawComponent(self):
        """Draw the board and pieces."""
        self.draw_board()
        self.draw_pieces()
        self.draw_timer()
        pygame.display.update()
        
        
    def draw_board(self):
        """Draw the chessboard grid."""
        for row in range(8):
            for col in range(8):
                color = WHITE if (row + col) % 2 == 0 else BLACK
                pygame.draw.rect(self.surface, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
####### UserInterface.py Updates end                
    def draw_pieces(self):
        white_pawns = self.chessboard.white_pawns
        black_pawns = self.chessboard.black_pawns
        
        for pos in range(64):
            row = pos // 8
            col = pos % 8
            if white_pawns & (1 << pos):
                pygame.draw.circle(self.surface, (255, 255, 255),
                    (col * SQUARE_SIZE + SQUARE_SIZE//2, 
                    row * SQUARE_SIZE + SQUARE_SIZE//2), 
                    SQUARE_SIZE//3)
            elif black_pawns & (1 << pos):
                pygame.draw.circle(self.surface, (0, 0, 0),
                    (col * SQUARE_SIZE + SQUARE_SIZE//2,
                    row * SQUARE_SIZE + SQUARE_SIZE//2),
                    SQUARE_SIZE//3)
                
    def clientMove(self):
        """Handle user moves using bitboard checks with validation."""
        move = None
        flag = 0
        waiting_for_move = True
        valid_moves = []  # Store valid moves for selected pawn

        while waiting_for_move:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting_for_move = False
                    flag = -1
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    col = pos[0] // SQUARE_SIZE
                    row = pos[1] // SQUARE_SIZE
                    bit_position = 1 << (row * 8 + col)

                    if self.selected_square:
                        # Check if destination is valid
                        start_pos = (self.selected_square[0], self.selected_square[1])
                        end_pos = (row, col)
                        
                        if end_pos in valid_moves:
                            stored_info = self.chessboard.make_move(start_pos, end_pos, self.playerColor)
                            if stored_info is not None:
                                move = (*start_pos, *end_pos)
                                waiting_for_move = False
                        else:
                            print("Invalid move")
                        self.selected_square = None
                        valid_moves = []
                    else:
                        # Check if clicked square contains player's pawn and get valid moves
                        if (self.playerColor == "W" and (self.chessboard.white_pawns & bit_position)) or \
                        (self.playerColor == "B" and (self.chessboard.black_pawns & bit_position)):
                            self.selected_square = (row, col)
                            # Generate valid moves for selected pawn
                            valid_moves = [
                                (move[1][0], move[1][1])  # Extract destination positions
                                for move in self.chessboard.get_all_moves(self.playerColor)
                                if (move[0][0], move[0][1]) == (row, col)
                            ]

            self.drawComponent()
            if self.selected_square:
                self.draw_highlight(valid_moves)

        return move, flag

    def draw_highlight(self, valid_moves):
        """Highlight valid move destinations."""
        for (row, col) in valid_moves:
            rect = pygame.Rect(
                col * SQUARE_SIZE + 2,
                row * SQUARE_SIZE + 2,
                SQUARE_SIZE - 4,
                SQUARE_SIZE - 4
            )
            pygame.draw.rect(self.surface, HIGHLIGHT_COLOR, rect, 4)
        pygame.display.update()






