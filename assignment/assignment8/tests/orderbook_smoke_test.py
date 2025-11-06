# tests/orderbook_test.py
import socket
import threading
import time
from multiprocessing import Process

from src.orderbook import run_orderbook
from src.shared_memory_utils import SharedPriceBook

HOST = "localhost"
PORT = 9010
SHM_NAME = "pricebook_test"


def _mock_gateway(host: str, port: int, messages: list[bytes], interval: float = 0.05):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    conn, _ = srv.accept()
    try:
        for m in messages:
            conn.sendall(m)
            time.sleep(interval)
    finally:
        try: conn.close()
        except Exception: pass
        srv.close()


def _cleanup_shm(name: str):
    try:
        shm = SharedPriceBook(name=name, create=False)
        shm.close()
        shm.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


if __name__ == "__main__":
    _cleanup_shm(SHM_NAME)

    msgs = [
        b"AAPL,101.25*MSFT,275.10*",
        b"SENTIMENT,45*",
        b"GOOG,300.00*AAPL,102.75*",
    ]

    t = threading.Thread(target=_mock_gateway, args=(HOST, PORT, msgs), daemon=True)
    t.start()

    p = Process(target=run_orderbook, kwargs={"host": HOST, "port": PORT, "shm_name": SHM_NAME})
    p.start()

    time.sleep(0.6)

    reader = SharedPriceBook(name=SHM_NAME, create=False)
    data = reader.read()
    print(f"[Test] SHM: {data}")

    ok = (
        isinstance(data.get("AAPL"), float)
        and isinstance(data.get("MSFT"), float)
        and isinstance(data.get("GOOG"), float)
        and "SENTIMENT" not in data
    )
    print("OrderBook Test passed" if ok else "OrderBook Test failed")

    try: reader.close()
    except Exception: pass

    try:
        p.terminate()
        p.join(timeout=2)
    except Exception:
        pass

    _cleanup_shm(SHM_NAME)
    t.join(timeout=1.0)
