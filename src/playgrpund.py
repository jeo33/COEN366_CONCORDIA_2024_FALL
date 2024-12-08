import socket
import time

def start_client():
    """Connect to the server and send messages."""
    server_address = ('localhost', 9929)

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server_address)
        print(f"Connected to server as RQ_number {1}")

        while 1:  # Send 5 messages
            message = f"333"
            client_socket.sendto(message.encode(),server_address)
            print(f"Sent: {message}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_client()
