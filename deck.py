import socket
import random
import argparse
import hashlib
from time import sleep
from utils import CARDS


def main():
    played_cards = []
    checkers = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', 5000))
    sock.listen(1)
    try:
        while True:
            conn, addr = sock.accept()
            data = conn.recv(2).decode('utf-8')
            print(f">{data}<")
            if "GC"in data:
                card = random.choice(CARDS)
                print(f"Draw: {card}")
                played_cards.append(card)
                conn.sendall(f'{card.rjust(2)}\n'.encode('utf-8'))
            elif "HC"in data and checkers < 2:
                played_hash = hashlib.md5(f'{played_cards}'.encode('utf-8')).hexdigest()
                print(f'{played_cards} -> {played_hash}') 
                conn.sendall(f'{played_hash}\n'.encode('utf-8'))
                checkers+=1
            else:
                conn.sendall(f"BAD COMMAND".encode('utf-8'))
            sleep(1)
            conn.close()
    except Exception as err:
        print(err)
    
    sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    main()
    
