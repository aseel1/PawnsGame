import random
import socket
import pygame
import time
from Board_bit import ChessBoardChessBoard_Bit, zobrist_white, zobrist_black, zobrist_en_passant, zobrist_current_player

CHECKMATE = 100000000000
LOSE = -100000000000

# Bitwise operations for move generation
LSB_INDEX_TABLE = {}
for i in range(64):
    LSB_INDEX_TABLE[1 << i] = i
PRECOMPUTED_ROW_COL = [(i // 8, i % 8) for i in range(64)]

# Precompute capture masks (only used if you decide to use them)
WHITE_CAPTURES = [ (((1 << (i + 7)) if (i + 7) < 64 else 0) | ((1 << (i + 9)) if (i + 9) < 64 else 0)) for i in range(64) ]
BLACK_CAPTURES = [ (((1 << (i - 7)) if (i - 7) >= 0 else 0) | ((1 << (i - 9)) if (i - 9) >= 0 else 0)) for i in range(64) ]

# Transposition table setup
HASH_EXACT, HASH_ALPHA, HASH_BETA = 0, 1, 2
TRANSPOSITION_TABLE = {}

# ---------------------------
# Evaluation & Utility Functions
def evaluate_board(board, player_color):
    white_score = 0
    black_score = 0

    # Evaluate white pawns
    white_pawns = board.white_pawns
    while white_pawns:
        lsb_val = white_pawns & -white_pawns
        pos = LSB_INDEX_TABLE[lsb_val]
        row, col = PRECOMPUTED_ROW_COL[pos]
        white_score += 10 + (6 - row) * 2

        # Passed pawn (White)
        opponent_pawns = board.black_pawns
        file_mask = 0x0101010101010101 << col
        adjacent_files = (file_mask << 1) | (file_mask >> 1)
        full_mask = file_mask | adjacent_files
        ahead_mask = ~((1 << ((row + 1) * 8)) - 1)
        if not (opponent_pawns & full_mask & ahead_mask):
            white_score += 25

        # Blocked pawn (White)
        direction = -1
        forward_row = row + direction
        if 0 <= forward_row < 8:
            forward_bit = 1 << (forward_row * 8 + col)
            if (board.white_pawns | board.black_pawns) & forward_bit:
                white_score -= 15

        # Hanging pawn (White)
        # White pawns attack upward: ensure row+direction is in bounds.
        direction = -1  
        attack_mask = 0
        if col - 1 >= 0 and 0 <= row + direction < 8:
            attack_mask |= 1 << ((row + direction) * 8 + (col - 1))
        if col + 1 < 8 and 0 <= row + direction < 8:
            attack_mask |= 1 << ((row + direction) * 8 + (col + 1))
        if board.black_pawns & attack_mask:
            white_score -= 50

        # En passant vulnerability (White)
        if board.en_passant_target:
            ep_pos = board.en_passant_target.bit_length() - 1
            ep_row, ep_col = divmod(ep_pos, 8)
            if row == 3 and ep_row == 2 and col == ep_col:
                adjacent_mask = 0
                if col - 1 >= 0:
                    adjacent_mask |= 1 << (row * 8 + col - 1)
                if col + 1 < 8:
                    adjacent_mask |= 1 << (row * 8 + col + 1)
                if board.black_pawns & adjacent_mask:
                    white_score -= 50

        white_pawns ^= lsb_val

    # Evaluate black pawns
    black_pawns = board.black_pawns
    while black_pawns:
        lsb_val = black_pawns & -black_pawns
        pos = LSB_INDEX_TABLE[lsb_val]
        row, col = PRECOMPUTED_ROW_COL[pos]
        black_score += 10 + (row - 1) * 2

        # Passed pawn (Black)
        opponent_pawns = board.white_pawns
        file_mask = 0x0101010101010101 << col
        adjacent_files = (file_mask << 1) | (file_mask >> 1)
        full_mask = file_mask | adjacent_files
        ahead_mask = (1 << (row * 8)) - 1
        if not (opponent_pawns & full_mask & ahead_mask):
            black_score += 25

        # Blocked pawn (Black)
        direction = 1
        forward_row = row + direction
        if 0 <= forward_row < 8:
            forward_bit = 1 << (forward_row * 8 + col)
            if (board.white_pawns | board.black_pawns) & forward_bit:
                black_score -= 15

        # Hanging pawn (Black)
        direction = 1  
        attack_mask = 0
        if col - 1 >= 0 and 0 <= row + direction < 8:
            attack_mask |= 1 << ((row + direction) * 8 + (col - 1))
        if col + 1 < 8 and 0 <= row + direction < 8:
            attack_mask |= 1 << ((row + direction) * 8 + (col + 1))
        if board.white_pawns & attack_mask:
            black_score -= 50

        # En passant vulnerability (Black)
        if board.en_passant_target:
            ep_pos = board.en_passant_target.bit_length() - 1
            ep_row, ep_col = divmod(ep_pos, 8)
            if row == 4 and ep_row == 5 and col == ep_col:
                adjacent_mask = 0
                if col - 1 >= 0:
                    adjacent_mask |= 1 << (row * 8 + col - 1)
                if col + 1 < 8:
                    adjacent_mask |= 1 << (row * 8 + col + 1)
                if board.white_pawns & adjacent_mask:
                    black_score -= 50

        black_pawns ^= lsb_val

    return white_score - black_score if player_color == "W" else black_score - white_score

# ---------------------------
# Move Generation
def get_all_moves(board, player_color):
    moves = []
    if player_color == "W":
        pawns = board.white_pawns
        opponent_pawns = board.black_pawns
        direction = -1
    else:
        pawns = board.black_pawns
        opponent_pawns = board.white_pawns
        direction = 1
    all_pawns = board.white_pawns | board.black_pawns

    while pawns:
        lsb_val = pawns & -pawns
        pos = LSB_INDEX_TABLE[lsb_val]
        row, col = PRECOMPUTED_ROW_COL[pos]
        pawns ^= lsb_val

        # Single push
        if 0 <= row + direction < 8:
            forward = pos + (direction * 8)
            if not (all_pawns & (1 << forward)):
                moves.append(((row, col), (row + direction, col)))
        # Double push from starting rank
        if (player_color == "W" and row == 6) or (player_color == "B" and row == 1):
            if 0 <= row + direction < 8 and 0 <= row + 2 * direction < 8:
                double_forward = pos + (2 * direction * 8)
                if not (all_pawns & (1 << double_forward)) and not (all_pawns & (1 << (pos + direction * 8))):
                    moves.append(((row, col), (row + 2 * direction, col)))
        # Captures
        for dc in [-1, 1]:
            if 0 <= col + dc < 8 and 0 <= row + direction < 8:
                capture_pos = pos + direction * 8 + dc
                if capture_pos < 0 or capture_pos >= 64:
                    continue
                if opponent_pawns & (1 << capture_pos):
                    moves.append(((row, col), (row + direction, col + dc)))
        # En passant capture
        if board.en_passant_target:
            ep_pos = board.en_passant_target.bit_length() - 1
            ep_row, ep_col = divmod(ep_pos, 8)
            if (player_color == "W" and row == 3 and ep_row == 2) or (player_color == "B" and row == 4 and ep_row == 5):
                if abs(col - ep_col) == 1:
                    moves.append(((row, col), (ep_row, ep_col)))
    return moves

def move_to_notation(move):
    start, end = move
    return f"{chr(97 + start[1])}{8 - start[0]}{chr(97 + end[1])}{8 - end[0]}"

def order_moves(board, moves, player_color):
    def move_score(move):
        _, end = move
        end_row, end_col = end
        score = 0
        if (player_color == "W" and end_row == 0) or (player_color == "B" and end_row == 7):
            score += 10000
        if 0 <= end_row < 8 and 0 <= end_col < 8:
            end_bit = 1 << (end_row * 8 + end_col)
            if (player_color == "W" and (board.black_pawns & end_bit)) or (player_color == "B" and (board.white_pawns & end_bit)):
                score += 500
        if 0 <= end_row < 8:
            score += (7 - end_row) if player_color == "W" else end_row
        if player_color == "W" and end_row > 0:
            above_row = end_row - 1
            if 0 <= above_row < 8:
                above_bit = 1 << (above_row * 8 + end_col)
                if board.black_pawns & above_bit:
                    score += 200
        elif player_color == "B" and end_row < 7:
            below_row = end_row + 1
            if 0 <= below_row < 8:
                below_bit = 1 << (below_row * 8 + end_col)
                if board.white_pawns & below_bit:
                    score += 200
        return -score
    return sorted(moves, key=move_score)

def get_captures(board, player_color):
    """Generate captures including correct en passant"""
    captures = []
    if player_color == "W":
        pawns = board.white_pawns
        opponent = board.black_pawns
        # Regular captures
        cap_masks = ((pawns << 7) & 0xFEFEFEFEFEFEFEFE, (pawns << 9) & 0x7F7F7F7F7F7F7F7F)
    else:
        pawns = board.black_pawns
        opponent = board.white_pawns
        cap_masks = ((pawns >> 7) & 0x7F7F7F7F7F7F7F7F, (pawns >> 9) & 0xFEFEFEFEFEFEFEFE)
    
    for cap_mask in cap_masks:
        valid_caps = cap_mask & opponent
        while valid_caps:
            to_idx = (valid_caps & -valid_caps).bit_length() - 1
            from_idx = to_idx - (7 if player_color == "W" else 9) if cap_mask == cap_masks[0] else to_idx - (9 if player_color == "W" else 7)
            if 0 <= from_idx < 64:
                captures.append((
                    (from_idx // 8, from_idx % 8),
                    (to_idx // 8, to_idx % 8)
                ))
            valid_caps &= valid_caps - 1
    
    # En passant captures
    if board.en_passant_target:
        ep_pos = (board.en_passant_target).bit_length() - 1
        ep_row, ep_col = ep_pos // 8, ep_pos % 8
        if player_color == "W" and ep_row == 2:  # White en passant
            from_row = 3
            for dc in (-1, 1):
                from_col = ep_col + dc
                if 0 <= from_col < 8:
                    from_idx = from_row * 8 + from_col
                    if pawns & (1 << from_idx):
                        captures.append(((from_row, from_col), (ep_row, ep_col)))
        elif player_color == "B" and ep_row == 5:  # Black en passant
            from_row = 4
            for dc in (-1, 1):
                from_col = ep_col + dc
                if 0 <= from_col < 8:
                    from_idx = from_row * 8 + from_col
                    if pawns & (1 << from_idx):
                        captures.append(((from_row, from_col), (ep_row, ep_col)))
    
    return captures



def order_captures(board, moves, player_color):
    return sorted(moves, key=lambda m: (
        -1000 if is_promotion(m) else 
        -500 if board.en_passant_target and (1 << (m[1][0]*8 + m[1][1])) == board.en_passant_target else 
        0
    ))


def is_promotion(move):
    _, end = move
    return end[0] == 0 or end[0] == 7


# ---------------------------
# Quiescence Search
def quiesce(board, alpha, beta, player_color, q_depth=0):
    # Use full evaluation for initial stand-pat, fast_eval for deeper quiescence
    stand_pat = evaluate_board(board, player_color) if q_depth == 0 else fast_eval(board, player_color)
    
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    # Delta pruning based on max possible material gain (pawn value + buffer)
    max_gain = 15  # 10 (pawn value) + 5 buffer
    if stand_pat + max_gain <= alpha:
        return alpha

    # Early exit for deep quiescence
    if q_depth >= 2:
        return stand_pat

    # Generate and process captures
    moves = get_captures(board, board.current_player)
    moves = order_captures(board, moves, board.current_player)
    
    for move in moves:
        stored_info = board.make_move(move[0], move[1], board.current_player)
        score = -quiesce(board, -beta, -alpha, player_color, q_depth + 1)
        board.undo_move(stored_info)
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def fast_eval(board, player_color):
    """Material count only (10x faster than bin().count())"""
    w = board.white_pawns
    b = board.black_pawns
    white_count = ((w & 0xAAAAAAAAAAAAAAAA) >> 1).bit_count() + (w & 0x5555555555555555).bit_count()
    black_count = ((b & 0xAAAAAAAAAAAAAAAA) >> 1).bit_count() + (b & 0x5555555555555555).bit_count()
    return (white_count - black_count) * 10 if player_color == "W" else (black_count - white_count) * 10
# ---------------------------
# PV Search (Minimax-AlphaBeta Clone) with Quiescence
def pvs(board, depth, alpha, beta, maximizing_player, root_color):
    global TRANSPOSITION_TABLE
    entry = TRANSPOSITION_TABLE.get(board.zobrist_hash)
    if entry and entry["depth"] >= depth:
        if entry["flag"] == HASH_EXACT:
            return entry["score"], entry["best_move"]
        elif entry["flag"] == HASH_ALPHA and entry["score"] <= alpha:
            return alpha, entry["best_move"]
        elif entry["flag"] == HASH_BETA and entry["score"] >= beta:
            return beta, entry["best_move"]

    game_result = board.is_game_over_2(board.current_player)
    if game_result is not None:
        score = CHECKMATE if game_result == root_color else LOSE
        TRANSPOSITION_TABLE[board.zobrist_hash] = {"depth": depth, "score": score, "flag": HASH_EXACT, "best_move": None}
        return score, None

    if depth == 0:
        score = quiesce(board, alpha, beta, root_color)
        TRANSPOSITION_TABLE[board.zobrist_hash] = {"depth": 0, "score": score, "flag": HASH_EXACT, "best_move": None}
        return score, None

    moves = get_all_moves(board, board.current_player)
    moves = order_moves(board, moves, board.current_player)
    original_alpha = alpha
    best_move = moves[0] if moves else None

    if maximizing_player:
        max_eval = -CHECKMATE
        best_move = None
        for move in moves:
            stored_info = board.make_move(move[0], move[1], board.current_player)
            eval_score, _ = pvs(board, depth-1, alpha, beta, False, root_color)
            board.undo_move(stored_info)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
                if max_eval >= beta:
                    break
            alpha = max(alpha, max_eval)
            if alpha >= beta:
                break
        flag = HASH_EXACT
        if max_eval <= original_alpha:
            flag = HASH_ALPHA
        elif max_eval >= beta:
            flag = HASH_BETA
        TRANSPOSITION_TABLE[board.zobrist_hash] = {"depth": depth, "score": max_eval, "flag": flag, "best_move": best_move}
        return max_eval, best_move
    else:
        min_eval = CHECKMATE
        best_move = None
        for move in moves:
            stored_info = board.make_move(move[0], move[1], board.current_player)
            eval_score, _ = pvs(board, depth-1, alpha, beta, True, root_color)
            board.undo_move(stored_info)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                if min_eval <= alpha:
                    break
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        flag = HASH_EXACT
        if min_eval <= original_alpha:
            flag = HASH_ALPHA
        elif min_eval >= beta:
            flag = HASH_BETA
        TRANSPOSITION_TABLE[board.zobrist_hash] = {"depth": depth, "score": min_eval, "flag": flag, "best_move": best_move}
        return min_eval, best_move

def iterative_deepening_pvs(board, max_depth, player_color, time_limit=100):
    global TRANSPOSITION_TABLE
    start_time = time.time()
    best_move = None
    
    
    global move_count
    dynamic_max_depth = min(max_depth + move_count, 16)

    
    for depth in range(1, dynamic_max_depth + 1):
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break
        eval_score, move = pvs(board, depth, -CHECKMATE, CHECKMATE, True, player_color)
        
        
        if move:
            best_move = move
            print(f"Depth {depth} Best Move: {move_to_notation(move)} | Eval: {eval_score}")
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


move_count = 0
# ---------------------------
# Main Game Loop
def main():
    global move_count
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9999))
    running = True
    game_active = False
    clock = pygame.time.Clock()
    board = ChessBoardChessBoard_Bit()
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
            move = iterative_deepening_pvs(board, max_depth=8, player_color=player_color, time_limit=1000)
            move_notation = move_to_notation(move)
            print(f"Agent move ({player_color}): {move_notation}")
            client_socket.send(move_notation.encode())
            board.make_move(move[0], move[1], player_color)
            move_count += 1  # Increment move counter after each move

        elif data.startswith("TimeRemaining"):
            client_time_remaining = float(data.split()[1])
            print(f"Client time remaining: {client_time_remaining:.2f} seconds")
        elif data == "exit":
            print("Game over. Disconnecting.")
            break
        elif len(data) == 4:
            print(f"Opponent moved: {data}")
            start_col, start_row = ord(data[0]) - 97, 8 - int(data[1])
            end_col, end_row = ord(data[2]) - 97, 8 - int(data[3])
            opponent_color = "B" if player_color == "W" else "W"
            board.make_move((start_row, start_col), (end_row, end_col), opponent_color)
    client_socket.close()
    pygame.quit()

if __name__ == "__main__":
    main()
