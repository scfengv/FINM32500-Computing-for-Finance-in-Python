# src/orderbook.py
import socket
import time
from typing import Optional

try:
    from .shared_memory_utils import SharedPriceBook
except ImportError:
    from shared_memory_utils import SharedPriceBook

HOST = "localhost"
PORT = 9000
MESSAGE_DELIMITER = b"*"
RECONNECT_BASE = 0.5
RECONNECT_MAX = 5.0
SOCKET_TIMEOUT = 5.0


def _connect(host: str, port: int) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(SOCKET_TIMEOUT)
    s.connect((host, port))
    s.settimeout(None)
    return s


def _iter_messages(sock: socket.socket):
    # Yield delimiter-terminated messages
    buf = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionResetError("Gateway closed")
        buf.extend(chunk)
        while True:
            i = buf.find(MESSAGE_DELIMITER)
            if i == -1:
                break
            raw = bytes(buf[:i])
            del buf[: i + 1]
            if raw:
                yield raw.decode("utf-8", "replace")


def _parse_price(msg: str) -> Optional[tuple[str, float]]:
    # Accept "SYM,123.45"; ignore "SENTIMENT,NN"
    parts = msg.split(",")
    if len(parts) < 2 or parts[0].strip().upper() == "SENTIMENT":
        return None
    try:
        return parts[0].strip(), float(parts[1])
    except ValueError:
        return None


def run_orderbook(host: str = HOST, port: int = PORT, shm_name: str = "pricebook"):
    # Create or attach SHM
    try:
        book = SharedPriceBook(name=shm_name, create=True)
        print(f"OrderBook: created shm '{shm_name}'")
    except FileExistsError:
        book = SharedPriceBook(name=shm_name, create=False)
        print(f"OrderBook: attached shm '{shm_name}'")

    sock = None
    backoff = RECONNECT_BASE

    try:
        while True:
            try:
                if sock is None:
                    print(f"OrderBook: connecting {host}:{port} ...")
                    sock = _connect(host, port)
                    print("OrderBook: connected")
                    backoff = RECONNECT_BASE

                for raw in _iter_messages(sock):
                    p = _parse_price(raw)
                    if p is None:
                        continue
                    sym, px = p
                    book.update(sym, px)
                    print(f"OrderBook: {sym} -> {px}")

                # Generator ended → treat as disconnect
                raise ConnectionResetError("Stream ended")

            except (ConnectionRefusedError, ConnectionResetError, socket.timeout, OSError) as e:
                if sock:
                    try: sock.close()
                    except Exception: pass
                    sock = None
                print(f"OrderBook: reconnect in {backoff:.1f}s ({e})")
                time.sleep(backoff)
                backoff = min(RECONNECT_MAX, backoff * 1.5)
    except KeyboardInterrupt:
        print("OrderBook: shutdown")
    finally:
        try:
            if sock: sock.close()
        except Exception:
            pass
        try:
            book.close()  # do not unlink; other processes may use it
        except Exception:
            pass


if __name__ == "__main__":
    run_orderbook()
