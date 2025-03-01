import random
import socket
import pygame
import time
from Board_bit import ChessBoardChessBoard_Bit

CHECKMATE = 100000000000
LOSE =     -100000000000

# ---------------------------
# Transposition Table Setup
# ---------------------------
transposition_table = {}

# ---------------------------
# Transposition Table Setup (Bitboard Version)
# ---------------------------
def board_hash(board):
    """Create hash for bitboard-based chess board"""
    return (
        board.white_pawns, 
        board.black_pawns,
        board.en_passant_target,
        board.last_move
    )

# ---------------------------
# Evaluation & Utility Functions (Bitboard Version)
# ---------------------------
def evaluate_board(board, player_color):
    """Evaluate board state using bitboard features"""
    white_score = 0
    black_score = 0
    
    # Material count (base value)
    white_material = bin(board.white_pawns).count('1') * 100
    black_material = bin(board.black_pawns).count('1') * 100
    white_score += white_material
    black_score += black_material

    # Process white pawn features
    white_pawns = board.white_pawns
    while white_pawns:
        lsb = white_pawns & -white_pawns
        pos = lsb.bit_length() - 1
        row, col = divmod(pos, 8)
        
        # Only process valid positions
        if not (0 <= row < 8 and 0 <= col < 8):
            white_pawns ^= lsb
            continue

        # Advancement bonus (closer to promotion)
        white_score += (7 - row) * 2  # Max 12 points for 7th rank
        
        # Blocked penalty (fixed syntax)
        if row > 0:  # Prevent checking row -1
            forward_pos = pos - 8
            if 0 <= forward_pos < 64:
                # Corrected bitwise operation with proper parentheses
                if (1 << forward_pos) & (board.white_pawns | board.black_pawns):
                    white_score -= 30
        
        # Passed pawn check
        file_mask = 0x0101010101010101 << col
        ahead_mask = ~((1 << (pos + 8)) - 1)
        if not (board.black_pawns & file_mask & ahead_mask):
            white_score += 50
            
        # Hanging pawn check
        hanging = False
        for dc in [-1, 1]:
            attack_col = col + dc
            if 0 <= attack_col < 8:
                attack_pos = pos - 8 + dc
                if 0 <= attack_pos < 64:
                    if board.black_pawns & (1 << attack_pos):
                        white_score -= 50
                        hanging = True
                        break
            
        # En passant vulnerability
        if not hanging and board.en_passant_target:
            ep_pos = board.en_passant_target.bit_length() - 1
            if row == 3 and abs(col - (ep_pos % 8)) == 1:
                white_score -= 30

        white_pawns ^= lsb

    # Process black pawn features (similar fixes applied)
    black_pawns = board.black_pawns
    while black_pawns:
        lsb = black_pawns & -black_pawns
        pos = lsb.bit_length() - 1
        row, col = divmod(pos, 8)
        
        if not (0 <= row < 8 and 0 <= col < 8):
            black_pawns ^= lsb
            continue

        black_score += row * 2
        
        if row < 7:
            forward_pos = pos + 8
            if 0 <= forward_pos < 64:
                if (1 << forward_pos) & (board.white_pawns | board.black_pawns):
                    black_score -= 30
        
        file_mask = 0x0101010101010101 << col
        ahead_mask = (1 << pos) - 1
        if not (board.white_pawns & file_mask & ahead_mask):
            black_score += 50
            
        hanging = False
        for dc in [-1, 1]:
            attack_col = col + dc
            if 0 <= attack_col < 8:
                attack_pos = pos + 8 + dc
                if 0 <= attack_pos < 64:
                    if board.white_pawns & (1 << attack_pos):
                        black_score -= 50
                        hanging = True
                        break
            
        if not hanging and board.en_passant_target:
            ep_pos = board.en_passant_target.bit_length() - 1
            if row == 4 and abs(col - (ep_pos % 8)) == 1:
                black_score -= 30

        black_pawns ^= lsb

    final_score = white_score - black_score
    return final_score if player_color == "W" else -final_score


def passed_pawns_score(pawns, opponent_pawns, color):
    """Calculate passed pawns score using bitwise operations"""
    score = 0
    mask = pawns
    while mask:
        lsb = mask & -mask
        pos = lsb.bit_length() - 1
        col = pos % 8
        row = pos // 8
        
        # Check if pawn is passed
        file_mask = 0x0101010101010101 << col
        ahead_mask = (0xFFFFFFFFFFFFFFFF << (pos + 8)) if color == "W" else (0xFFFFFFFFFFFFFFFF >> (64 - pos))
        if not (opponent_pawns & file_mask & ahead_mask):
            score += 50
            
        mask ^= lsb
    return score

# Remove or update these legacy functions that use boardArray
def is_hanging_pawn(board, pos, player_color):
    """Check if a pawn is unprotected using bitboards"""
    row, col = pos
    pos_bit = 1 << (row * 8 + col)
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    direction = 1 if player_color == "W" else -1
    
    # Check diagonal attacks
    for dc in [-1, 1]:
        attack_row = row + direction
        attack_col = col + dc
        if 0 <= attack_col < 8:
            attack_bit = 1 << (attack_row * 8 + attack_col)
            if opponent_pawns & attack_bit:
                return True
    return False

def is_passed_pawn(pos, board, player_color):
    """Check passed pawn using bitboard operations"""
    row, col = pos
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    file_mask = 0x0101010101010101 << col
    ahead_mask = ~((1 << (row * 8)) - 1) if player_color == "W" else ((1 << (row * 8)) - 1)
    return not (opponent_pawns & file_mask & ahead_mask)

def is_pawn_blocked(pos, board, player_color):
    """Check blocked pawn using bitboards"""
    row, col = pos
    direction = -1 if player_color == "W" else 1
    forward_bit = 1 << ((row + direction) * 8 + col)
    all_pawns = board.white_pawns | board.black_pawns
    return bool(all_pawns & forward_bit)

def is_en_passant_possible(board, pos, player_color):
    """Check en passant using bitboard data"""
    if not board.en_passant_target:
        return False
    
    row, col = pos
    ep_pos = board.en_passant_target.bit_length() - 1
    ep_row, ep_col = divmod(ep_pos, 8)
    
    if player_color == "W":
        return row == 3 and ep_row == 2 and abs(col - ep_col) == 1
    else:
        return row == 4 and ep_row == 5 and abs(col - ep_col) == 1


def get_all_moves(board, player_color):
    """Generate all valid pawn moves using bitboard operations"""
    moves = []
    pawns = board.white_pawns if player_color == "W" else board.black_pawns
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    direction = -1 if player_color == "W" else 1
    all_pawns = pawns | opponent_pawns

    # Iterate through all pawns using bitwise operations
    while pawns:
        lsb = pawns & -pawns
        pos = lsb.bit_length() - 1
        pawns ^= lsb
        row, col = divmod(pos, 8)

        # Single push
        if (row + direction) >= 0 and (row + direction) < 8:
            forward = pos + (direction * 8)
            if not (all_pawns & (1 << forward)):
                moves.append(((row, col), (row + direction, col)))

        # Double push
        if (player_color == "W" and row == 6) or (player_color == "B" and row == 1):
            double_forward = pos + (2 * direction * 8)
            if not (all_pawns & (1 << double_forward)) and not (all_pawns & (1 << (pos + direction * 8))):
                moves.append(((row, col), (row + 2 * direction, col)))

        # Captures
        for dc in [-1, 1]:
            if 0 <= col + dc < 8:
                capture_pos = pos + direction * 8 + dc
                if opponent_pawns & (1 << capture_pos):
                    moves.append(((row, col), (row + direction, col + dc)))

        # En passant
        if board.en_passant_target:
            ep_pos = board.en_passant_target.bit_length() - 1
            ep_row, ep_col = divmod(ep_pos, 8)
            if (player_color == "W" and row == 3 and ep_row == 2) or \
               (player_color == "B" and row == 4 and ep_row == 5):
                if abs(col - ep_col) == 1:
                    moves.append(((row, col), (ep_row, ep_col)))

    return moves
def apply_move(board, move, player_color):
    new_board = ChessBoardChessBoard_Bit()
    new_board.white_pawns = board.white_pawns
    new_board.black_pawns = board.black_pawns
    start, end = move
    new_board.move_pawn(start, end, player_color)
    return new_board

def move_to_notation(move):
    start, end = move
    return f"{chr(97 + start[1])}{8 - start[0]}{chr(97 + end[1])}{8 - end[0]}"

def order_moves(board, moves, player_color):
    """Sort moves based on bitboard heuristics"""
    def move_score(move):
        _, end = move
        end_row, end_col = end
        score = 0
        
        # Promotion check (only valid if move is to promotion rank)
        if (player_color == "W" and end_row == 0) or (player_color == "B" and end_row == 7):
            score += 10000
        
        # Capture check using bitboards (valid coordinates only)
        if 0 <= end_row < 8 and 0 <= end_col < 8:
            end_bit = 1 << (end_row * 8 + end_col)
            if (player_color == "W" and (board.black_pawns & end_bit)) or \
               (player_color == "B" and (board.white_pawns & end_bit)):
                score += 500
        
        # Advancement bonus with valid row check
        if 0 <= end_row < 8:
            score += (7 - end_row) if player_color == "W" else end_row
        
        # Pawn tension bonus with strict bounds checking
        if player_color == "W" and end_row > 0:  # Prevent row -1
            above_row = end_row - 1
            if 0 <= above_row < 8:
                above_bit = 1 << (above_row * 8 + end_col)
                if board.black_pawns & above_bit:
                    score += 200
        elif player_color == "B" and end_row < 7:  # Prevent row 8
            below_row = end_row + 1
            if 0 <= below_row < 8:
                below_bit = 1 << (below_row * 8 + end_col)
                if board.white_pawns & below_bit:
                    score += 200
                
        return -score  # Negative for descending sort
    
    return sorted(moves, key=move_score)
# ---------------------------
# PV Search with Aspiration and Transposition Table
# ---------------------------
# ---------------------------
# PV Search with Transposition Table
# ---------------------------
# ---------------------------
# PV Search with Transposition Table (Minimax-Compatible Version)
# ---------------------------
# ---------------------------
# PV Search (Minimax-AlphaBeta Clone)
# ---------------------------
def pvs(board, depth, alpha, beta, maximizing_player, root_color):
    global transposition_table
    key = (board_hash(board), depth, maximizing_player)
    if key in transposition_table:
        return transposition_table[key]

    current_color = root_color if maximizing_player else ("B" if root_color == "W" else "W")
    
    # Terminal state check (identical to Minimax)
    game_result = board.is_game_over_2(current_color)
    if game_result is not None:
        if game_result == root_color:
            value = CHECKMATE
        else:
            value = LOSE
        transposition_table[key] = (value, None)
        return value, None

    if depth == 0:
        value = evaluate_board(board, root_color)
        transposition_table[key] = (value, None)
        return value, None

    best_move = None
    moves = get_all_moves(board, current_color)
    moves = order_moves(board, moves, current_color)

    if maximizing_player:
        max_eval = -CHECKMATE
        for move in moves:
            new_board = apply_move(board, move, current_color)
            eval_score, _ = pvs(new_board, depth-1, alpha, beta, False, root_color)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
                if max_eval >= CHECKMATE - 1:  # Exact mate detection
                    break
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        transposition_table[key] = (max_eval, best_move)
        return max_eval, best_move
    else:
        min_eval = CHECKMATE
        for move in moves:
            new_board = apply_move(board, move, current_color)
            eval_score, _ = pvs(new_board, depth-1, alpha, beta, True, root_color)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                if min_eval <= LOSE + 1:  # Exact mate detection
                    break
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        transposition_table[key] = (min_eval, best_move)
        return min_eval, best_move

def iterative_deepening_pvs(board, max_depth, player_color, time_limit=100):
    global transposition_table
    transposition_table.clear()
    start_time = time.time()
    best_move = None
    
    for depth in range(1, max_depth + 1):
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break
            
        # Identical parameters to Minimax
        eval_score, move = pvs(board, depth, -CHECKMATE, CHECKMATE, True, player_color)
        
        if move:
            best_move = move
            print(f"Depth {depth} Best Move: {move_to_notation(move)} | Eval: {eval_score}")
            
            # Exact Minimax stopping condition
            if eval_score >= CHECKMATE - 1 or eval_score <= LOSE + 1:
                print(f"🏆 Checkmate detected at depth {depth}")
                break

    # Fallback identical to Minimax
    if best_move is None:
        moves = get_all_moves(board, player_color)
        if moves:
            best_move = moves[0]
    
    print("Search completed!")
    return best_move

# ---------------------------
# Main Game Loop
# ---------------------------
def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9999))
    running = True
    game_active = False  # Game starts after "Begin"
    clock = pygame.time.Clock()
    board = ChessBoardChessBoard_Bit()  # Initialize board from board.py

    while running:
        data = client_socket.recv(1024).decode()
        if data == "Connected to the server!":
            client_socket.send("OK".encode())
        elif data.startswith("Color"):
            player_color = data.split()[1]
            print(f"My color is: {player_color}")
            client_socket.send("OK".encode())
        elif data.startswith("Setup"):
            print(f"Setting up the board: {data}")
            board.initialize_custom_board(data)
            client_socket.send("OK".encode())
        elif data.isdigit():
            print(f"Game time set to {data} minutes.")
            client_socket.send("OK".encode())
        elif data == "Begin":
            print("Game is starting!")
            game_active = True
        elif data == "Your turn" and game_active:
            print("--------------------------------")
            print("Agent is thinking...")
            move = iterative_deepening_pvs(board, max_depth=10, player_color=player_color, time_limit=1000)
            move_notation = move_to_notation(move)
            print(f"Agent move ({player_color}): {move_notation}")
            client_socket.send(move_notation.encode())
            board.move_pawn(move[0], move[1], player_color)
        elif data.startswith("TimeRemaining"):
            client_time_remaining = float(data.split()[1])
            print(f"Client time remaining: {client_time_remaining:.2f} seconds")
        elif data == "exit":
            print("Game over. Disconnecting.")
            break
        elif len(data) == 4:  # e.g., "e2e4"
            print(f"Opponent moved: {data}")
            start_col, start_row = ord(data[0]) - 97, 8 - int(data[1])
            end_col, end_row = ord(data[2]) - 97, 8 - int(data[3])
            opponent_color = "B" if player_color == "W" else "W"
            board.move_pawn((start_row, start_col), (end_row, end_col), opponent_color)

    client_socket.close()
    pygame.quit()

if __name__ == "__main__":
    main()
