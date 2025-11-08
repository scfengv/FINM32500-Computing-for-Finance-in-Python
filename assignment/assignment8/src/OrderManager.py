import socket
import json
import threading

# Order Manager TCP Connection deets
HOST = "localhost"
PORT = 9001
MESSAGE_DELIMITER = b"*"

def handle_client(conn, addr):
    """
    Handles a Strategy client connection

    Reads a continuous TCP byte stream from the connected client,
    splits it into individual order messages using MESSAGE_DELIMITER,
    deserializes each JSON-encoded order, and logs the trade

    Args:
        conn (socket.socket): the client socket wwe accept
        addr (tuple): (host, port) address of the connected client
    """
    print(f"OrderManager: connected by {addr}")
    buf = bytearray()
    with conn:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            while True:
                i = buf.find(MESSAGE_DELIMITER)
                if i == -1:
                    break
                raw = bytes(buf[:i])
                del buf[:i+1]
                if not raw:
                    continue
                try:
                    order = json.loads(raw.decode("utf-8"))
                    print(f"Received Order: {order['action']} {order['ticker']} @ {order['price']:.2f} ({order['reason']})")
                except Exception as e:
                    print("OrderManager: bad message:", raw, e)

def run_ordermanager():
    """
    Start the OrderManager TCP server
    Binds a listening socket on (HOST, PORT) and accepts incoming
    Strategy connections. Thenf or each, delegates all message
    handling to handle_client() function above. Will run indefinitely until the process
    is terminated
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"OrderManager listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    run_ordermanager()
