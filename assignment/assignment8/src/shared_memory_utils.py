from multiprocessing import shared_memory
import pickle
import struct

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
        data_len = len(encoded)
        if data_len + 4 > self.size:  # 4 bytes for length prefix
            raise ValueError(f"Data too large: {data_len} bytes > {self.size - 4} bytes")
        
        # Write length prefix (4 bytes)
        length_bytes = struct.pack('I', data_len)
        for i in range(4):
            self.shm.buf[i] = length_bytes[i]
        
        # Write the encoded data
        for i, byte in enumerate(encoded):
            self.shm.buf[4 + i] = byte

    def read(self): # Read dict
        # Read length prefix
        length_bytes = bytes(self.shm.buf[0:4])
        data_len = struct.unpack('I', length_bytes)[0]
        
        if data_len == 0:
            return {}
        
        if data_len > self.size - 4:
            return {}  # Corrupted data
        
        # Read the actual data
        raw = bytes(self.shm.buf[4:4 + data_len])
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