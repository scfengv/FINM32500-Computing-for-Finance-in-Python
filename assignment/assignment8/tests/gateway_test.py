# Unit test: just run gateway.py then this file
import socket
import re

HOST = "localhost"
PORT = 9000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print('Connected to Gateway')

# Read message
data = client.recv(4096)
msg = data.decode().strip()
print(f'Received: {msg}')

# Check message formatting
has_price = re.search(r"AAPL,\d+\.\d+", msg)
has_sentiment = 'SENTIMENT' in msg
if has_price and has_sentiment and msg.endswith('*'):
    print('Test passed')
else:
    print('Test failed')

client.close()