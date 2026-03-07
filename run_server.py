import sys
import os

# Ensure the root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.main import start_server

if __name__ == "__main__":
    start_server()
