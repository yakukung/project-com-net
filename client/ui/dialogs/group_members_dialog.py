import customtkinter as ctk
class GroupMembersDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        group_id: str,
        group_name: str,
        members: list[str],
        owner_name: str,
        my_username: str,
        on_kick,
        on_transfer,
        on_add,
    ) -> None:
        super().__init__(parent)
        self.group_id = group_id
        self.members = members
        self.on_kick = on_kick
        self.on_transfer = on_transfer
        self.on_add = on_add
        self.is_owner = my_username == owner_name

        self.title(f"สมาชิก - {group_name}")
        self.geometry("320x420")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#1A1D2E")

        self.update_idletasks()
        pos_x = parent.winfo_x() + (parent.winfo_width() // 2) - 160
        pos_y = parent.winfo_y() + (parent.winfo_height() // 2) - 210
        self.geometry(f"+{pos_x}+{pos_y}")

        ctk.CTkLabel(
            self,
            text=f"👥 {group_name}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF75D8",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text=f"{len(members)} สมาชิก | เจ้าของ: {owner_name}",
            font=ctk.CTkFont(size=11),
            text_color="#6B728E",
        ).pack(pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F1120",
            corner_radius=10,
            height=230,
            width=280,
        )
        scroll.pack(padx=20, pady=(0, 16))
        scroll.grid_columnconfigure(0, weight=1)

        for index, username in enumerate(members):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.grid(row=index, column=0, sticky="ew", padx=6, pady=3)
            row.grid_columnconfigure(0, weight=1)

            crown = " 👑" if username == owner_name else ""
            ctk.CTkLabel(
                row,
                text=f"● {username}{crown}",
                font=ctk.CTkFont(size=13),
                text_color="white",
                anchor="w",
            ).grid(row=0, column=0, sticky="w")

            if self.is_owner and username != my_username:
                ctk.CTkButton(
                    row,
                    text="เตะ",
                    width=50,
                    height=26,
                    fg_color="#B71C1C",
                    hover_color="#7F0000",
                    text_color="white",
                    corner_radius=8,
                    font=ctk.CTkFont(size=11),
                    command=lambda name=username: self._kick(name),
                ).grid(row=0, column=1, padx=(8, 0))

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 16))

        if self.is_owner:
            ctk.CTkButton(
                button_frame,
                text="เพิ่มสมาชิก",
                width=120,
                height=36,
                fg_color="#4CAF50",
                hover_color="#388E3C",
                text_color="white",
                corner_radius=18,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=self._add,
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                button_frame,
                text="เปลี่ยนเจ้าของช่องแชท",
                width=130,
                height=36,
                fg_color="#FFD700",
                hover_color="#B8860B",
                text_color="#1A1D2E",
                corner_radius=18,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=self._transfer,
            ).pack(side="left", padx=6)
        else:
            ctk.CTkButton(
                button_frame,
                text="ปิด",
                width=110,
                height=36,
                fg_color="#2A2E44",
                hover_color="#3A3E54",
                corner_radius=18,
                command=self.destroy,
            ).pack(side="left", padx=6)

    def _kick(self, username: str) -> None:
        self.destroy()
        self.on_kick(self.group_id, username)

    def _transfer(self) -> None:
        self.destroy()
        self.on_transfer(self.group_id, self.members)

    def _add(self) -> None:
        self.destroy()
        self.on_add(self.group_id, self.members)
