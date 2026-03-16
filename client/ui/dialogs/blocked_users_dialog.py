from tkinter import messagebox

import customtkinter as ctk

from client.ui.popup_utils import bring_popup_to_front
from client.ui.theme import BORDER_COLOR, TEXT_MUTED


class BlockedUsersDialog(ctk.CTkToplevel):
    def __init__(self, parent, blocked_users: list[str], on_unblock) -> None:
        super().__init__(parent)
        self.on_unblock = on_unblock
        self.blocked_users = list(blocked_users)
        self.rows: dict[str, ctk.CTkFrame] = {}

        dialog_width = 380
        dialog_height = 520
        self.title("รายการบล็อค")
        self.geometry(f"{dialog_width}x{dialog_height}")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#1A1D2E")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.update_idletasks()
        pos_x = parent.winfo_x() + (parent.winfo_width() // 2) - (dialog_width // 2)
        pos_y = parent.winfo_y() + (parent.winfo_height() // 2) - (dialog_height // 2)
        self.geometry(f"+{pos_x}+{pos_y}")
        bring_popup_to_front(self, parent, keep_on_top=True)

        ctk.CTkLabel(
            self,
            text="🚫 ผู้ใช้ที่บล็อค",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF9AA8",
        ).grid(row=0, column=0, pady=(20, 4))

        self.count_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self.count_label.grid(row=1, column=0, pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F1120",
            corner_radius=10,
            height=320,
            width=330,
        )
        self.list_frame.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="ยังไม่มีผู้ใช้ที่ถูกบล็อค",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )

        self._render_rows()

        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 10),
        )

        ctk.CTkButton(
            self,
            text="ปิด",
            width=110,
            height=36,
            fg_color="#2A2E44",
            hover_color="#3A3E54",
            corner_radius=18,
            command=self.destroy,
        ).grid(row=4, column=0, pady=(0, 14))

    def _render_rows(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        self.rows.clear()

        if not self.blocked_users:
            self.empty_label = ctk.CTkLabel(
                self.list_frame,
                text="ยังไม่มีผู้ใช้ที่ถูกบล็อค",
                font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED,
            )
            self.empty_label.grid(row=0, column=0, pady=20)
        else:
            for index, username in enumerate(self.blocked_users):
                row = ctk.CTkFrame(
                    self.list_frame,
                    fg_color="transparent",
                    border_width=1,
                    border_color=BORDER_COLOR,
                    corner_radius=8,
                )
                row.grid(row=index, column=0, sticky="ew", padx=6, pady=4)
                row.grid_columnconfigure(0, weight=1)
                self.rows[username] = row

                ctk.CTkLabel(
                    row,
                    text=f"● {username}",
                    font=ctk.CTkFont(size=13),
                    text_color="white",
                    anchor="w",
                ).grid(row=0, column=0, sticky="w", padx=10, pady=8)

                ctk.CTkButton(
                    row,
                    text="เลิกบล็อค",
                    width=80,
                    height=28,
                    fg_color="#26573A",
                    hover_color="#2E6E48",
                    text_color="#B8F7CF",
                    corner_radius=10,
                    font=ctk.CTkFont(size=11),
                    command=lambda name=username: self._on_click_unblock(name),
                ).grid(row=0, column=1, padx=8, pady=8)

        self.count_label.configure(text=f"ทั้งหมด {len(self.blocked_users)} คน")

    def _on_click_unblock(self, username: str) -> None:
        if not messagebox.askyesno("ยืนยัน", f"เลิกบล็อค '{username}' หรือไม่?", parent=self):
            return

        self.on_unblock(username)
        self.blocked_users = [name for name in self.blocked_users if name != username]
        self._render_rows()
