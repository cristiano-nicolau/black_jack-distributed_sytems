import argparse
import socket
from time import sleep
import redis
from utils import score
import ast, select

def interact_with_user(player_cards):
    """ All interaction with user must be done through this method.
    YOU CANNOT CHANGE THIS METHOD. """

    print(f"\nCurrent cards: {player_cards}")
    print("(H)it")
    print("(S)tand")
    print("(W)in")  # Claim victory
    print("(D)efeat")  # Fold in defeat
    print("(L)ie about winning")  # Lie about winning
    print("(C)heat with an extra card")  # Draw an extra card
    print("lie about (P)oints")
    key = " "
    while key not in "HSWDLCP":
        key = input("> ").upper()
    return key.upper()


def main(self_port, players_ports):
    """ Main function of the player. """
    print("Connecting to other players...")
    connections = []
    self_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self_connection.bind(('localhost', self_port))
    self_connection.listen()
    selfconn = []

    for port in players_ports:
        if port == self_port:
            continue

        while True:
            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.connect(('localhost', port))
                connections.append(connection)
                print(f'Connected with player on port {port}')
                break
            except ConnectionRefusedError:
                print(f"Connection refused to {port}. Retrying...")
                sleep(1)
                continue

    # Wait until everyone is ready
    print("\nAll players connected. Starting the game.\n")
    # Aceitar conexões de outros jogadores
    for port in players_ports:
        if port == self_port:
            continue
        else:
            conn, addr = self_connection.accept()
            selfconn.append(conn)


    flag = False
    self_cards = []
    all_cards = {}
    #player status dic, key é id port, value == playing
    player_status = {}
    for port in players_ports:
        player_status[port] = 'playing'

    # Connect to Redis server
    redis_host = 'localhost'
    redis_port = 6379
    redis_client = redis.Redis(host=redis_host, port=redis_port)
    redis_client.delete(str(self_port))

    # Function to receive messages in my socket and print them
    def receive_message(connection):
        """ Receive message in self socket from others players"""
        while True:
                flag = False
                turn_index = 0
                # Receive message from the previous player
                data_size = connection.recv(2)
                if not data_size:
                    break
                message_size = int.from_bytes(data_size, byteorder='big')
                data = b""
                while len(data) < message_size:
                    chunk = connection.recv(min(message_size - len(data), 1024))
                    if not chunk:
                        break
                    data += chunk
                if b'Next Player' in data:
                    message = data.decode('utf-8').strip()

                    # Extrair os valores das variáveis da mensagem
                    next_player_port = message.split(';')[0].split(':')[1].strip()
                    self_port_anterior = message.split(';')[1].split(',')[0].split(':')[1].strip()
                    player_status_anterior = message.split(';')[1].split(',')[1].split(':')[1].strip()

                    # Atualizar o dicionário player_status com as informações recebidas
                    player_status[int(self_port_anterior)] = player_status_anterior
                    if str(self_port) == str(next_player_port):
                        turn_index = players_ports.index(self_port)
                        return turn_index, flag
                    else:
                        print(f"It's player {next_player_port}'s turn. Please wait.\n")
                        turn_index = players_ports.index(int(next_player_port))
                        return turn_index, flag

                elif b'who won' in data:
                    # Extrair os valores das variáveis da mensagem
                    message = data.decode('utf-8').strip()
                    self_port_anterior1 = message.split(';')[1].split(',')[0].split(':')[1].strip()
                    player_status_anterior1= message.split(';')[1].split(',')[1].split(':')[1].strip()

                    # Atualizar o dicionário player_status com as informações recebidas
                    player_status[int(self_port_anterior1)] = player_status_anterior1
                    flag = True
                    return turn_index, flag
                   #nao volta ao ciclo while e segue para o declare winner
                    
                elif data:
                    message = data.decode('utf-8').strip()
                    print(message)

    # Function to send data to other players in the game
    def send_message(connection, message):
        """ send message in self socket to others players"""

        message_size = len(message)
        message_size_bytes = message_size.to_bytes(2, byteorder='big')
        connection.sendall(message_size_bytes + message.encode('utf-8'))


    # Function to draw a card from the deck
    def draw_card():       
        """ Draw cards to players """

        deck_host = 'localhost'
        deck_port = 5000
        deck_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        deck_sock.connect((deck_host, deck_port))

        # Send request to deck.py to draw a card
        deck_sock.sendall(b"GC")

        # Receive the drawn card from deck.py
        card = deck_sock.recv(3).decode('utf-8').strip()

        print(f'You draw a card: {card}')

        deck_sock.close()

        return card

    # Function to get hash from deck
    def get_hash():
        deck_hash_host = 'localhost'
        deck_hash_port = 5000
        deck_hash_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        deck_hash_sock.connect((deck_hash_host, deck_hash_port))

        # Send request to deck_hash.py to draw a card
        deck_hash_sock.sendall(b"GH")

        # Receive the drawn card from deck_hash.py
        hash = deck_hash_sock.recv(64).decode('utf-8').strip()

        deck_hash_sock.close()

        return hash

    # Draw cards for each player
    num_players = len(players_ports) 
    num_cards = num_players * 2
    for _ in range(2):
        card = draw_card()
        self_cards.append(card)
        all_cards[self_port] = self_cards

    print(f"Your cards: {self_cards}")
    redis_client.set(str(self_port), str(self_cards))
    sleep(0.7)

    print('\nAll Players have first cards\n')

    def declare_winner(players_status):
        """Declare the winner of the game"""
        print("\nGame over, looking for the winner...")
        
        winner = None
        
        # Verificar se algum jogador disse que ganhou
        for port, data in players_status.items():
            status = data['status']
            score = data['score']
            if status == 'won':
                # Verificar se esse jogador tem 21 pontos ou é o único jogador com status != 'lost'
                if score == 21 or len([p for p, d in players_status.items() if d['status'] != 'lost']) == 1:
                    winner = port  # Guardar a porta do jogador vencedor
                    
                else:
                    print(f"Player {port} is a cheater, said he won, but he doesn't meet the requirements to win.")
                    
        
        if winner is not None:
            print(f"Player {winner} won the game.\n")
            return winner
        
        cheaters = [p for p, d in players_status.items() if d['score'] > 21 and d['status'] != 'lost']
        if cheaters:
            print(f"Cheater(s) detected: {cheaters}")
        else:
            # Verificar se todos os jogadores têm status 'lost' ou 'stand'
            players_without_playing = [p for p, d in players_status.items() if d['status'] != 'playing']
            if len(players_without_playing) == len(players_status):
                # Encontrar o vencedor com base nos critérios mencionados

                if all(d['status'] == 'stand' for _, d in players_status.items()):
                    # Encontrar o jogador com a maior pontuação menor ou igual a 21
                    valid_scores = [d['score'] for _, d in players_status.items() if d['score'] <= 21]
                    max_score = max(valid_scores) if valid_scores else 0
                    players_stand = [p for p, d in players_status.items() if d['status'] == 'stand' and d['score'] == max_score]

                    if len(players_stand) == 1:
                        winner = players_stand[0]
                    else:
                        # Verificar se há cheaters com pontuação superior a 21
                        cheaters = [p for p, d in players_status.items() if d['score'] > 21]
                        if cheaters:
                            print(f"Cheater(s) detected: {cheaters}")
                        else:
                            print(f"Players {players_stand} tied with {max_score} points.")
                            


        if winner is not None:
            print(f"Player {winner} won the game.\n")
            return winner
        
        return None  # Retorna None se nenhum vencedor for encontrado

    # Play the game

    turn_index = players_ports.index(min(players_ports))

    while True:
        if turn_index == players_ports.index(self_port):
            print("It's your turn. Please make your move.\n")
            # ve se o player ja começa com 21 pontos
            if player_status[self_port] =="playing" or player_status[self_port] == 'stand':
                
                action = interact_with_user(self_cards)
                #cheat lying about points
                if action == "P":
                #cheat lying about points
                    total_score = score(self_cards)
                    print(f"You are a cheater, you have {total_score} points!")
                    player_status[self_port] = "stand"
                    redis_client.set(str(self_port), str(self_cards))


                # cheat with extra card C
                if action == "C":
                    # Draw a card
                    card = draw_card()
                    self_cards.append(card)
                    total_score = score(self_cards)
                    #envia mensagem a dizer que pediu carta
                    player_status[self_port] = "playing"
                    # ultrupasssa o score
                    redis_client.set(str(self_port), str(self_cards))

                    if total_score > 21:
                        print("You have more than 21 points, but you are a cheater!")
                        print("You still playing, if you want give up!")
                        #coloca as cartas na mesa, key = port id, value lista com as cartas
                    # tem 21 pontos
                    elif total_score == 21:
                        redis_client.set(str(self_port), str(self_cards))
                        print("You have 21 points!")
                        for connection in connections:
                            send_message(connection, f"Player {self_port} have 21 points.")

                if action == "L":
                    print("You claimed victory.")
                    for connection in connections:
                        send_message(connection, f"Player {self_port} claimed victory\n")
                    player_status[self_port] = "won"
                    redis_client.set(str(self_port), str(self_cards))
                    for connection in connections:
                        send_message(connection, f"who won; port_player anterior: {self_port}, player_status_anterior:{player_status[self_port]}")
                    break


                if action == "H":
                    # Draw a card
                    card = draw_card()
                    self_cards.append(card)
                    total_score = score(self_cards)
                    #envia mensagem a dizer que pediu carta
                    for connection in connections:
                        send_message(connection, f"Player {self_port} draw another card")
                    player_status[self_port] = "playing"
                    # ultrupasssa o score
                    if total_score > 21:
                        print("Bust! You lost.")
                        for connection in connections:
                            send_message(connection, f"Player {self_port} lost")
                        # Cannot play anymore, but wait to determine the winner
                        player_status[self_port] = "lost"
                        #coloca as cartas na mesa, key = port id, value lista com as cartas
                        redis_client.set(str(self_port), str(self_cards))
                    # tem 21 pontos
                    elif total_score == 21:
                        redis_client.set(str(self_port), str(self_cards))
                        print("You have 21 points!")
                        for connection in connections:
                            send_message(connection, f"Player {self_port} have 21 points.")

                #stand  
                elif action == "S":
                    # Senvia a mensagem e guarda a variavel a dizer que fica
                    print("You chose to stand.")
                    for connection in connections:
                        send_message(connection, f"Player {self_port} stood")
                    player_status[self_port] = "stand"
                    #coloca as cartas na mesa, key = port id, value lista com as cartas
                    redis_client.set(str(self_port), str(self_cards))

                elif action == "W":
                    # Claim victory
                    print("You claimed victory.")
                    for connection in connections:
                        send_message(connection, f"Player {self_port} claimed victory\n")
                    player_status[self_port] = "won"
                    # coloca as cartas no redis
                    redis_client.set(str(self_port), str(self_cards))
                    # envia mensagem para averiguar pontos e sai ciclo while
                    for connection in connections:
                        send_message(connection, f"who won; port_player anterior: {self_port}, player_status_anterior:{player_status[self_port]}")
                    break

                elif action == "D":
                    # Fold in defeat
                    print("You folded in defeat.")
                    for connection in connections:
                        send_message(connection, f"Player {self_port} folded in defeat")
                    player_status[self_port] = "lost"

                    #coloca as cartas na mesa, key = port id, value lista com as cartas
                    redis_client.set(str(self_port), str(self_cards))
                    print("You cannot play anymore, but wait to determine the winner.")

                active_players = [player for player in player_status if player_status[player] == 'playing']
                if len(active_players) == 0:    
                    for connection in connections:
                        send_message(connection, f"who won; port_player anterior: {self_port}, player_status_anterior:{player_status[self_port]}")
                    break

                turn_index = (players_ports.index(self_port) + 1) % len(players_ports)
                next_player_port = players_ports[turn_index]

                for conn in connections:
                    send_message(conn, f"Next Player: {next_player_port}; port_player anterior: {self_port}, player_status_anterior:{player_status[self_port]}")
                

            elif player_status[self_port] == "lost":
                # No caso dos satus de todos os jogadores serem != playing
                # envia mensagem para averiguar pontos e sai ciclo while
                active_players = [player for player in player_status if player_status[player] == 'playing']
                if len(active_players) == 0:    
                    for connection in connections:
                        send_message(connection, f"who won; port_player anterior: {self_port}, player_status_anterior:{player_status[self_port]}")
                    break
                else:
                    turn_index = (players_ports.index(self_port) + 1) % len(players_ports)
                    next_player_port = players_ports[turn_index]

                    for conn in connections:
                        send_message(conn, f"Next Player: {next_player_port};  port_player anterior: {self_port}, player_status_anterior: {player_status[self_port]}")
    
                    

        else:
            # Wait for other players' turns
            print("\nWaiting for other player...")    
            your_turn = False  
            while not your_turn:
                # Prepare a lista de conexões para select
                read_sockets = [self_connection] + selfconn

                # Use select para esperar por eventos de leitura nas conexões
                readable, _, _ = select.select(read_sockets, [], [])

                # Processar mensagens recebidas nas conexões
                for sock in readable:
                    if sock is self_connection:
                        # Receber conexões entrantes
                        connection, address = self_connection.accept()
                        selfconn.append(connection)
                    else:
                        # Receber mensagem de uma conexão existente
                        turn_index, flag = receive_message(sock)
                        if turn_index == players_ports.index(self_port) or flag == True:
                            your_turn = True
                            break
                      
            
            if flag:
                break
            sleep(1)

    sleep(3)

    # Close connections
    self_connection.close()
    for connection in connections:
        connection.close()

    for port, status in player_status.items():
        player_score = score(ast.literal_eval(redis_client.get(str(port)).decode('utf-8')))
        # Adicionar além do status que já existe o score ao player_status
        player_status[port] = {'status': status, 'score': player_score}
    declare_winner(player_status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--self", type=int, help="The port number of this player")
    parser.add_argument("-p", "--players", nargs="+", type=int, help="The port numbers of all players")
    args = parser.parse_args()
    if args.self in args.players:
        print(f"{args.self} must not be part of the list of players")
        exit(1) 

    if args.self is None or args.players is None:
        parser.print_help()
    else:
        players_ports = sorted([args.self] + args.players)
        main(args.self, players_ports)