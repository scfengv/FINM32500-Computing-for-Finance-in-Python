import socket
import random
import time
from typing import List

HOST = "localhost"
PORT = 9000
TICKERS = ["AAPL", "MSFT", "GOOG"]
SLEEP_SECONDS = 0.5


def _accept_new_clients(server_sock: socket.socket, clients: List[socket.socket]):
    """
    Accept all pending connections without blocking the publisher loop.
    """
    while True:
        try:
            conn, addr = server_sock.accept()
        except BlockingIOError:
            break

        conn.setblocking(True)  # keep client sockets blocking for sendall
        clients.append(conn)
        print(f"Gateway: client connected from {addr} (total clients: {len(clients)})")


def _broadcast(msg: bytes, clients: List[socket.socket]):
    """
    Send the given message to every connected client.
    Drops clients that disconnect or error out.
    """
    stale = []

    for conn in clients:
        try:
            conn.sendall(msg)
        except OSError as exc:
            peer = None
            try:
                peer = conn.getpeername()
            except OSError:
                peer = "unknown"
            print(f"Gateway: dropping client {peer}: {exc}")
            stale.append(conn)

    for dead in stale:
        try:
            dead.close()
        except OSError:
            pass
        clients.remove(dead)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    server.setblocking(False)

    print(f"Gateway TCP server running on {HOST}:{PORT}")
    print("Gateway waiting for client connections")

    clients: List[socket.socket] = []
    prices = {tk: 100.0 + random.random() * 5 for tk in TICKERS}

    try:
        while True:
            # Pick up any new OrderBook / Strategy clients
            _accept_new_clients(server, clients)

            # If no clients are connected yet, back off a little
            if not clients:
                time.sleep(0.1)
                continue

            # Update random-walk prices and sentiment
            for tk in TICKERS:
                prices[tk] = round(prices[tk] * (1 + random.uniform(-0.001, 0.001)), 2)
            news = random.randint(0, 100)

            price_str = "*".join(f"{tk},{p}" for tk, p in prices.items()) + "*"
            sentiment = f"SENTIMENT,{news}*"
            msg = (price_str + sentiment).encode("utf-8")

            _broadcast(msg, clients)
            print(f"Gateway sent ({len(clients)} clients): {msg.decode().strip()}")

            time.sleep(SLEEP_SECONDS)

    except KeyboardInterrupt:
        print("\nGateway shutting down...")
    finally:
        for conn in clients:
            try:
                conn.close()
            except OSError:
                pass
        server.close()


if __name__ == "__main__":
    main()
