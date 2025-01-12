# board.py

class ChessBoard:
    def __init__(self):
        # Initialize the 8x8 board with white and black pawns
        self.boardArray = [
            ["--"] * 8,      # Row 0: Empty
            ["bp"] * 8,      # Row 1: Black pawns
            ["--"] * 8,      # Row 2: Empty
            ["--"] * 8,      # Row 3: Empty
            ["--"] * 8,      # Row 4: Empty
            ["--"] * 8,      # Row 5: Empty
            ["wp"] * 8,      # Row 6: White pawns
            ["--"] * 8       # Row 7: Empty
        ]
        self.enpassant = False
        self.enpassantCol = -1
        self.round = 0

    def move_pawn(self, start_pos, end_pos, player_color):
        """Move a pawn if the move is legal and belongs to the player."""
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        piece = self.boardArray[start_row][start_col]

        # Check if the pawn belongs to the player
        if player_color == "W" and piece != "wp":
            print("Invalid move: You can only move white pawns!")
            return False
        elif player_color == "B" and piece != "bp":
            print("Invalid move: You can only move black pawns!")
            return False

        # White pawn moves
        if piece == "wp":
            if end_row == start_row - 1 and start_col == end_col and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                return True
            if start_row == 6 and end_row == start_row - 2 and start_col == end_col and \
               self.boardArray[start_row - 1][start_col] == "--" and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                return True
            if end_row == start_row - 1 and abs(start_col - end_col) == 1 and \
               self.boardArray[end_row][end_col].startswith("b"):
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                return True

        # Black pawn moves
        elif piece == "bp":
            if end_row == start_row + 1 and start_col == end_col and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                return True
            if start_row == 1 and end_row == start_row + 2 and start_col == end_col and \
               self.boardArray[start_row + 1][start_col] == "--" and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                return True
            if end_row == start_row + 1 and abs(start_col - end_col) == 1 and \
               self.boardArray[end_row][end_col].startswith("w"):
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                return True

        return False

    def print_board(self):
        """Print the board state in the console for debugging."""
        print("\nCurrent Board State:")
        for row in self.boardArray:
            print(" ".join(row))
        print("\n")
