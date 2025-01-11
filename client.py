import socket

def main():
    # Step 1: Connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9999))
    
    while True:
        data = client_socket.recv(1024).decode()

        # Step 2: Confirm connection
        if data == "Connected to the server!":
            client_socket.send("OK".encode())

        # Step 3: Handle Setup command
        elif data.startswith("Setup"):
            print(f"Setting up the board: {data}")
            client_socket.send("OK".encode())

        # Step 4: Handle game time
        elif data.isdigit():
            print(f"Game time set to {data} minutes.")
            client_socket.send("OK".encode())
            
        # Step 5: Game begins
        elif data == "Begin":
            print("Game is starting!")

        # Step 6: Handle turn
        elif data == "Your turn":
            move = input("Enter your move (e.g., e2e4): ")
            client_socket.send(move.encode())

        # Step 7: Handle opponent's move
        elif len(data) == 4:  # e.g., "e2e4"
            print(f"Opponent moved: {data}")

        # Step 8: Handle game termination
        elif data == "exit":
            print("Game over. Disconnecting.")
            break

    client_socket.close()

if __name__ == "__main__":
    main()
