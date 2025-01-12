import random
import socket
import pygame
from board import ChessBoard


# Minimax Evaluation Function
def evaluate_board(board, player_color):
    """Simple evaluation based on pawn count."""
    white_pawns = sum(row.count("wp") for row in board.boardArray)
    black_pawns = sum(row.count("bp") for row in board.boardArray)
    return white_pawns - black_pawns if player_color == "W" else black_pawns - white_pawns

# Generate All Valid Moves for a Given Color
def get_all_moves(board, player_color):
    """Generate all valid pawn moves for the given color."""
    moves = []
    direction = -1 if player_color == "W" else 1
    pawn = "wp" if player_color == "W" else "bp"

    for row in range(8):
        for col in range(8):
            if board.boardArray[row][col] == pawn:
                # Move forward by 1
                if 0 <= row + direction < 8 and board.boardArray[row + direction][col] == "--":
                    moves.append(((row, col), (row + direction, col)))

                # Move forward by 2 from starting position
                if (player_color == "W" and row == 6) or (player_color == "B" and row == 1):
                    if board.boardArray[row + direction][col] == "--" and board.boardArray[row + 2 * direction][col] == "--":
                        moves.append(((row, col), (row + 2 * direction, col)))

                # Capture diagonally
                for dc in [-1, 1]:
                    if 0 <= col + dc < 8:
                        target = board.boardArray[row + direction][col + dc]
                        if (player_color == "W" and target == "bp") or (player_color == "B" and target == "wp"):
                            moves.append(((row, col), (row + direction, col + dc)))
    return moves

# Apply a Move to the Board
def apply_move(board, move, player_color):
    """Apply a move to the board and return a new board state."""
    new_board = ChessBoard()
    new_board.boardArray = [row[:] for row in board.boardArray]  # Deep copy

    start, end = move
    new_board.move_pawn(start, end, player_color)
    return new_board

# Convert a Move to Chess Notation (e.g., e2e4)
def move_to_notation(move):
    start, end = move
    return f"{chr(97 + start[1])}{8 - start[0]}{chr(97 + end[1])}{8 - end[0]}"

# Minimax Algorithm
def minimax(board, depth, maximizing_player, player_color):
    """Minimax algorithm for decision making."""
    if depth == 0:
        return evaluate_board(board, player_color), None

    best_move = None
    opponent_color = "B" if player_color == "W" else "W"

    if maximizing_player:
        max_eval = float('-inf')
        for move in get_all_moves(board, player_color):
            new_board = apply_move(board, move, player_color)
            eval_score, _ = minimax(new_board, depth - 1, False, player_color)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in get_all_moves(board, opponent_color):
            new_board = apply_move(board, move, opponent_color)
            eval_score, _ = minimax(new_board, depth - 1, True, player_color)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
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
            print("Agent is thinking...")
            _, move = minimax(board, depth=2, maximizing_player=True, player_color=player_color)  # Use Minimax to decide the move
            
            # ✅ Convert the move to chess notation
            move_notation = move_to_notation(move)
            print(f"Agent move: {move_notation}")
            
            client_socket.send(move_notation.encode())
            
            # ✅ Apply the move to the internal board
            board.move_pawn(move[0], move[1], player_color)

        #? Step 7: Handle opponent's move
        elif len(data) == 4:  # e.g., "e2e4"
            print(f"Opponent moved: {data}")

            # Convert the move from notation to board coordinates
            start_col, start_row = ord(data[0]) - 97, 8 - int(data[1])
            end_col, end_row = ord(data[2]) - 97, 8 - int(data[3])
            
            # Apply the opponent's move to the client's board
            opponent_color = "B" if player_color == "W" else "W"
            board.move_pawn((start_row, start_col), (end_row, end_col), opponent_color)
            
        #? Step 8: Handle game termination
        elif data == "exit":
            print("Game over. Disconnecting.")
            break




    client_socket.close()
    pygame.quit()

if __name__ == "__main__":
    main()
