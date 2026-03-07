import customtkinter as ctk

from shared.config import BG_COLOR
from client.network import NetworkMixin
from client.ui.login import LoginMixin
from client.ui.sidebar import SidebarMixin
from client.ui.chat_area import ChatAreaMixin
from client.ui.bubbles import BubblesMixin

# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ChatApp(ctk.CTk, NetworkMixin, LoginMixin, SidebarMixin, ChatAreaMixin, BubblesMixin):
    def __init__(self):
        super().__init__()
        self.title("AI Network ChatRoom")
        
        # Center window (slightly higher)
        w, h = 1000, 650
        x = int((self.winfo_screenwidth() - w) / 2)
        y = int((self.winfo_screenheight() - h) / 2) - 50
        if y < 0: y = 0
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(fg_color=BG_COLOR)

        # Network State
        self.host = '127.0.0.1'
        self.port = 5000
        self.client_socket = None
        self.username = ""

        # UI State
        self.online_users  = []        # list of online usernames
        self.dm_tabs       = {}        # { username: { frame, chat_display, chat_row } }
        self.active_tab    = "group"   # "group" or a username string
        self.unread_dms    = {}        # { username: count }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.show_login_frame()
