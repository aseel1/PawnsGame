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

    def draw_pieces(self):
        """Draw the pawns on the board."""
        for row in range(8):
            for col in range(8):
                piece = self.chessboard.boardArray[row][col]
                if piece == "wp":
                    pygame.draw.circle(self.surface, (255, 255, 255), 
                        (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 3)
                elif piece == "bp":
                    pygame.draw.circle(self.surface, (0, 0, 0), 
                        (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 3)

    def clientMove(self):
        """Handle user moves."""
        move = None
        flag = 0
        waiting_for_move = True

        while waiting_for_move:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting_for_move = False
                    flag = -1
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
                    #! print(f"Mouse clicked at: {pos}, translated to board position: ({row}, {col})")

                    if self.selected_square:
                        start_row, start_col = self.selected_square
                       #! print(f"Selected square: {self.selected_square}, attempting to move to: ({row}, {col})")
                        if self.chessboard.move_pawn((start_row, start_col), (row, col), self.playerColor ):
                            move = (start_row, start_col, row, col)
                            waiting_for_move = False
                          #!  print(f"Move successful: {move}")
                        else:
                            print("Invalid move")
                        self.selected_square = None
                    elif self.chessboard.boardArray[row][col] in ["wp", "bp"]:
                        self.selected_square = (row, col)
                     #!   print(f"Piece selected at: {self.selected_square}")
            
            self.drawComponent()

        return move, flag












