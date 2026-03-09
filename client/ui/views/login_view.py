import customtkinter as ctk

from client.ui.theme import (    BG_COLOR,
    BORDER_COLOR,
    INPUT_BG,
    PANEL_BG,
    PRIMARY_BTN,
    PRIMARY_BTN_HOVER,
    TEXT_MUTED,
)
from shared.network_constants import DEFAULT_CLIENT_HOST


class LoginViewMixin:
    def show_login_frame(self) -> None:
        self.login_bg = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.login_bg.grid(row=0, column=0, sticky="nsew")
        self.login_bg.grid_columnconfigure(0, weight=1)
        self.login_bg.grid_rowconfigure(0, weight=1)

        self.login_card = ctk.CTkFrame(
            self.login_bg,
            fg_color=PANEL_BG,
            width=400,
            height=450,
            corner_radius=25,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.login_card.grid(row=0, column=0, padx=40, pady=40)
        self.login_card.grid_propagate(False)
        self.login_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.login_card,
            text="✨ AI NETWORK",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=PRIMARY_BTN,
        ).grid(row=0, column=0, pady=(40, 5))

        ctk.CTkLabel(
            self.login_card,
            text="ระบบแชทเรียลไทม์แห่งอนาคต",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, pady=(0, 25))

        ctk.CTkLabel(
            self.login_card,
            text="ชื่อผู้ใช้",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
        ).grid(row=2, column=0, sticky="w", padx=50, pady=(10, 0))
        self.username_entry = ctk.CTkEntry(
            self.login_card,
            placeholder_text="เช่น CyberPunk",
            width=300,
            height=45,
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=14),
        )
        self.username_entry.grid(row=3, column=0, padx=50, pady=(5, 15))

        ctk.CTkLabel(
            self.login_card,
            text="ที่อยู่เซิร์ฟเวอร์",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
        ).grid(row=4, column=0, sticky="w", padx=50, pady=(10, 0))
        self.host_entry = ctk.CTkEntry(
            self.login_card,
            placeholder_text=DEFAULT_CLIENT_HOST,
            width=300,
            height=45,
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=14),
        )
        self.host_entry.insert(0, DEFAULT_CLIENT_HOST)
        self.host_entry.grid(row=5, column=0, padx=50, pady=(5, 30))

        self.connect_btn = ctk.CTkButton(
            self.login_card,
            text="เข้าสู่ห้องแชท 🚀",
            command=self.connect_to_server,
            width=300,
            height=50,
            fg_color=PRIMARY_BTN,
            hover_color=PRIMARY_BTN_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=15,
            text_color="white",
        )
        self.connect_btn.grid(row=6, column=0, padx=50, pady=(0, 40))

        self.bind("<Return>", lambda _event: self.connect_to_server())
        self.username_entry.focus()
