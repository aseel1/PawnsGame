import socket
import pygame
from Board_bit import ChessBoardChessBoard_Bit
from UserInterface_bit import UserInterface

clients = []

def send_to_all_clients(message):
    """Send a message to both clients."""
    for client in clients:
        client.send(message.encode())

def wait_for_ok(client, step_description):
    """Wait for 'OK' from a client and handle errors."""
    response = client.recv(1024).decode()
    if response != "OK":
        print(f"Client failed to respond with OK during {step_description}.")
        client.close()
        exit()

def start_server():
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 9999))
    server_socket.listen(2)
    print("Server started on port 9999... Waiting for players to connect.")


    #! Select game mode
    print("Select Game Mode:")
    print("1. Server vs Client (You play against the agent)")
    print("2. Client vs Client (Agent vs Agent)")
    mode = input("Enter 1 or 2: ")
    
    # Select the server's color if Server vs Client
    server_color = "W"
    client_color = "B"
    if mode == "1":
        print("Select your color:")
        print("1. White")
        print("2. Black")
        color_choice = input("Enter 1 for White or 2 for Black: ")

        if color_choice == "1":
            server_color = "W"
            client_color = "B"
        else:
            server_color = "B"
            client_color = "W"
        
        
            
    print("Waiting for a client to connect...")
          
    
    # Accept client(s)
    
    #! Server vs Client
    if mode == "1":
        # Server vs Client
        client_socket, client_address = server_socket.accept()
        clients.append(client_socket)
        print(f"Client connected from {client_address}")
        client_socket.send("Connected to the server!".encode())
        wait_for_ok(client_socket, "connection confirmation")

        # 🔥 Send color assignment to the client
        client_socket.send(f"Color {client_color}".encode())
        wait_for_ok(client_socket, "color confirmation")
        
        #! Initialize Pygame for server GUI
        pygame.init()
        surface = pygame.display.set_mode([600, 600])
        pygame.display.set_caption("Pawn Chess - Server")
        Board = ChessBoardChessBoard_Bit()
        UI = UserInterface(surface, Board, player_color=server_color)

        
    #! Client vs Client
    elif mode == "2":    
            # Client vs Client - Wait for two agents to connect
            print("Waiting for two agents to connect...")
            while len(clients) < 2:
                client_socket, client_address = server_socket.accept()
                clients.append(client_socket)
                print(f"Player {len(clients)} connected from {client_address}")
                client_socket.send("Connected to the server!".encode())
                wait_for_ok(client_socket, f"connection confirmation for Player {len(clients)}")

            # ✅ Assign colors after both clients have connected
            print("Both players connected. Assigning colors...")

            clients[0].send("Color W".encode())  # Player 1 is White
            wait_for_ok(clients[0], "color assignment for Player 1")

            clients[1].send("Color B".encode())  # Player 2 is Black
            wait_for_ok(clients[1], "color assignment for Player 2")
            
            # #! Initialize Pygame for Client vs Client GUI
            pygame.init()
            surface = pygame.display.set_mode([600, 600])
            pygame.display.set_caption("Pawn Chess - Client vs Client")
            Board = ChessBoardChessBoard_Bit()
            UI = UserInterface(surface, Board , player_color=server_color)
    else:
        print("Invalid selection.")
        return
        
    
    #! Step 2: Send custom Setup command
    setup_message = input("Enter setup command (e.g., 'Setup Wa2 Wb2 Wc2 Wd2 We2 Wf2 Wg2 Wh2 Ba7 Bb7 Bc7 Bd7 Be7 Bf7 Bg7 Bh7'): ")
    Board.initialize_custom_board(setup_message)
    send_to_all_clients(setup_message)
    for client in clients:
        wait_for_ok(client, "setup confirmation")

    #! Step 3: Send game time
    game_time = input("Enter game time in minutes (e.g., 'Time 10'): ")
    send_to_all_clients(game_time)
    game_time = float(game_time) # Convert to seconds
    
    server_time_remaining = game_time
    client_time_remaining = game_time
    start_time = pygame.time.get_ticks()

    UI.server_time = server_time_remaining   # Convert to minutes
    UI.client_time = client_time_remaining   # Convert to minutes
        
    
    for client in clients:
        wait_for_ok(client, "time confirmation")

    #! Step 4: Begin the game
    begin_message = input(" Enter begin to the game...")
    send_to_all_clients(begin_message)
 
    #! Step 5: Game loop
    player_index = 0 if server_color == "W" else 1
    running = True
    last_turn_start_time = pygame.time.get_ticks() / 1000  # Start time in seconds

    while running:
        current_time = pygame.time.get_ticks() / 1000  # Current time in seconds

        if mode == "1":
            if player_index == 0:
                # Server's turn (User input)
                print("--------------------------------------------")
                print(f"Your turn (Server {server_color}):")
                move, flag = UI.clientMove()  # Using the same method as the client for making a move
                
                
                # Calculate time taken
                current_time2 = pygame.time.get_ticks() / 1000
                elapsed_time = current_time2 - current_time
                server_time_remaining -= elapsed_time

                #?print(server_time_remaining)

                if server_time_remaining <= 0:
                    print("Server ran out of time. Client wins!")
                    clients[0].send("exit".encode())
                    break

                # Format move as e2e4
                move_str = f"{chr(97 + move[1])}{8 - move[0]}{chr(97 + move[3])}{8 - move[2]}"
                clients[0].send(move_str.encode())
                
                print(f"Server's move: {move_str}")
                print(f"Time remaining for server: {server_time_remaining:.2f} seconds")

                # 🔥 Check if the server wins
                winner = Board.is_game_over(server_color)
                if winner:
                    print(f"{'Server' if winner == server_color else 'Client'} wins!")
                    clients[0].send("exit".encode())
                    break
                Board.print_board()

                        
            else:
                # Client's turn
                clients[0].send("Your turn".encode())
                move = clients[0].recv(1024).decode()
                
                # Calculate time taken
                current_time2 = pygame.time.get_ticks() / 1000
                elapsed_time = current_time2 - current_time
                client_time_remaining -= elapsed_time


                if client_time_remaining <= 0:
                    print("Client ran out of time. Server wins!")
                    clients[0].send("exit".encode())
                    break


                # Send remaining time to the client
                clients[0].send(f"TimeRemaining {client_time_remaining:.2f}".encode())

                print(f"Client's move: {move}")
                print(f"Time remaining for client: {client_time_remaining:.2f} seconds")

                # Apply the client's move on the server's GUI
                start_col, start_row = ord(move[0]) - 97, 8 - int(move[1])
                end_col, end_row = ord(move[2]) - 97, 8 - int(move[3])
                # Board.move_pawn((start_row, start_col), (end_row, end_col), client_color)
                # Apply the opponent's move permanently using the new make_move system.
                Board.make_move((start_row, start_col), (end_row, end_col), client_color)

                # 🔥 Check if the client wins
                winner = Board.is_game_over(client_color)
                if winner:
                    print(f"{'Client' if winner == client_color else 'Server'} wins!")
                    clients[0].send("exit".encode())
                    break
                
                
                Board.print_board()




        elif mode == "2":
            
            current_player_color=  "W" if player_index == 0 else "B"
            opponent_color = "B" if current_player_color == "W" else "W"
            
            #this is the remaining time for the current client  ServerTime for client0 and ClientTime for client1
            player_time_remaining = (
            server_time_remaining if player_index == 0 else client_time_remaining
            )
                    
            # Client vs Client
            clients[player_index].send("Your turn".encode())
            move = clients[player_index].recv(1024).decode()
            print(f"Player {current_player_color} move: {move}")
            


            clients[1 - player_index].send(move.encode()) # Send move to client
            


            # Apply the move to the GUI
            start_col, start_row = ord(move[0]) - 97, 8 - int(move[1])
            end_col, end_row = ord(move[2]) - 97, 8 - int(move[3])
            # Board.move_pawn((start_row, start_col), (end_row, end_col), current_player_color)
            
            # Apply the opponent's move permanently using the new make_move system.
            Board.make_move((start_row, start_col), (end_row, end_col), current_player_color)


            current_time2 = pygame.time.get_ticks() / 1000
            # Calculate time taken
            elapsed_time = current_time2 - current_time
            if player_index == 0:
                server_time_remaining -= elapsed_time
            else:
                client_time_remaining -= elapsed_time
            
            # Check if the current player's time expired
            if player_time_remaining <= 0:
                send_to_all_clients("exit")
                print(f"Player {player_index } ran out of time. Player {1 - player_index} wins!")
                break
            
            # 🔥 Check if the client wins
            winner = Board.is_game_over(current_player_color)
            if winner:
                print(f"{'Client' if winner == client_color else 'Server'} wins!")
                clients[0].send("exit".encode())
                clients[1].send("exit".encode())

                break
            
            Board.print_board()
            
        # Switch turns
        UI.server_time = server_time_remaining
        UI.client_time = client_time_remaining
        UI.drawComponent()  # Always update the GUI
        pygame.display.flip()
        player_index = 1 - player_index

    # Close connections
    for client in clients:
        client.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
