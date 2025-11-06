from multiprocessing import shared_memory
import pickle

class SharedPriceBook:
    def __init__(self, name='pricebook', create=True):
        self.name = name
        self.size = 4096  # small block of memory
        if create:  # If first, create shared memory block
            self.shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.size)
            self.write({})
        else:
            self.shm = shared_memory.SharedMemory(name=self.name)

    def write(self, data): # Write dictionary {ticker: price}
        encoded = pickle.dumps(data)
        self.shm.buf[:len(encoded)] = encoded
        self.shm.buf[len(encoded):] = b'\x00' * (self.size - len(encoded))

    def read(self): # Read dict
        raw = bytes(self.shm.buf).split(b'\x00', 1)[0]
        if not raw:
            return {}
        return pickle.loads(raw)

    def update(self, ticker, price): # Update a ticker
        data = self.read()
        data[ticker] = price
        self.write(data)

    def read_tick(self, ticker): # Read ticker
        return self.read().get(ticker)

    def close(self):
        self.shm.close()

    def unlink(self): # Free shared mem
        self.shm.unlink()