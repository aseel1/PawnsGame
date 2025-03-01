import random
import socket
import pygame
import time
from board import ChessBoard

CHECKMATE = 100000000000
LOSE =     -100000000000

# ---------------------------
# Transposition Table Setup
# ---------------------------
transposition_table = {}

def board_hash(board):
    """
    Create a hashable representation of the board state.
    We use a tuple of tuples for board.boardArray, along with en_passant_target and last_move.
    """
    board_tuple = tuple(tuple(row) for row in board.boardArray)
    return (board_tuple, board.en_passant_target, board.last_move)

# ---------------------------
# Evaluation & Utility Functions
# ---------------------------
def evaluate_board(board, player_color):
    """
    Evaluate the board based on pawn game principles.
    - Passed pawns are rewarded.
    - Blocked pawns are penalized.
    - Clear paths to promotion are rewarded.
    - En passant vulnerability is penalized.
    """
    white_score = 0
    black_score = 0

    for row in range(8):
        for col in range(8):
            piece = board.boardArray[row][col]
            # White pawns
            if piece == "wp":
                white_score += 10 + (6 - row) * 2  # Base + advancement
                if is_passed_pawn((row, col), board, "W"):
                    white_score += 15
                if is_pawn_blocked((row, col), board, "W"):
                    white_score -= 5
                if is_en_passant_possible(board, (row, col), "W"):
                    white_score -= 50
            # Black pawns
            elif piece == "bp":
                black_score += 10 + (row - 1) * 2
                if is_passed_pawn((row, col), board, "B"):
                    black_score += 15
                if is_pawn_blocked((row, col), board, "B"):
                    black_score -= 5
                if is_en_passant_possible(board, (row, col), "B"):
                    black_score -= 50

    result = white_score - black_score if player_color == "W" else black_score - white_score
    return result

def is_hanging_pawn(board, pos, player_color):
    """Check if a pawn is unprotected and can be captured next turn."""
    row, col = pos
    opponent_pawn = "bp" if player_color == "W" else "wp"
    direction = -1 if player_color == "W" else 1  # opponent moves toward our side
    for dc in [-1, 1]:
        new_row, new_col = row + direction, col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board.boardArray[new_row][new_col] == opponent_pawn:
                return True
    return False

def is_passed_pawn(pos, board, player_color):
    """
    Check if a pawn is passed (no opponent pawn blocks its file or adjacent files ahead).
    """
    row, col = pos
    direction = -1 if player_color == "W" else 1
    opponent_pawn = "bp" if player_color == "W" else "wp"
    for dc in [-1, 0, 1]:
        new_col = col + dc
        if 0 <= new_col < 8:
            check_row = row + direction
            while 0 <= check_row < 8:
                if board.boardArray[check_row][new_col] == opponent_pawn:
                    return False
                check_row += direction
    return True

def is_pawn_blocked(pos, board, player_color):
    """
    Check if a pawn cannot move forward because the square ahead is occupied.
    """
    row, col = pos
    direction = -1 if player_color == "W" else 1
    forward_row = row + direction
    if 0 <= forward_row < 8 and board.boardArray[forward_row][col] != "--":
        return True
    return False

def is_en_passant_possible(board, pos, player_color):
    """
    Check if a pawn is vulnerable to an en passant capture.
    Standard rules:
      - When a white pawn moves two squares from row 6 to row 4,
        board.en_passant_target is set to the skipped square (row 5, col).
        A black pawn must be on row 4 adjacent to that target to capture.
      - When a black pawn moves two squares from row 1 to row 3,
        board.en_passant_target is set to (row 2, col),
        and a white pawn must be on row 3 adjacent to that target.
    """
    row, col = pos
    if board.en_passant_target is None:
        return False
    target_row, target_col = board.en_passant_target
    if player_color == "W":
        if row != 4 or col != target_col:
            return False
        for dc in [-1, 1]:
            adj = col + dc
            if 0 <= adj < 8 and board.boardArray[row][adj] == "bp":
                return True
    else:
        if row != 3 or col != target_col:
            return False
        for dc in [-1, 1]:
            adj = col + dc
            if 0 <= adj < 8 and board.boardArray[row][adj] == "wp":
                return True
    return False

def get_all_moves(board, player_color):
    """Generate all valid pawn moves for the given color."""
    moves = []
    direction = -1 if player_color == "W" else 1
    pawn = "wp" if player_color == "W" else "bp"
    en_passant_row = 3 if player_color == "W" else 4
    opponent_pawn = "bp" if player_color == "W" else "wp"

    for row in range(8):
        for col in range(8):
            if board.boardArray[row][col] == pawn:
                if 0 <= row + direction < 8 and board.boardArray[row + direction][col] == "--":
                    moves.append(((row, col), (row + direction, col)))
                if (player_color == "W" and row == 6) or (player_color == "B" and row == 1):
                    if (0 <= row + 2 * direction < 8 and
                        board.boardArray[row + direction][col] == "--" and
                        board.boardArray[row + 2 * direction][col] == "--"):
                        moves.append(((row, col), (row + 2 * direction, col)))
                for dc in [-1, 1]:
                    new_row, new_col = row + direction, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target = board.boardArray[new_row][new_col]
                        if (player_color == "W" and target == "bp") or (player_color == "B" and target == "wp"):
                            moves.append(((row, col), (new_row, new_col)))
                if row == en_passant_row:
                    for dc in [-1, 1]:
                        new_col = col + dc
                        if 0 <= new_col < 8:
                            if board.boardArray[row][new_col] == opponent_pawn:
                                if board.last_move:
                                    last_start, last_end = board.last_move
                                    last_start_row, _ = last_start
                                    last_end_row, last_end_col = last_end
                                    if (last_end_row == row and last_end_col == new_col and
                                        abs(last_start_row - last_end_row) == 2):
                                        moves.append(((row, col), (row + direction, new_col)))
    return moves

def generate_bitboard(board, pawn_type):
    """Generate a bitboard for pawns of the specified type."""
    bitboard = 0
    for row in range(8):
        for col in range(8):
            if board.boardArray[row][col] == pawn_type:
                bitboard |= (1 << (row * 8 + col))
    return bitboard

def bitboard_clear_path_score(player_bitboard, opponent_bitboard, player_color):
    """Evaluate clear paths to promotion using bitboards."""
    direction = -1 if player_color == "W" else 1
    promotion_row = 0 if player_color == "W" else 7
    score = 0
    for position in range(64):
        if player_bitboard & (1 << position):
            row = position // 8
            col = position % 8
            clear_path = True
            for r in range(row + direction, promotion_row + direction, direction):
                if r < 0 or r >= 8:
                    break
                if opponent_bitboard & (1 << (r * 8 + col)):
                    clear_path = False
                    break
            if clear_path:
                score += 1000
            else:
                score -= 50
    return score

def apply_move(board, move, player_color):
    """Return a new board state after applying the move."""
    new_board = ChessBoard()
    new_board.boardArray = [row[:] for row in board.boardArray]  # Deep copy
    new_board.last_move = board.last_move  # Copy last move info
    new_board.en_passant_target = board.en_passant_target  # Copy en passant target
    start, end = move
    new_board.move_pawn(start, end, player_color, simulate=True)
    return new_board

def move_to_notation(move):
    start, end = move
    return f"{chr(97 + start[1])}{8 - start[0]}{chr(97 + end[1])}{8 - end[0]}"

def order_moves(board, moves, player_color):
    """Sort moves based on heuristics for better alpha-beta pruning."""
    def move_score(move):
        start, end = move
        row, col = end
        piece = board.boardArray[row][col]
        score = 0
        if (player_color == "W" and row == 0) or (player_color == "B" and row == 7):
            score += 10000
        if piece in ["wp", "bp"]:
            score += 500
        score += (6 - row) if player_color == "W" else row
        if player_color == "W":
            if row > 0 and board.boardArray[row - 1][col] == "bp":
                score += 200
        else:
            if row < 7 and board.boardArray[row + 1][col] == "wp":
                score += 200
        return -score
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
    board = ChessBoard()  # Initialize board from board.py

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
            move = iterative_deepening_pvs(board, max_depth=11, player_color=player_color, time_limit=1000)
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
