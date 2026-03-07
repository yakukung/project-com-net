import customtkinter as ctk

from shared.config import PANEL_BG, BORDER_COLOR, INPUT_BG, TEXT_MUTED, AI_BTN, PRIMARY_BTN, PRIMARY_BTN_HOVER

class ChatAreaMixin:
    def show_chat_frame(self):
        self.login_bg.destroy()
        self.unbind('<Return>')

        self.main_container = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_chat_area()

        self.bind('<Return>', lambda e: self.send_message())

        import threading
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()
        self.message_input.focus()

    def _build_chat_area(self):
        self.content = ctk.CTkFrame(self.main_container, fg_color=PANEL_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(14,0))
        self.header_title = ctk.CTkLabel(header, text="# Global Chat",
                                          font=ctk.CTkFont(size=18, weight="bold"),
                                          text_color="#FF75D8")
        self.header_title.pack(side="left", pady=(0,4))

        ctk.CTkFrame(self.content, height=1, fg_color=BORDER_COLOR).grid(row=0, column=0, sticky="sew")

        self.panels_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.panels_frame.grid(row=1, column=0, sticky="nsew")
        self.panels_frame.grid_columnconfigure(0, weight=1)
        self.panels_frame.grid_rowconfigure(0, weight=1)

        self.group_panel = self._make_chat_panel()
        self.group_panel["frame"].grid(row=0, column=0, sticky="nsew")
        self._post_welcome(self.group_panel)
        self._bind_drag_recursive(self.group_panel["scroll"])

        self._build_input_area()

    def _make_chat_panel(self):
        frame = ctk.CTkFrame(self.panels_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.grid(row=0, column=0, padx=16, pady=10, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        return {"frame": frame, "scroll": scroll, "chat_row": 0}

    def _post_welcome(self, panel):
        wf = ctk.CTkFrame(panel["scroll"], fg_color="#272A3B", corner_radius=20)
        wf.grid(row=panel["chat_row"], column=0, pady=10)
        panel["chat_row"] += 1
        ctk.CTkLabel(wf, text="Welcome! Type @ai to talk to Gemini. Click a user to DM.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(padx=20, pady=5)

    def _build_input_area(self):
        wrapper = ctk.CTkFrame(self.content, fg_color="transparent")
        wrapper.grid(row=2, column=0, sticky="ew")
        ctk.CTkFrame(wrapper, height=1, fg_color=BORDER_COLOR).pack(fill="x")

        inp = ctk.CTkFrame(wrapper, fg_color=INPUT_BG, corner_radius=25,
                            border_width=1, border_color=BORDER_COLOR)
        inp.pack(fill="x", padx=20, pady=14)
        inp.grid_columnconfigure(1, weight=1)

        def insert_ai_tag():
            cur = self.message_input.get()
            if not cur.startswith("@ai "):
                self.message_input.insert(0, "@ai ")
            else:
                self.message_input.delete(0, 4)
            self.message_input.focus()

        ctk.CTkButton(inp, text="✨ @ai", width=70, height=35,
                      fg_color=AI_BTN, hover_color="#3E256C", corner_radius=15,
                      command=insert_ai_tag).grid(row=0, column=0, padx=(10,5), pady=10)

        self.message_input = ctk.CTkEntry(
            inp, placeholder_text="Type a message or @username for DM…",
            placeholder_text_color=TEXT_MUTED, height=45,
            fg_color="transparent", border_width=0, font=ctk.CTkFont(size=13))
        self.message_input.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(inp, text="Send 🚀", command=self.send_message, width=90, height=35,
                      fg_color=PRIMARY_BTN, hover_color=PRIMARY_BTN_HOVER,
                      text_color="white", corner_radius=15).grid(row=0, column=2, padx=(5,10), pady=10)

    def switch_tab(self, tab_key):
        self.active_tab = tab_key

        self.group_panel["frame"].grid_remove()
        for info in self.dm_tabs.values():
            info["frame"].grid_remove()

        if tab_key == "group":
            self.group_panel["frame"].grid(row=0, column=0, sticky="nsew")
            self.header_title.configure(text="# Global Chat")
            self.group_tab_btn.configure(fg_color="#2A2E44")
        else:
            if tab_key not in self.dm_tabs:
                self._create_dm_tab(tab_key)
            self.dm_tabs[tab_key]["frame"].grid(row=0, column=0, sticky="nsew")
            self.header_title.configure(text=f"🔒 DM — {tab_key}")
            self.unread_dms[tab_key] = 0
            self._refresh_dm_button(tab_key)
            for uname, btn in self.dm_buttons.items():
                btn.configure(fg_color="#2A2E44" if uname == tab_key else "transparent")
        self.message_input.focus()

    def _create_dm_tab(self, username):
        panel = self._make_chat_panel()
        panel["frame"].grid_columnconfigure(0, weight=1)
        panel["frame"].grid_rowconfigure(0, weight=1)
        self.dm_tabs[username] = panel
        self._bind_drag_recursive(panel["scroll"])
