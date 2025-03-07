import random
import socket
import pygame
import time
from Board_bit import ChessBoardChessBoard_Bit, zobrist_white, zobrist_black, zobrist_en_passant, zobrist_current_player

CHECKMATE = 100000000000
LOSE =     -100000000000

# Add at the top of your file
# Zobrist Tables

# ---------------------------
# Bitwise Operations
# Maps 1<<i to i (for i in 0..63)
LSB_INDEX_TABLE = {}
for i in range(64):
    LSB_INDEX_TABLE[1 << i] = i

# Maps an index i in [0..63] to (row, col)
PRECOMPUTED_ROW_COL = [(i // 8, i % 8) for i in range(64)]



# ---------------------------
# Transposition Table Setup
# ---------------------------
transposition_table = {}
HASH_EXACT, HASH_ALPHA, HASH_BETA = 0, 1, 2
TRANSPOSITION_TABLE = {}

# ---------------------------
# Transposition Table Setup (Bitboard Version)
# ---------------------------

# ---------------------------
# Evaluation & Utility Functions (Bitboard Version)
# ---------------------------
def evaluate_board(board, player_color):
    """Bitboard version maintaining original evaluation structure"""
    white_score = 0
    black_score = 0

    # Process white pawns using bitboard
    white_pawns = board.white_pawns
    while white_pawns:
        lsb_val = white_pawns & -white_pawns
        pos = LSB_INDEX_TABLE[lsb_val]       # Lookup the index
        row, col = PRECOMPUTED_ROW_COL[pos]  # Then get (row, col)
        pos_tuple = (row, col)

        # Original scoring logic
        white_score += 10 + (6 - row) * 2
        if is_passed_pawn(pos_tuple, board, "W"):
            white_score += 25
        if is_pawn_blocked(pos_tuple, board, "W"):
            white_score -= 5
        if is_hanging_pawn(board, pos_tuple, "W"):
            white_score -= 30
        if is_en_passant_possible(board, pos_tuple, "W"):
            white_score -= 50

        white_pawns ^= lsb_val

    # Process black pawns using bitboard
    black_pawns = board.black_pawns
    while black_pawns:
        lsb_val = black_pawns & -black_pawns
        pos = LSB_INDEX_TABLE[lsb_val]
        row, col = PRECOMPUTED_ROW_COL[pos]
        pos_tuple = (row, col)

        # Original scoring logic
        black_score += 10 + (row - 1) * 2
        if is_passed_pawn(pos_tuple, board, "B"):
            black_score += 25
        if is_pawn_blocked(pos_tuple, board, "B"):
            black_score -= 5
        if is_hanging_pawn(board, pos_tuple, "B"):
            black_score -= 30
        if is_en_passant_possible(board, pos_tuple, "B"):
            black_score -= 50

        black_pawns ^= lsb_val

    return white_score - black_score if player_color == "W" else black_score - white_score

def is_hanging_pawn(board, pos, player_color):
    """Bitboard version of hanging pawn check"""
    row, col = pos
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    direction = 1 if player_color == "W" else -1  # Attack direction
    
    # Calculate attack positions using bitwise operations
    attack_mask = 0
    for dc in [-1, 1]:
        if 0 <= col + dc < 8:
            attack_pos = (row + direction) * 8 + (col + dc)
            attack_mask |= 1 << attack_pos
            
    return bool(opponent_pawns & attack_mask)

def is_passed_pawn(pos, board, player_color):
    """Bitboard version of passed pawn check"""
    row, col = pos
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    
    # Create file masks
    file_mask = 0x0101010101010101 << col
    adjacent_files = (file_mask << 1) | (file_mask >> 1)
    full_mask = file_mask | adjacent_files
    
    # Create ahead mask
    if player_color == "W":
        ahead_mask = ~((1 << ((row + 1) * 8)) - 1)
    else:
        ahead_mask = (1 << (row * 8)) - 1
        
    return not (opponent_pawns & full_mask & ahead_mask)

def is_pawn_blocked(pos, board, player_color):
    """Bitboard version of blocked pawn check"""
    row, col = pos
    direction = -1 if player_color == "W" else 1
    forward_row = row + direction
    
    if 0 <= forward_row < 8:
        forward_bit = 1 << (forward_row * 8 + col)
        return bool((board.white_pawns | board.black_pawns) & forward_bit)
    return False  # Edge of board

def is_en_passant_possible(board, pos, player_color):
    """Bitboard version of en passant check"""
    if not board.en_passant_target:
        return False
    
    row, col = pos
    ep_pos = board.en_passant_target.bit_length() - 1
    ep_row, ep_col = divmod(ep_pos, 8)
    
    # Check position alignment
    if player_color == "W":
        if row != 3 or ep_row != 2 or col != ep_col:
            return False
    else:
        if row != 4 or ep_row != 5 or col != ep_col:
            return False
    
    # Check adjacent pawns using bitboard
    adjacent_mask = (1 << (row * 8 + col - 1)) | (1 << (row * 8 + col + 1))
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    return bool(opponent_pawns & adjacent_mask)

def get_all_moves(board, player_color):
    """Generate all valid pawn moves using bitboard operations with cached lookups."""
    moves = []
    pawns = board.white_pawns if player_color == "W" else board.black_pawns
    opponent_pawns = board.black_pawns if player_color == "W" else board.white_pawns
    direction = -1 if player_color == "W" else 1
    all_pawns = pawns | opponent_pawns

    while pawns:
        lsb_val = pawns & -pawns
        pos = LSB_INDEX_TABLE[lsb_val]      # Cached index lookup
        row, col = PRECOMPUTED_ROW_COL[pos]   # Cached (row, col) lookup
        pawns ^= lsb_val

        # Single push
        if (row + direction) >= 0 and (row + direction) < 8:
            forward = pos + (direction * 8)
            if not (all_pawns & (1 << forward)):
                moves.append(((row, col), (row + direction, col)))

        # Double push from starting rank
        if (player_color == "W" and row == 6) or (player_color == "B" and row == 1):
            double_forward = pos + (2 * direction * 8)
            if not (all_pawns & (1 << double_forward)) and not (all_pawns & (1 << (pos + direction * 8))):
                moves.append(((row, col), (row + 2 * direction, col)))

        # Captures (diagonals)
        for dc in [-1, 1]:
            if 0 <= col + dc < 8:
                capture_pos = pos + direction * 8 + dc
                if opponent_pawns & (1 << capture_pos):
                    moves.append(((row, col), (row + direction, col + dc)))

        # En passant capture
        if board.en_passant_target:
            # There is only one en passant target; its calculation is minor
            ep_pos = board.en_passant_target.bit_length() - 1
            ep_row, ep_col = divmod(ep_pos, 8)
            if (player_color == "W" and row == 3 and ep_row == 2) or \
               (player_color == "B" and row == 4 and ep_row == 5):
                if abs(col - ep_col) == 1:
                    moves.append(((row, col), (ep_row, ep_col)))
    return moves

def apply_move(board, move, player_color):
    """Create new board with updated hash"""
    new_board = board.copy()
    new_board.move_pawn(move[0], move[1], player_color)
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


# PV Search (Minimax-AlphaBeta Clone)
# ---------------------------
def pvs(board, depth, alpha, beta, maximizing_player, root_color):
    global transposition_table
    # --- Transposition Table Lookup ---
    entry = TRANSPOSITION_TABLE.get(board.zobrist_hash)
    if entry and entry["depth"] >= depth:
        if entry["flag"] == HASH_EXACT:
            return entry["score"], entry["best_move"]
        elif entry["flag"] == HASH_ALPHA and entry["score"] <= alpha:
            return alpha, entry["best_move"]
        elif entry["flag"] == HASH_BETA and entry["score"] >= beta:
            return beta, entry["best_move"]

    # Terminal state check
    game_result = board.is_game_over_2(board.current_player)
    if game_result is not None:
        score = CHECKMATE if game_result == root_color else LOSE
        TRANSPOSITION_TABLE[board.zobrist_hash] = {
            "depth": depth,
            "score": score,
            "flag": HASH_EXACT,
            "best_move": None
        }
        return score, None

    if depth == 0:
        score = evaluate_board(board, root_color)
        TRANSPOSITION_TABLE[board.zobrist_hash] = {
            "depth": 0,
            "score": score,
            "flag": HASH_EXACT,
            "best_move": None
        }
        return score, None

    moves = get_all_moves(board, board.current_player)
    moves = order_moves(board, moves, board.current_player)
    original_alpha = alpha
    best_move = moves[0] if moves else None  # Critical fix!

    if maximizing_player:
        max_eval = -CHECKMATE
        best_move = None  # Initialize best_move here
        for move in moves:
            new_board = apply_move(board, move, board.current_player)
            eval_score, _ = pvs(new_board, depth-1, alpha, beta, False, root_color)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
                if max_eval >= beta:
                    break  # Beta cutoff
                    
            alpha = max(alpha, max_eval)
            if alpha >= beta:
                break

        # Store in transposition table
        flag = HASH_EXACT
        if max_eval <= original_alpha:
            flag = HASH_ALPHA
        elif max_eval >= beta:
            flag = HASH_BETA
            
        TRANSPOSITION_TABLE[board.zobrist_hash] = {
            "depth": depth,
            "score": max_eval,
            "flag": flag,
            "best_move": best_move
        }
        return max_eval, best_move
        
    else:  # Minimizing player
        min_eval = CHECKMATE
        best_move = None  # Initialize best_move here
        for move in moves:
            new_board = apply_move(board, move, board.current_player)
            eval_score, _ = pvs(new_board, depth-1, alpha, beta, True, root_color)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                if min_eval <= alpha:
                    break  # Alpha cutoff
                    
            beta = min(beta, min_eval)
            if beta <= alpha:
                break

        # Store in transposition table
        flag = HASH_EXACT
        if min_eval <= original_alpha:
            flag = HASH_ALPHA
        elif min_eval >= beta:
            flag = HASH_BETA
            
        TRANSPOSITION_TABLE[board.zobrist_hash] = {
            "depth": depth,
            "score": min_eval,
            "flag": flag,
            "best_move": best_move
        }
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
        if eval_score >= CHECKMATE - 1000 or eval_score <= LOSE + 1000:
                print(f"🏆 Checkmate move found at depth {depth}! Stopping search early.")
                break

    if best_move is None:
        print("No moves found. Randomly selecting fallback move.")
        fallback_moves = get_all_moves(board, player_color)
        if fallback_moves:
            best_move = random.choice(fallback_moves)
    
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
