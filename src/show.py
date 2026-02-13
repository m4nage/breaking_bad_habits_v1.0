import socket
import sys

def trigger_show():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            s.sendall(b"SHOW")
            print("Signal sent: Dashboard should appear.")
    except ConnectionRefusedError:
        print("Error: The main application is not running.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    trigger_show()