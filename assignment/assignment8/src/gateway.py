import socket
import random
import time

HOST = "localhost"
PORT = 9000
ticks = ['AAPL', 'MSFT', 'GOOG']

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print(f'Gateway TCP server running on {HOST}:{PORT}')
print('Gateway waiting for client connection')

conn, addr = server.accept()
print(f'Gateway Connected by {addr}')

prices = {tk: 100.0 + random.random() * 5 for tk in ticks}

while True:
    for tk in ticks:
        prices[tk] = round(prices[tk] * (1 + random.uniform(-0.001, 0.001)), 2)
    news = random.randint(0, 100)

    price_str = '*'.join([f'{tk},{p}' for tk, p in prices.items()]) + '*'
    sentiment = f'SENTIMENT,{news}*'
    msg = (price_str + sentiment).encode('utf-8')
    conn.sendall(msg)
    print('Gateway sent:', msg.decode().strip())
    time.sleep(0.5)