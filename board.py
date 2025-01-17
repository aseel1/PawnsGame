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

    def move_pawn(self, start_pos, end_pos, player_color, simulate=False):
        """Move a pawn if the move is legal, including diagonal captures and en passant."""
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        piece = self.boardArray[start_row][start_col]
        opponent_pawn = "bp" if player_color == "W" else "wp"

        # Check if the pawn belongs to the player
        if player_color == "W" and piece != "wp":
            return False
        elif player_color == "B" and piece != "bp":
            return False

        # Flag to check if a capture occurred
        captured = False

        # White pawn moves
        if piece == "wp":
            # Move forward by 1
            if end_row == start_row - 1 and start_col == end_col and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                self.enpassant = False  # Reset en passant
                return True

            # Move forward by 2 from starting position
            if start_row == 6 and end_row == start_row - 2 and start_col == end_col and \
            self.boardArray[start_row - 1][start_col] == "--" and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                self.enpassant = True
                self.enpassantCol = start_col  # Track the column for en passant
                return True

            # ✅ Regular Diagonal Capture
            if end_row == start_row - 1 and abs(start_col - end_col) == 1 and self.boardArray[end_row][end_col].startswith("b"):
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                captured = True

            # ✅ En Passant Capture (Corrected)
            if self.enpassant and start_row == 3 and end_row == 2 and abs(start_col - end_col) == 1 and end_col == self.enpassantCol:
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                self.boardArray[start_row][end_col] = "--"  # Remove the captured pawn
                captured = True
                self.enpassant = False  # Reset en passant

        # Black pawn moves
        elif piece == "bp":
            # Move forward by 1
            if end_row == start_row + 1 and start_col == end_col and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                self.enpassant = False  # Reset en passant
                return True

            # Move forward by 2 from starting position
            if start_row == 1 and end_row == start_row + 2 and start_col == end_col and \
            self.boardArray[start_row + 1][start_col] == "--" and self.boardArray[end_row][end_col] == "--":
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                self.enpassant = True
                self.enpassantCol = start_col
                return True

            # ✅ Regular Diagonal Capture
            if end_row == start_row + 1 and abs(start_col - end_col) == 1 and self.boardArray[end_row][end_col].startswith("w"):
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                captured = True

            # ✅ En Passant Capture (Corrected)
            if self.enpassant and start_row == 4 and end_row == 5 and abs(start_col - end_col) == 1 and end_col == self.enpassantCol:
                self.boardArray[end_row][end_col] = piece
                self.boardArray[start_row][start_col] = "--"
                self.boardArray[start_row][end_col] = "--"  # Remove the captured pawn
                captured = True
                self.enpassant = False  # Reset en passant

        # 🔔 Print capture only once
        if captured and not simulate:
            print(f"{'White' if player_color == 'W' else 'Black'} pawn captured a piece!")
            return True

        return False


    def is_game_over(self, player_color):
        """Check if the game should end."""
        opponent_color = "B" if player_color == "W" else "W"

        # 1. Check if any pawn reached the opponent's back rank
        if "wp" in self.boardArray[0]:
            print("White wins by reaching the end!")
            return "W"
        if "bp" in self.boardArray[7]:
            print("Black wins by reaching the end!")
            return "B"

        # 2. Check if all opponent pawns are captured
        opponent_pawn = "wp" if opponent_color == "W" else "bp"
        if not any(opponent_pawn in row for row in self.boardArray):
            print(f"{player_color} wins by capturing all pawns!")
            return player_color

        # 3. Check if opponent has any legal moves
        if not self.has_moves(opponent_color):
            print(f"{player_color} wins by blocking all moves!")
            return player_color

        return None  # Game continues

    def has_moves(self, player_color):
        """Check if the player has any valid moves."""
        direction = -1 if player_color == "W" else 1
        pawn = "wp" if player_color == "W" else "bp"

        for row in range(8):
            for col in range(8):
                if self.boardArray[row][col] == pawn:
                    # Forward move
                    if 0 <= row + direction < 8 and self.boardArray[row + direction][col] == "--":
                        return True
                    # Diagonal captures
                    for dc in [-1, 1]:
                        if 0 <= col + dc < 8:
                            target = self.boardArray[row + direction][col + dc]
                            if (player_color == "W" and target == "bp") or (player_color == "B" and target == "wp"):
                                return True
        return False  # No valid moves
    

