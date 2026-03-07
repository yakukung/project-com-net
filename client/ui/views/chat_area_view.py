import customtkinter as ctk

from client.services.group_service import (
    build_group_leave_payload,
    build_group_members_request_payload,
)
from client.ui.theme import (    AI_BTN,
    BORDER_COLOR,
    INPUT_BG,
    PANEL_BG,
    PRIMARY_BTN,
    PRIMARY_BTN_HOVER,
    TEXT_MUTED,
)


class ChatAreaViewMixin:
    def show_chat_frame(self) -> None:
        self.login_bg.destroy()
        self.unbind("<Return>")

        self.main_container = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_chat_area()

        self.bind("<Return>", lambda _event: self.send_message())

        self.group_panels = {}
        self.group_names = {}

        import threading

        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()
        self.message_input.focus()

    def _build_chat_area(self) -> None:
        self.content = ctk.CTkFrame(self.main_container, fg_color=PANEL_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 0))

        self.header_title = ctk.CTkLabel(
            header,
            text="# แชทรวม",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF75D8",
        )
        self.header_title.pack(side="left", pady=(0, 4))

        self.header_members_btn = ctk.CTkButton(
            header,
            text="👥 สมาชิก",
            width=80,
            height=30,
            fg_color="#2A2E44",
            hover_color="#3A3E54",
            corner_radius=15,
            font=ctk.CTkFont(size=12),
            command=self._on_click_members,
        )
        self.header_members_btn.pack(side="right", pady=(0, 4), padx=(5, 0))
        self.header_members_btn.pack_forget()

        self.header_leave_btn = ctk.CTkButton(
            header,
            text="ออกช่องแชท",
            width=90,
            height=30,
            fg_color="#3B2A2A",
            hover_color="#5C3A3A",
            text_color="#FF6B6B",
            corner_radius=15,
            font=ctk.CTkFont(size=12),
            command=self._on_click_leave_group,
        )
        self.header_leave_btn.pack(side="right", pady=(0, 4))
        self.header_leave_btn.pack_forget()

        ctk.CTkFrame(self.content, height=1, fg_color=BORDER_COLOR).grid(
            row=0,
            column=0,
            sticky="sew",
        )

        self.panels_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.panels_frame.grid(row=1, column=0, sticky="nsew")
        self.panels_frame.grid_columnconfigure(0, weight=1)
        self.panels_frame.grid_rowconfigure(0, weight=1)

        self.group_panel = self._make_chat_panel()
        self.group_panel["frame"].grid(row=0, column=0, sticky="nsew")
        self._post_welcome(self.group_panel)
        self._bind_drag_recursive(self.group_panel["scroll"])

        self._build_input_area()

    def _make_chat_panel(self) -> dict:
        frame = ctk.CTkFrame(self.panels_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.grid(row=0, column=0, padx=16, pady=10, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        return {"frame": frame, "scroll": scroll, "chat_row": 0, "typing_placeholders": []}

    def _post_welcome(self, panel: dict) -> None:
        welcome_frame = ctk.CTkFrame(panel["scroll"], fg_color="#272A3B", corner_radius=20)
        welcome_frame.grid(row=panel["chat_row"], column=0, pady=10)
        panel["chat_row"] += 1

        ctk.CTkLabel(
            welcome_frame,
            text="ยินดีต้อนรับ! พิมพ์ @ai เพื่อคุยกับ AI หรือคลิกที่ผู้ใช้เพื่อส่งข้อความส่วนตัว",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).pack(padx=20, pady=5)

    def _build_input_area(self) -> None:
        wrapper = ctk.CTkFrame(self.content, fg_color="transparent")
        wrapper.grid(row=2, column=0, sticky="ew")
        ctk.CTkFrame(wrapper, height=1, fg_color=BORDER_COLOR).pack(fill="x")

        input_container = ctk.CTkFrame(
            wrapper,
            fg_color=INPUT_BG,
            corner_radius=25,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        input_container.pack(fill="x", padx=20, pady=14)
        input_container.grid_columnconfigure(1, weight=1)

        def insert_ai_tag() -> None:
            current = self.message_input.get()
            if not current.startswith("@ai "):
                self.message_input.insert(0, "@ai ")
            else:
                self.message_input.delete(0, 4)
            self.message_input.focus()

        ctk.CTkButton(
            input_container,
            text="✨ @ai",
            width=70,
            height=35,
            fg_color=AI_BTN,
            hover_color="#3E256C",
            corner_radius=15,
            command=insert_ai_tag,
        ).grid(row=0, column=0, padx=(10, 5), pady=10)

        self.message_input = ctk.CTkEntry(
            input_container,
            placeholder_text="พิมพ์ข้อความ หรือ @username สำหรับแชทส่วนตัว…",
            placeholder_text_color=TEXT_MUTED,
            height=45,
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(size=13),
        )
        self.message_input.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            input_container,
            text="ส่ง 🚀",
            command=self.send_message,
            width=90,
            height=35,
            fg_color=PRIMARY_BTN,
            hover_color=PRIMARY_BTN_HOVER,
            text_color="white",
            corner_radius=15,
        ).grid(row=0, column=2, padx=(5, 10), pady=10)

    def switch_tab(self, tab_key: str) -> None:
        self.active_tab = tab_key

        self.group_panel["frame"].grid_remove()
        for info in self.dm_tabs.values():
            info["frame"].grid_remove()
        for info in self.group_panels.values():
            info["frame"].grid_remove()

        if tab_key == "group":
            self.group_panel["frame"].grid(row=0, column=0, sticky="nsew")
            self.header_title.configure(text="# แชทรวม")
            self.header_members_btn.pack_forget()
            self.header_leave_btn.pack_forget()
        elif tab_key.startswith("group:"):
            group_id = tab_key[6:]
            if group_id not in self.group_panels:
                self._create_group_panel(group_id)
            self.group_panels[group_id]["frame"].grid(row=0, column=0, sticky="nsew")
            group_name = self.group_names.get(group_id, group_id)
            self.header_title.configure(text=f"👥 {group_name}")
            self.header_members_btn.pack(side="right", pady=(0, 4), padx=(5, 0))
            self.header_leave_btn.pack(side="right", pady=(0, 4))
        else:
            if tab_key not in self.dm_tabs:
                self._create_dm_tab(tab_key)
            self.dm_tabs[tab_key]["frame"].grid(row=0, column=0, sticky="nsew")
            self.header_title.configure(text=f"🔒 DM - {tab_key}")
            self.unread_dms[tab_key] = 0
            self._refresh_dm_button(tab_key)
            self.header_members_btn.pack_forget()
            self.header_leave_btn.pack_forget()

        self.group_tab_btn.configure(fg_color="#2A2E44" if tab_key == "group" else "transparent")
        for group_id, button in self.group_channel_buttons.items():
            button.configure(fg_color="#2A2E44" if f"group:{group_id}" == tab_key else "transparent")
        for username, button in self.dm_buttons.items():
            button.configure(fg_color="#2A2E44" if username == tab_key else "transparent")

        self.message_input.focus()

    def _on_click_members(self) -> None:
        if not self.active_tab.startswith("group:"):
            return
        group_id = self.active_tab[6:]
        self.send_raw(build_group_members_request_payload(group_id))

    def _on_click_leave_group(self) -> None:
        if not self.active_tab.startswith("group:"):
            return

        from tkinter import messagebox

        group_id = self.active_tab[6:]
        if messagebox.askyesno("ยืนยัน", "คุณต้องการออกจากช่องแชทหรือไม่?"):
            self.send_raw(build_group_leave_payload(group_id))

    def _create_dm_tab(self, username: str) -> None:
        panel = self._make_chat_panel()
        panel["frame"].grid_columnconfigure(0, weight=1)
        panel["frame"].grid_rowconfigure(0, weight=1)
        self.dm_tabs[username] = panel
        self._bind_drag_recursive(panel["scroll"])

    def _create_group_panel(self, group_id: str) -> None:
        panel = self._make_chat_panel()
        panel["frame"].grid_columnconfigure(0, weight=1)
        panel["frame"].grid_rowconfigure(0, weight=1)
        self.group_panels[group_id] = panel
        self._bind_drag_recursive(panel["scroll"])
