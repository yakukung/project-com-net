import customtkinter as ctk
class GroupCreateDialog(ctk.CTkToplevel):
    def __init__(self, parent, online_users: list[str], on_confirm) -> None:
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.selected = {}

        self.title("สร้างช่องแชทใหม่")
        self.geometry("360x520")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#1A1D2E")

        self.update_idletasks()
        pos_x = parent.winfo_x() + (parent.winfo_width() // 2) - 180
        pos_y = parent.winfo_y() + (parent.winfo_height() // 2) - 220
        self.geometry(f"+{pos_x}+{pos_y}")

        ctk.CTkLabel(
            self,
            text="สร้างช่องแชทใหม่",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF75D8",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="ตั้งชื่อช่องแชทและเลือกสมาชิก",
            font=ctk.CTkFont(size=11),
            text_color="#6B728E",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            self,
            text="ชื่อช่องแชท",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A0A8CC",
        ).pack(anchor="w", padx=28)

        self.name_entry = ctk.CTkEntry(
            self,
            width=300,
            height=38,
            placeholder_text="เช่น ทีมงาน, Friends",
            fg_color="#0F1120",
            border_color="#2A2E44",
            font=ctk.CTkFont(size=13),
        )
        self.name_entry.pack(pady=(4, 16), padx=28)

        ctk.CTkLabel(
            self,
            text="เลือกสมาชิก",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A0A8CC",
        ).pack(anchor="w", padx=28)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F1120",
            corner_radius=10,
            height=150,
            width=300,
        )
        scroll.pack(padx=28, pady=(4, 20))
        scroll.grid_columnconfigure(0, weight=1)

        if not online_users:
            ctk.CTkLabel(
                scroll,
                text="ไม่มีผู้ใช้ออนไลน์อื่น",
                text_color="#6B728E",
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=0, pady=20)
        else:
            for index, username in enumerate(online_users):
                value = ctk.BooleanVar(value=False)
                self.selected[username] = value
                checkbox = ctk.CTkCheckBox(
                    scroll,
                    text=f"● {username}",
                    variable=value,
                    font=ctk.CTkFont(size=13),
                    fg_color="#FF75D8",
                    hover_color="#C2185B",
                    text_color="white",
                    checkmark_color="white",
                )
                checkbox.grid(row=index, column=0, sticky="w", padx=10, pady=4)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        ctk.CTkButton(
            button_frame,
            text="ยกเลิก",
            width=120,
            height=36,
            fg_color="#2A2E44",
            hover_color="#3A3E54",
            corner_radius=18,
            command=self.destroy,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            button_frame,
            text="สร้างช่องแชท",
            width=140,
            height=36,
            fg_color="#FF75D8",
            hover_color="#C2185B",
            text_color="white",
            corner_radius=18,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._confirm,
        ).pack(side="left", padx=8)

    def _confirm(self) -> None:
        from shared.validation import validate_group_name

        group_name = self.name_entry.get().strip()
        invalid_reason = validate_group_name(group_name)

        if invalid_reason:
            self.name_entry.configure(border_color="#FF5370")
            error_map = {
                "empty": "กรุณาระบุชื่อช่องแชท",
                "too_long": f"ชื่อช่องแชทยาวเกินไป (สูงสุด 48 ตัวอักษร)",
                "invalid_chars": "ชื่อช่องแชทมีอักขระที่ไม่อนุญาต",
                "reserved": "ชื่อช่องแชทนี้ไม่สามารถใช้งานได้ (คำสงวน)"
            }
            msg = error_map.get(invalid_reason, "ชื่อช่องแชทไม่ถูกต้อง")
            # self.master is the ChatApplication instance which has _show_error_popup
            if hasattr(self.master, "_show_error_popup"):
                self.master._show_error_popup("ข้อมูลไม่ถูกต้อง", msg)
            return

        members = [username for username, selected in self.selected.items() if selected.get()]
        self.destroy()
        self.on_confirm(group_name, members)


class GroupMemberAddDialog(ctk.CTkToplevel):
    def __init__(self, parent, online_users: list[str], existing_members: list[str], on_confirm) -> None:
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.selected = {}
        self.eligible_users = [username for username in online_users if username not in existing_members]

        self.title("เพิ่มสมาชิกเข้าช่องแชท")
        self.geometry("340x400")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#1A1D2E")

        self.update_idletasks()
        pos_x = parent.winfo_x() + (parent.winfo_width() // 2) - 170
        pos_y = parent.winfo_y() + (parent.winfo_height() // 2) - 200
        self.geometry(f"+{pos_x}+{pos_y}")

        ctk.CTkLabel(
            self,
            text="เพิ่มสมาชิกใหม่",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF75D8",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="เลือกเพื่อนที่ต้องการเชิญเข้าช่องแชท",
            font=ctk.CTkFont(size=11),
            text_color="#6B728E",
        ).pack(pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#0F1120",
            corner_radius=10,
            height=180,
            width=280,
        )
        scroll.pack(padx=28, pady=(4, 20))
        scroll.grid_columnconfigure(0, weight=1)

        if not self.eligible_users:
            ctk.CTkLabel(
                scroll,
                text="ไม่มีผู้ใช้อื่นที่สามารถเพิ่มได้",
                text_color="#6B728E",
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=0, pady=20)
        else:
            for index, username in enumerate(self.eligible_users):
                value = ctk.BooleanVar(value=False)
                self.selected[username] = value
                checkbox = ctk.CTkCheckBox(
                    scroll,
                    text=f"● {username}",
                    variable=value,
                    font=ctk.CTkFont(size=13),
                    fg_color="#FF75D8",
                    hover_color="#C2185B",
                    text_color="white",
                    checkmark_color="white",
                )
                checkbox.grid(row=index, column=0, sticky="w", padx=10, pady=4)

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
            text="เพิ่มสมาชิก",
            width=130,
            height=36,
            fg_color="#FF75D8",
            hover_color="#C2185B",
            text_color="white",
            corner_radius=18,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._confirm,
        ).pack(side="left", padx=8)

    def _confirm(self) -> None:
        members = [username for username, selected in self.selected.items() if selected.get()]
        if not members:
            return

        self.destroy()
        self.on_confirm(members)
