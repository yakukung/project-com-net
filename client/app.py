import customtkinter as ctk

from client.handlers.socket_handler import SocketHandlerMixin
from client.state.chat_state import initialize_client_state
from client.ui.components.chat_bubbles import ChatBubblesComponentMixin
from client.ui.theme import BG_COLOR
from client.ui.views.chat_area_view import ChatAreaViewMixin
from client.ui.views.login_view import LoginViewMixin
from client.ui.views.sidebar_view import SidebarViewMixin

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class ChatApplication(
    ctk.CTk,
    SocketHandlerMixin,
    LoginViewMixin,
    SidebarViewMixin,
    ChatAreaViewMixin,
    ChatBubblesComponentMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Network ChatRoom")

        width, height = 1000, 650
        pos_x = int((self.winfo_screenwidth() - width) / 2)
        pos_y = int((self.winfo_screenheight() - height) / 2) - 50
        self.geometry(f"{width}x{height}+{pos_x}+{max(pos_y, 0)}")
        self.configure(fg_color=BG_COLOR)

        initialize_client_state(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.show_login_frame()


# Backward-compatible alias
ChatApp = ChatApplication


def start_client() -> None:
    app = ChatApplication()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()
