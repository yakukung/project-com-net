import sys
from client.app import ChatApp

def start_client():
    app = ChatApp()
    app.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    app.mainloop()

if __name__ == "__main__":
    start_client()
