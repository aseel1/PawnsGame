class ChessBoardChessBoard_Bit:
    def __init__(self):
        self.white_pawns = 0x00FF000000000000  # Corrected to row 6
        self.black_pawns = 0x000000000000FF00  # Corrected to row 1
        self.en_passant_target = None
        self.last_move = None

    def initialize_custom_board(self, setup_message):
        self.white_pawns = 0
        self.black_pawns = 0
        _, *positions = setup_message.split()
        
        for pos in positions:
            color = pos[0]
            col = ord(pos[1]) - ord('a')
            row = 8 - int(pos[2])
            bit = 1 << (row * 8 + col)
            
            if color == 'W':
                self.white_pawns |= bit
            else:
                self.black_pawns |= bit

    def move_pawn(self, start_pos, end_pos, player_color, simulate=False):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        start_bit = 1 << (start_row * 8 + start_col)
        end_bit = 1 << (end_row * 8 + end_col)
        
        # Validate player's pawn exists at start position
        if player_color == 'W' and not (self.white_pawns & start_bit):
            return False
        if player_color == 'B' and not (self.black_pawns & start_bit):
            return False

        # Create temp board for simulation
        temp = ChessBoardChessBoard_Bit()
        temp.white_pawns = self.white_pawns
        temp.black_pawns = self.black_pawns
        temp.en_passant_target = self.en_passant_target

        # Clear start position
        if player_color == 'W':
            temp.white_pawns ^= start_bit
        else:
            temp.black_pawns ^= start_bit

        # Handle captures
        if abs(start_col - end_col) == 1:
            # Regular capture
            if player_color == 'W' and (temp.black_pawns & end_bit):
                temp.black_pawns ^= end_bit
            elif player_color == 'B' and (temp.white_pawns & end_bit):
                temp.white_pawns ^= end_bit
            # En passant capture
            elif self.en_passant_target and end_bit == self.en_passant_target:
                captured_row = start_row  # For en passant, capture is on same row
                captured_bit = 1 << (captured_row * 8 + end_col)
                if player_color == 'W':
                    temp.black_pawns ^= captured_bit
                else:
                    temp.white_pawns ^= captured_bit

        # Set end position
        if player_color == 'W':
            temp.white_pawns |= end_bit
        else:
            temp.black_pawns |= end_bit

        # Update en passant target
        temp.en_passant_target = None
        if abs(start_row - end_row) == 2:
            mid_row = (start_row + end_row) // 2
            temp.en_passant_target = 1 << (mid_row * 8 + start_col)

        if not simulate:
            self.white_pawns = temp.white_pawns
            self.black_pawns = temp.black_pawns
            self.en_passant_target = temp.en_passant_target
            self.last_move = (start_pos, end_pos)

        return True

    def _can_move_forward(self, row, col, direction):
        new_row = row + direction
        if 0 <= new_row < 8:
            pos_mask = 1 << (new_row * 8 + col)
            return not (self.white_pawns | self.black_pawns) & pos_mask
        return False

    def _can_capture(self, row, col, direction, player_color):
        new_row = row + direction
        for dc in [-1, 1]:
            new_col = col + dc
            if 0 <= new_col < 8:
                pos_mask = 1 << (new_row * 8 + new_col)
                if player_color == 'W' and (self.black_pawns & pos_mask):
                    return True
                if player_color == 'B' and (self.white_pawns & pos_mask):
                    return True
        return False

    def _can_en_passant(self, row, col, direction, player_color):
        if not self.en_passant_target:
            return False
            
        target_row = row + direction
        if (player_color == 'W' and row == 3) or (player_color == 'B' and row == 4):
            for dc in [-1, 1]:
                if 0 <= col + dc < 8:
                    ep_mask = 1 << (row * 8 + (col + dc))
                    if self.en_passant_target == (1 << (target_row * 8 + (col + dc))):
                        return True
        return False

    def has_moves(self, player_color):
        pawns = self.white_pawns if player_color == "W" else self.black_pawns
        direction = -1 if player_color == "W" else 1
        all_pawns = self.white_pawns | self.black_pawns

        while pawns:
            lsb = pawns & -pawns
            pos = (lsb.bit_length() - 1)
            pawns ^= lsb
            row, col = divmod(pos, 8)

            # Check single forward move
            forward_pos = pos + direction * 8
            if 0 <= row + direction < 8 and not (all_pawns & (1 << forward_pos)):
                return True

            # Check captures
            for dc in [-1, 1]:
                if 0 <= col + dc < 8:
                    capture_pos = pos + direction * 8 + dc
                    opponent_pawns = self.black_pawns if player_color == "W" else self.white_pawns
                    if opponent_pawns & (1 << capture_pos):
                        return True

            # Check en passant (ADDED: Adjacent opponent pawn check)
            if self.en_passant_target:
                ep_row, ep_col = divmod(self.en_passant_target.bit_length() - 1, 8)
                # Validate alignment and adjacent pawn
                if (player_color == "W" and row == 3 and ep_row == 2 and abs(col - ep_col) == 1) or \
                (player_color == "B" and row == 4 and ep_row == 5 and abs(col - ep_col) == 1):
                    # Check adjacent column for opponent pawn
                    adjacent_col = ep_col
                    adjacent_bit = 1 << (row * 8 + adjacent_col)
                    opponent_pawns = self.black_pawns if player_color == "W" else self.white_pawns
                    if opponent_pawns & adjacent_bit:
                        return True

        return False  # No moves available

    def is_game_over(self, player_color):
        opponent_color = 'B' if player_color == 'W' else 'W'
        
        # Check promotion
        if (self.white_pawns & 0xFF) != 0:
            return 'W'
        if (self.black_pawns & 0xFF00000000000000) != 0:
            return 'B'

        # Check elimination
        if (self.black_pawns == 0 and player_color == 'W') or \
           (self.white_pawns == 0 and player_color == 'B'):
            return player_color

        # Check opponent moves
        if not self.has_moves(opponent_color):
            return player_color

        return None

    def is_game_over_2(self, player_color):
        # Promotion check
        promotion_mask = 0xFF if player_color == "W" else 0xFF00000000000000
        if player_color == "W" and (self.white_pawns & promotion_mask):
            return "W"
        if player_color == "B" and (self.black_pawns & promotion_mask):
            return "B"

        # Elimination check
        if (player_color == "W" and self.white_pawns == 0) or \
        (player_color == "B" and self.black_pawns == 0):
            return "B" if player_color == "W" else "W"

        # Mobility check
        if not self.has_moves(player_color):
            return "B" if player_color == "W" else "W"

        return None

    def print_board(self):
        print("   a b c d e f g h")
        for row in range(8):
            print(f"{row+1} ", end="")
            for col in range(8):
                bit_index = row * 8 + col
                bit_mask = 1 << bit_index
                if self.white_pawns & bit_mask:
                    print("wp", end=" ")
                elif self.black_pawns & bit_mask:
                    print("bp", end=" ")
                else:
                    print("--", end=" ")
            print(f"{row+1}")
        print("   a b c d e f g h")
