import random
import socket
import pygame
from board import ChessBoard

CHECKMATE = 100000000000
LOSE =     -100000000000

# Minimax Evaluation Function
# def evaluate_board(board, player_color):
#     """
#     Advanced evaluation function for the pawn game.
#     - Strongly rewards promotion and aggressive advancement.
#     - Penalizes weak pawn structures (isolated, doubled, blocked pawns).
#     - Encourages central control and blocking opponent pawns.
#     - Recognizes passed pawns and threats.
#     - Adds a heuristic for detecting a free road to victory.
#     """
#     score = 0

#     # Constants for scoring
#     PAWN_VALUE = 100              # Base reward for pawns
#     ADVANCE_REWARD = 20           # Reward for advancing pawns
#     CENTER_CONTROL_REWARD = 50    # Reward for controlling the center
#     CAPTURE_THREAT_REWARD = 500   # Reward for threatening a capture
#     CAPTURE_REWARD = 800          # Reward for actual captures
#     PROMOTION_REWARD = 9000    # Max reward for promotion
#     BLOCK_OPPONENT_REWARD = 200   # Reward for blocking opponent pawns
#     PASSED_PAWN_REWARD = 300      # Reward for passed pawns
#     FREE_PATH_REWARD = 9000       # Strong reward for a free path to promotion
#     ISOLATED_PAWN_PENALTY = 75    # Penalty for isolated pawns
#     DOUBLED_PAWN_PENALTY = 75     # Penalty for doubled pawns
#     BLOCKED_PAWN_PENALTY = 100    # Penalty for blocked pawns
#     OPPONENT_CAPTURE_PENALTY = 800  # Penalty if AI pawn is captured

#     # Board-specific parameters
#     player_pawn = "wp" if player_color == "W" else "bp"
#     opponent_pawn = "bp" if player_color == "W" else "wp"
#     direction = -1 if player_color == "W" else 1
#     promotion_row = 0 if player_color == "W" else 7
#     center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]  # Control of the center

#     player_pawn_count = 0
#     opponent_pawn_count = 0

#     for row in range(8):
#         for col in range(8):
#             piece = board.boardArray[row][col]

#             # ✅ Player's pawns
#             if piece == player_pawn:
#                 player_pawn_count += 1
#                 score += PAWN_VALUE

#                 # ✅ Advancement reward
#                 advancement = (6 - row) if player_color == "W" else (row - 1)
#                 score += advancement * ADVANCE_REWARD

#                 # ✅ Promotion Reward
#                 if row == promotion_row:
#                     return PROMOTION_REWARD  # Instant win

#                 # ✅ Passed pawn bonus (no opponent blocking it)
#                 is_passed = True
#                 check_row_range = range(row - 1, -1, -1) if player_color == "W" else range(row + 1, 8)
#                 for r in check_row_range:
#                     if board.boardArray[r][col] == opponent_pawn:
#                         is_passed = False
#                         break
#                 if is_passed:
#                     score += PASSED_PAWN_REWARD

#                 # ✅ Free Path to Victory
#                 is_free_path = True
#                 for r in check_row_range:
#                     if board.boardArray[r][col] != "--":
#                         is_free_path = False
#                         break
#                 if is_free_path:
#                     score += FREE_PATH_REWARD

#                 # ✅ Control of the center
#                 if (row, col) in center_squares:
#                     score += CENTER_CONTROL_REWARD

#                 # ✅ Threatening opponent pawns
#                 for dc in [-1, 1]:
#                     new_row, new_col = row + direction, col + dc
#                     if 0 <= new_row < 8 and 0 <= new_col < 8:
#                         target_piece = board.boardArray[new_row][new_col]
#                         if target_piece == opponent_pawn:
#                             score += CAPTURE_THREAT_REWARD

#                 # ⚠️ Isolated pawn penalty
#                 if not ((col > 0 and board.boardArray[row][col - 1] == player_pawn) or 
#                         (col < 7 and board.boardArray[row][col + 1] == player_pawn)):
#                     score -= ISOLATED_PAWN_PENALTY

#                 # ⚠️ Doubled pawn penalty
#                 for check_row in range(8):
#                     if check_row != row and board.boardArray[check_row][col] == player_pawn:
#                         score -= DOUBLED_PAWN_PENALTY
#                         break

#                 # ⚠️ Blocked pawn penalty
#                 if 0 <= row + direction < 8 and board.boardArray[row + direction][col] != "--":
#                     score -= BLOCKED_PAWN_PENALTY

#             # 🚨 Opponent's pawns
#             elif piece == opponent_pawn:
#                 opponent_pawn_count += 1
#                 score -= PAWN_VALUE

#                 # Penalize if the opponent is close to promotion
#                 if row == promotion_row:
#                     return -PROMOTION_REWARD  # Instant loss

#                 # Penalize if the opponent controls the center
#                 if (row, col) in center_squares:
#                     score -= CENTER_CONTROL_REWARD

#                 # Reward blocking the opponent's pawns
#                 if 0 <= row - direction < 8 and board.boardArray[row - direction][col] == player_pawn:
#                     score += BLOCK_OPPONENT_REWARD

#     # ✅ Reward for Actual Captures
#     total_opponent_pawns = 8
#     captured_opponent_pawns = total_opponent_pawns - opponent_pawn_count
#     score += captured_opponent_pawns * CAPTURE_REWARD

#     # 🚨 Penalty for Losing Pawns
#     total_player_pawns = 8
#     lost_player_pawns = total_player_pawns - player_pawn_count
#     score -= lost_player_pawns * OPPONENT_CAPTURE_PENALTY
    
#     return score
def evaluate_board(board, player_color):
    """
    Evaluate the board based on pawn game principles with integrated bitboard evaluation.
    - Passed pawns are rewarded.
    - Blocked pawns are penalized.
    - Clear paths to promotion using bitboard are rewarded.
    - Score adjusts based on rank (advancement).
    """
    white_score = 0
    black_score = 0

    # Generate bitboards for white and black pawns
    # white_pawns_bitboard = generate_bitboard(board, "wp")
    # black_pawns_bitboard = generate_bitboard(board, "bp")

    for row in range(8):
        for col in range(8):
            piece = board.boardArray[row][col]

            # White pawns
            if piece == "wp":
                white_score += 10 + (6 - row) * 2  # Base and advancement reward
                if is_passed_pawn((row, col), board, "W"):
                    white_score += 15
                if is_pawn_blocked((row, col), board, "W"):
                    white_score -= 5

                # Check for En Passant vulnerability
                if is_en_passant_possible(board, (row, col), "W"):
                    white_score -= 50  # Penalize for vulnerability

            # Black pawns
            elif piece == "bp":
                black_score += 10 + row * 2  # Base and advancement reward
                if is_passed_pawn((row, col), board, "B"):
                    black_score += 15
                if is_pawn_blocked((row, col), board, "B"):
                    black_score -= 5

                # Check for En Passant vulnerability
                if is_en_passant_possible(board, (row, col), "B"):
                    black_score -= 50  # Penalize for vulnerability

    # Integrate bitboard-based clear path evaluation
    # white_score += bitboard_clear_path_score(white_pawns_bitboard, black_pawns_bitboard, "W")
    # black_score += bitboard_clear_path_score(black_pawns_bitboard, white_pawns_bitboard, "B")

    # Return score relative to player color
    return white_score - black_score if player_color == "W" else black_score - white_score


def is_passed_pawn(pos, board, player_color):
    """
    Check if a pawn is passed (no opponent pawns blocking its file or adjacent files).
    """
    row, col = pos
    direction = -1 if player_color == "W" else 1
    opponent_pawn = "bp" if player_color == "W" else "wp"

    for dc in [-1, 0, 1]:  # Check the same file and adjacent files
        new_col = col + dc
        if 0 <= new_col < 8:
            check_row = row + direction
            while 0 <= check_row < 8:
                if board.boardArray[check_row][new_col] == opponent_pawn:
                    return False  # Opponent pawn found blocking
                check_row += direction
    return True

def is_pawn_blocked(pos, board, player_color):
    """
    Check if a pawn is blocked (cannot move forward).
    """
    row, col = pos
    direction = -1 if player_color == "W" else 1
    forward_row = row + direction

    # Check if the square directly in front is occupied
    if 0 <= forward_row < 8 and board.boardArray[forward_row][col] != "--":
        return True
    return False

def is_en_passant_possible(board, pos, player_color):
    """
    Check if a pawn is vulnerable to or can perform an En Passant move.
    """
    row, col = pos
    direction = -1 if player_color == "W" else 1
    opponent_pawn = "bp" if player_color == "W" else "wp"
    en_passant_row = 3 if player_color == "W" else 4

    # Check for En Passant vulnerability
    if row == en_passant_row:
        for dc in [-1, 1]:
            adjacent_col = col + dc
            if 0 <= adjacent_col < 8:
                # Check if opponent pawn moved two steps forward
                if board.boardArray[row][adjacent_col] == opponent_pawn:
                    capture_row = row + direction
                    if 0 <= capture_row < 8 and board.boardArray[capture_row][col] == "--":
                        return True  # En Passant is possible
    return False



# Generate All Valid Moves for a Given Color
def get_all_moves(board, player_color):
    """Generate all valid pawn moves for the given color."""
    moves = []
    direction = -1 if player_color == "W" else 1
    pawn = "wp" if player_color == "W" else "bp"
    en_passant_row = 3 if player_color == "W" else 4  # Row where en passant is possible
    opponent_pawn = "bp" if player_color == "W" else "wp"

    for row in range(8):
        for col in range(8):
            if board.boardArray[row][col] == pawn:
                # Move forward by 1
                if 0 <= row + direction < 8 and board.boardArray[row + direction][col] == "--":
                    moves.append(((row, col), (row + direction, col)))

                # Move forward by 2 from starting position
                if (player_color == "W" and row == 6) or (player_color == "B" and row == 1):
                    if (0 <= row + 2 * direction < 8 and
                        board.boardArray[row + direction][col] == "--" and
                        board.boardArray[row + 2 * direction][col] == "--"):
                        moves.append(((row, col), (row + 2 * direction, col)))

                # Capture diagonally (with boundary checks)
                for dc in [-1, 1]:
                    new_row, new_col = row + direction, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target = board.boardArray[new_row][new_col]
                        if (player_color == "W" and target == "bp") or (player_color == "B" and target == "wp"):
                            moves.append(((row, col), (new_row, new_col)))
                        
                # En Passant capture
                if row == en_passant_row:
                    for dc in [-1, 1]:
                        new_col = col + dc
                        if 0 <= new_col < 8:
                            if board.boardArray[row][new_col] == opponent_pawn:
                                # Check if the opponent's pawn just moved two squares forward
                                if (player_color == "W" and row == 3 and board.boardArray[row + 1][new_col] == opponent_pawn) or \
                                   (player_color == "B" and row == 4 and board.boardArray[row - 1][new_col] == opponent_pawn):
                                    moves.append(((row, col), (row + direction, new_col)))

    return moves

def generate_bitboard(board, pawn_type):
    """
    Generate a bitboard for pawns of the specified type ('wp' or 'bp').
    Each bit represents a square on the board, where 1 indicates the presence of the pawn.
    """
    bitboard = 0
    for row in range(8):
        for col in range(8):
            if board.boardArray[row][col] == pawn_type:
                bitboard |= (1 << (row * 8 + col))
    return bitboard

def bitboard_clear_path_score(player_bitboard, opponent_bitboard, player_color):
    """
    Evaluate clear paths to promotion for a given player's pawns using bitboards.
    """
    direction = -1 if player_color == "W" else 1
    promotion_row = 0 if player_color == "W" else 7
    score = 0

    for position in range(64):
        if player_bitboard & (1 << position):
            row = position // 8
            col = position % 8

            # Check for a clear path to promotion
            clear_path = True
            for r in range(row + direction, promotion_row + direction, direction):
                if r < 0 or r >= 8:
                    break
                if opponent_bitboard & (1 << (r * 8 + col)):
                    clear_path = False
                    break

            # Reward pawns with a clear path
            if clear_path:
                score += 1000  # Strong reward for guaranteed promotion
            else:
                # Penalize if blocked
                score -= 50

    return score



# Apply a Move to the Board
def apply_move(board, move, player_color):
    """Apply a move to the board and return a new board state."""
    new_board = ChessBoard()
    new_board.boardArray = [row[:] for row in board.boardArray]  # Deep copy

    start, end = move
    new_board.move_pawn(start, end, player_color, simulate=True)  # 🔥 Disable printing during simulation
    return new_board

# Convert a Move to Chess Notation (e.g., e2e4)
def move_to_notation(move):
    start, end = move
    return f"{chr(97 + start[1])}{8 - start[0]}{chr(97 + end[1])}{8 - end[0]}"




def minimax(board, depth, alpha, beta, maximizing_player, player_color):
    opponent_color = "B" if player_color == "W" else "W"
    current_color = player_color if maximizing_player else opponent_color


    if depth == 0 or board.is_game_over_2(current_color):
        if board.is_game_over_2(current_color):
            return CHECKMATE if maximizing_player else LOSE, None
        return evaluate_board(board, current_color), None


    best_move = None
    moves = get_all_moves(board,current_color)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_board = apply_move(board, move, player_color)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, player_color)

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-Beta Pruning
            
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = apply_move(board, move, opponent_color)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, player_color)

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-Beta Pruning

        return min_eval, best_move

    
def main():

    # Step 1: Connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9999))
    
    running = True
    game_active = False  # Game starts after "Begin"
    clock = pygame.time.Clock()
    board = ChessBoard()  # Initialize the client's board to match the server
    
    while running :
        
        
        data = client_socket.recv(1024).decode()

        #? Step 2: Confirm connection
        if data == "Connected to the server!":
            client_socket.send("OK".encode())

        #? Step 2: Confirm color
        elif data.startswith("Color"):
            player_color = data.split()[1]
            print(f"My color is: {player_color}")
            client_socket.send("OK".encode())
                   
        #? Step 3: Handle Setup command
        elif data.startswith("Setup"):
            print(f"Setting up the board: {data}")
            board.initialize_custom_board(data)  # Initialize the board locally
            client_socket.send("OK".encode())

        #? Step 4: Handle game time
        elif data.isdigit():
            
            print(f"Game time set to {data} minutes.")
            client_socket.send("OK".encode())
            
        #? Step 5: Game begins
        elif data == "Begin":
            print("Game is starting!")
            game_active = True  # Start updating the game

        #? Step 6: Handle turn
        elif data == "Your turn" and game_active:
            
            print("--------------------------------")
            print("Agent is thinking...")
            _, move =minimax(board, depth=8, alpha=LOSE, beta=CHECKMATE, maximizing_player=True, player_color=player_color)
            # ✅ Convert the move to chess notation
   
            move_notation = move_to_notation(move)
            print(f"Agent move ({player_color}): {move_notation}")
            
            client_socket.send(move_notation.encode())
            
            # ✅ Apply the move to the internal board
            board.move_pawn(move[0], move[1], player_color)
        
        
        elif data.startswith("TimeRemaining"):
            # Extract remaining time from the server
            client_time_remaining = float(data.split()[1])
            print(f"Client time remaining : {client_time_remaining:.2f} seconds")
            
    
        #? Step 7: Handle game termination
        elif data == "exit":
            print("Game over. Disconnecting.")
            break

        #? Step 8: Handle opponent's move
        elif len(data) == 4:  # e.g., "e2e4"
            print(f"Opponent moved: {data}")

            # Convert the move from notation to board coordinates
            start_col, start_row = ord(data[0]) - 97, 8 - int(data[1])
            end_col, end_row = ord(data[2]) - 97, 8 - int(data[3])
            
            # Apply the opponent's move to the client's board
            opponent_color = "B" if player_color == "W" else "W"
            
            board.move_pawn((start_row, start_col), (end_row, end_col), opponent_color)
            




    client_socket.close()
    pygame.quit()

if __name__ == "__main__":
    main()
