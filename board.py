# board.py

class ChessBoard:
    def __init__(self):
        # Initialize the 8x8 board with only pawns
        self.boardArray = [
            ["--"] * 8,  # Black pawns
            ["bp"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["wp"] * 8,  # White pawns
            ["--"] * 8
        ]
        self.enpassant = False
        self.enpassantCol = -1
        self.round = 0

    def move_pawn(self, start_pos, end_pos):
        """Move a pawn if the move is legal."""
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        piece = self.boardArray[start_row][start_col]

        # Ensure there's a pawn to move
        if piece == "--":
            return False

        # Basic forward move validation for pawns
        if piece == "wp" and end_row == start_row - 1 and start_col == end_col:
            self.boardArray[end_row][end_col] = piece
            self.boardArray[start_row][start_col] = "--"
            return True

        if piece == "bp" and end_row == start_row + 1 and start_col == end_col:
            self.boardArray[end_row][end_col] = piece
            self.boardArray[start_row][start_col] = "--"
            return True

        return False

    def print_board(self):
        """Print the board state in the console."""
        for row in self.boardArray:
            print(" ".join(row))
        print("\n")
