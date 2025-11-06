from src.shared_memory_utils import SharedPriceBook

# Create new shared memory block
book = SharedPriceBook(create=True)
book.update('AAPL', 173.5)
book.update('MSFT', 322.1)

data = book.read()
print(f'Data after updates: {data}')

# Simulate another process reading same mem
other = SharedPriceBook(create=False)
print(f'Other process sees: {other.read()}')

# Basic check
if data == other.read():
    print('Test passed')
else:
    print('Test failed')

book.close()
book.unlink()
other.close()