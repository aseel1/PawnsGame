import socket

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


    # Select game mode
    print("Select Game Mode:")
    print("1. Server vs Client (You play against the agent)")
    print("2. Client vs Client (Agent vs Agent)")
    mode = input("Enter 1 or 2: ")
    
    # Accept client(s)
    
    #? Server vs Client
    if mode == "1":
        # Server vs Client
        client_socket, client_address = server_socket.accept()
        clients.append(client_socket)
        print(f"Client connected from {client_address}")
        client_socket.send("Connected to the server!".encode())
        wait_for_ok(client_socket, "connection confirmation")

    #? Client vs Client
    elif mode == "2":    
        for i in range(2):
            client_socket, client_address = server_socket.accept()
            clients.append(client_socket)
            print(f"Player {i + 1} connected from {client_address}")
            client_socket.send("Connected to the server!".encode())
            wait_for_ok(client_socket, "connection confirmation")
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
    player_index = 0

    while True:
        if mode == "1":
            if player_index == 0:
                # Server's turn (User input)
                print("Your turn:")
                move = input("Enter your move (e.g., e2e4 or 'exit'): ")
                if move == "exit":
                    clients[0].send("exit".encode())
                    break
                clients[0].send(move.encode())  # Send move to client

            else:
                # Client's turn
                clients[0].send("Your turn".encode())
                move = clients[0].recv(1024).decode()
                if move == "exit":
                    print("Client resigned. Game over.")
                    break
                print(f"Client's move: {move}")

        elif mode == "2":
            # Client vs Client
            clients[player_index].send("Your turn".encode())
            move = clients[player_index].recv(1024).decode()

            if move == "exit":
                send_to_all_clients("exit")
                print("A client resigned. Ending game.")
                break

            print(f"Player {player_index + 1} move: {move}")
            clients[1 - player_index].send(move.encode())

        # Switch turns
        player_index = 1 - player_index

    # Close connections
    for client in clients:
        client.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
