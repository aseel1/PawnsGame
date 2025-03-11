# Pawn Chess
<p float="left">
  <img src="https://github.com/user-attachments/assets/25d607c9-0bec-499f-9ae6-e397fe99fcf5" width="350" />
  <img src="https://github.com/user-attachments/assets/66ca91d5-04aa-4534-9c27-78e531de1960" width="200" />
  <img src="https://github.com/user-attachments/assets/f50dfb69-c7f7-49bc-93dd-50d4397cdd8b" width="350" />
</p>

Pawn Chess is a simplified chess-like game that uses only pawns. The game is implemented in Python using Pygame for the graphical user interface and Python’s socket module for network communication. The engine uses an efficient bitboard representation for the board, along with advanced search techniques such as minimax with alpha–beta pruning, iterative deepening, and principal variation (PV) search with aspiration windows and transposition tables.

## Features

- **Simplified Chess:**  
  Only pawns are used, with rules for normal moves, double moves, diagonal captures, and en passant.

- **Bitboard Representation:**  
  The board is stored as two 64-bit integers (one for white pawns and one for black pawns) for fast move generation and evaluation.

- **Advanced AI:**  
  The agent uses minimax search with alpha–beta pruning enhanced by iterative deepening, principal variation (PV) search with aspiration windows, and a transposition table.

- **Networking:**  
  The server supports both Server vs Client (human vs agent) and Client vs Client (agent vs agent) modes.

- **Pygame GUI:**  
  The graphical interface displays the board, pieces, and timers, and handles mouse input for human moves.

## File Structure

- **board.py:**  
  Implements the bitboard-based `ChessBoard` class and pawn move logic.

- **UserInterface.py:**  
  Contains the Pygame-based user interface for drawing the board, pieces, timers, and handling user moves.

- **agent.py:**  
  Contains the AI agent with evaluation, move generation, and search (minimax/PV search with transposition tables).

- **server.py:**  
  Manages network connections between clients, relays moves, handles game setup, and manages game time.

## Requirements

- **Python 3.x**
- **Pygame**

Install Pygame using pip:

```bash
pip install pygame
```
## How to Run
- **1. Server vs Client (Human vs Agent)**
- You will be prompted to select the game mode (choose 1 for Server vs Client).
- Next, choose your color (enter 1 for White or 2 for Black).
- When prompted, enter a custom setup command (for example:
 Setup Wa2 Wb2 Wc2 Wd2 We2 Wf2 Wg2 Wh2 Ba7 Bb7 Bc7 Bd7 Be7 Bf7 Bg7 Bh7)
-Enter the game time in seconds.
-Finally, type a command to Begin the game (B should be capital in Begin!! important).

- **2. Client vs Client (Agent vs Agent)**
-Run the server as described above, but choose 2 for Client vs Client.
-first client that connnects is the white color the second is black
- and contine regular as before...


## Game Rules
-A pawn moves forward one square.
-On its first move, a pawn may move forward two squares if both squares are empty.
-Pawns capture diagonally.
-En passant: When a pawn moves two squares forward and lands adjacent to an opponent pawn, the opponent pawn may capture it en passant on the very next move.

**Winning Conditions:**
-A pawn reaching the opponent’s back rank wins the game.
-If all pawns of one side are captured, or if the opponent has no legal moves, the other side wins.


## Technical Details
-Bitboard Representation:
The board is represented by two 64-bit integers: one for white pawns and one for black pawns. Each bit corresponds to a square (index = row * 8 + col), which allows for very fast move generation and evaluation.
-Search Algorithms:
The AI agent uses minimax search with alpha–beta pruning enhanced by iterative deepening, principal variation (PV) search with aspiration windows, and a transposition table to speed up move calculation.
-Networking
The server uses Python’s socket module to handle connections. Moves are sent as algebraic notation (e.g., "e2e4") and converted to bit indices using helper functions.
-User Interface:
The game uses Pygame for the GUI. The UI draws the board and pieces (using the bitboard representation) and handles mouse input for human moves.
-Responsiveness:
If the agent’s deep search causes the screen to freeze (or turn black), consider offloading the search computation to a separate thread so that the Pygame event loop remains responsive.


## Extra instructions:
the code is relased where it can be downloaded eaisly and played instead of compiling it.
![image](https://github.com/user-attachments/assets/ad57e7fd-7740-4ba5-b2fb-953c11453653)
 as seen there are diffrenet kind of agents each with spceifec implemntation and add-ons. 
the last agent which contatins all of the implementations is the aspiration window.




Credits -Aseel shaheen
email:aseelshaheen1@gmail.com










