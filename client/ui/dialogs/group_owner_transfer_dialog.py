import customtkinter as ctk

from client.ui.popup_utils import bring_popup_to_front


class GroupOwnerTransferDialog(ctk.CTkToplevel):
    def __init__(self, parent, members: list[str], my_username: str, on_confirm) -> None:
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.selected_user = ctk.StringVar()
        self.eligible_users = [username for username in members if username != my_username]

        self.title("โอนสิทธิ์เจ้าของกลุ่ม")
        self.geometry("340x440")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#1A1D2E")

        self.update_idletasks()
        pos_x = parent.winfo_x() + (parent.winfo_width() // 2) - 170
        pos_y = parent.winfo_y() + (parent.winfo_height() // 2) - 220
        self.geometry(f"+{pos_x}+{pos_y}")
        bring_popup_to_front(self, parent, keep_on_top=True)

        ctk.CTkLabel(
            self,
            text="โอนสิทธิ์เจ้าของช่องแชท",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFD700",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="เลือกสมาชิกที่จะเป็นเจ้าของช่องแชทคนใหม่",
            font=ctk.CTkFont(size=11),
            text_color="#6B728E",
        ).pack(pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F1120",
            corner_radius=10,
            height=220,
            width=280,
        )
        scroll.pack(padx=28, pady=(4, 20))
        scroll.grid_columnconfigure(0, weight=1)

        if not self.eligible_users:
            ctk.CTkLabel(
                scroll,
                text="ไม่มีสมาชิกคนอื่นในกลุ่ม",
                text_color="#6B728E",
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=0, pady=20)
        else:
            for index, username in enumerate(self.eligible_users):
                ctk.CTkRadioButton(
                    scroll,
                    text=f" {username}",
                    variable=self.selected_user,
                    value=username,
                    font=ctk.CTkFont(size=13),
                    fg_color="#FFD700",
                    hover_color="#B8860B",
                    text_color="white",
                ).grid(row=index, column=0, sticky="w", padx=10, pady=8)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        ctk.CTkButton(
            button_frame,
            text="ยกเลิก",
            width=110,
            height=36,
            fg_color="#2A2E44",
            hover_color="#3A3E54",
            corner_radius=18,
            command=self.destroy,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            button_frame,
            text="ยืนยัน",
            width=130,
            height=36,
            fg_color="#FFD700",
            hover_color="#B8860B",
            text_color="#1A1D2E",
            corner_radius=18,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._confirm,
        ).pack(side="left", padx=8)

    def _confirm(self) -> None:
        new_owner = self.selected_user.get()
        if not new_owner:
            return

        self.destroy()
        self.on_confirm(new_owner)
