# Distributed Black Jack

This is a project developed as part of the Distributed Computing course. The goal of the project is to create a P2P (peer-to-peer) black jack game where friends can play against each other. The game is fully distributed, with no central dealer, and players compete against each other.

## Introduction

In the game of black jack, players start by drawing two cards. They then take turns drawing cards until they reach a value close to 21. The "Ace" can be worth 1 or 11, face cards are worth 10, and the remaining cards have their face value. A player who is close to 21 without going over can pass their turn to another player. A player who reaches 21 immediately wins, and a player who exceeds 21 automatically loses ("bust"). The game assumes that each player's cards are unknown to their opponents, and players must inform others when they win or lose. The first player to reach 21 or the last player to go "bust" is the winner of the game.
## Contributors

## Project Structure

The project follows the client-server architecture, with the following components:

- `player.py`: This file contains the implementation of a well-behaved player agent for the black jack game.
- `bad_player.py`: This file contains the implementation of a misbehaving player agent that can cheat during the game.
- `deck.py`: This file contains the implementation of the central card deck server, which provides cards to the players upon request.
- `utils.py`: This file contains score calculater and the cards

## Concepts Covered

The project covers the following concepts:

- Sockets: Communication between players and the central deck server is done using socket programming.
- Marshalling: Communication messages are marshaled and unmarshaled to exchange information between players and the deck server.
- P2P: The game is designed as a peer-to-peer system, where players interact with each other directly.
- Fault Tolerance: The system should be able to handle failures and ensure that the game progresses correctly even in the presence of failures.

## Dependencies

```
sudo apt-get install redis
```

## Usage

1. Run central deck server
```
python deck.py
```

2. Run the player agents
   - Good player
  ```
  python3 player.py -s self_player -p other_players
  ```
   - Cheater Player
  ```
  python3 bad_player.py -s self_player -p other_players
  ```

3. Follow the instructions on the command line to interact with the game.

## Authors

* **Cristiano Nicolau** - [cristiano-nicolau]([https://github.com/cristiano-nicolau])
