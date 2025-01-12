import socket
import pygame
from board import ChessBoard
from UserInterface import UserInterface

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
        Board = ChessBoard()
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
            
            #! Initialize Pygame for Client vs Client GUI
            pygame.init()
            surface = pygame.display.set_mode([600, 600])
            pygame.display.set_caption("Pawn Chess - Client vs Client")
            Board = ChessBoard()
            UI = UserInterface(surface, Board)
    else:
        print("Invalid selection.")
        return
        
    
    # Step 2: Send custom Setup command
    setup_message = input("Enter setup command (e.g., 'Setup Wb4 Wa3 Wc2 Bg7 Wd4 Bg6 Be7'): ")
    send_to_all_clients(setup_message)
    for client in clients:
        wait_for_ok(client, "setup confirmation")

    # Step 3: Send game time
    game_time = input("Enter game time in minutes (e.g., 'Time 10'): ")
    send_to_all_clients(game_time)
    for client in clients:
        wait_for_ok(client, "time confirmation")

    # Step 4: Begin the game
    begin_message = input(" Enter begin to the game...")
    send_to_all_clients(begin_message)

    # Step 5: Game loop
    player_index = 0 if server_color == "W" else 1
    running = True

    while running:
        if mode == "1":
            if player_index == 0:
                # Server's turn (User input)
                print("Your turn (Server GUI):")
                move, flag = UI.clientMove()  # Using the same method as the client for making a move
                

                # Format move as e2e4
                move_str = f"{chr(97 + move[1])}{8 - move[0]}{chr(97 + move[3])}{8 - move[2]}"
                clients[0].send(move_str.encode())
                
                # 🔥 Check if the server wins
                winner = Board.is_game_over(server_color)
                if winner:
                    print(f"{'Server' if winner == server_color else 'Client'} wins!")
                    clients[0].send("exit".encode())
                    break
                        
            else:
                # Client's turn
                clients[0].send("Your turn".encode())
                move = clients[0].recv(1024).decode()
                

                print(f"Client's move: {move}")
                
                # Apply the client's move on the server's GUI
                start_col, start_row = ord(move[0]) - 97, 8 - int(move[1])
                end_col, end_row = ord(move[2]) - 97, 8 - int(move[3])
                Board.move_pawn((start_row, start_col), (end_row, end_col), client_color)
                
                # 🔥 Check if the client wins
                winner = Board.is_game_over(client_color)
                if winner:
                    print(f"{'Client' if winner == client_color else 'Server'} wins!")
                    clients[0].send("exit".encode())
                    break



        elif mode == "2":
            # Client vs Client
            clients[player_index].send("Your turn".encode())
            move = clients[player_index].recv(1024).decode()

            if move == "exit":
                send_to_all_clients("exit")
                print("A client resigned. Ending game.")
                break

            print(f"Player {player_index + 1} move: {move}")
            clients[1 - player_index].send(move.encode()) # Send move to client


            # Apply the move to the GUI
            start_col, start_row = ord(move[0]) - 97, 8 - int(move[1])
            end_col, end_row = ord(move[2]) - 97, 8 - int(move[3])
            Board.move_pawn((start_row, start_col), (end_row, end_col), "W" if player_index == 0 else "B")


        # Switch turns
        player_index = 1 - player_index
        
        UI.drawComponent()  # Always update the GUI
        pygame.display.flip()
        
    # Close connections
    for client in clients:
        client.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
