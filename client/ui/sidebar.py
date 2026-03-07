import customtkinter as ctk

from shared.config import SIDEBAR_BG, BORDER_COLOR, TEXT_MUTED

class SidebarMixin:
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.main_container, fg_color=SIDEBAR_BG,
                                     corner_radius=0, width=180)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(3, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(self.sidebar, text="✨ AI Network\nChatRoom",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#FF75D8").grid(row=0, column=0, padx=10, pady=(18,4))

        ctk.CTkLabel(self.sidebar, text=f"👤 {self.username}",
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_MUTED).grid(row=1, column=0, padx=10, pady=(0,8))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).grid(row=2, column=0, sticky="ew", padx=8)

        # Channels
        self.channel_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.channel_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=6)
        self.channel_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.channel_frame, text="CHANNELS",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=6, pady=(6,2))

        self.group_tab_btn = ctk.CTkButton(
            self.channel_frame, text="# Global Chat",
            fg_color="#2A2E44", hover_color="#3A3E54",
            anchor="w", font=ctk.CTkFont(size=13),
            command=lambda: self.switch_tab("group"), height=32)
        self.group_tab_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

        ctk.CTkFrame(self.channel_frame, height=1, fg_color=BORDER_COLOR).grid(
            row=2, column=0, sticky="ew", padx=4, pady=(8,2))

        ctk.CTkLabel(self.channel_frame, text="DIRECT MESSAGES",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).grid(row=3, column=0, sticky="w", padx=6, pady=(4,2))

        # Scrollable area for DM user buttons
        self.dm_list_frame = ctk.CTkScrollableFrame(self.channel_frame, fg_color="transparent", height=200)
        self.dm_list_frame.grid(row=4, column=0, sticky="nsew", padx=0, pady=0)
        self.dm_list_frame.grid_columnconfigure(0, weight=1)
        self.dm_buttons = {}   

        # Online count
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).grid(row=4, column=0, sticky="ew", padx=8)
        self.online_label = ctk.CTkLabel(self.sidebar, text="🟢 0 online",
                                          font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.online_label.grid(row=5, column=0, padx=10, pady=(6,12))

    def _update_user_list(self, users):
        self.online_users = [u for u in users if u != self.username]
        self.online_label.configure(text=f"🟢 {len(users)} online")

        gone = [u for u in self.dm_buttons if u not in self.online_users]
        for u in gone:
            self.dm_buttons[u].destroy()
            del self.dm_buttons[u]

        for i, uname in enumerate(self.online_users):
            if uname not in self.dm_buttons:
                def make_cmd(n=uname):
                    return lambda: self.switch_tab(n)
                btn = ctk.CTkButton(
                    self.dm_list_frame, text=f"● {uname}",
                    fg_color="transparent", hover_color="#2A2E44",
                    anchor="w", font=ctk.CTkFont(size=13),
                    command=make_cmd(), height=30)
                btn.grid(row=i, column=0, sticky="ew", padx=2, pady=1)
                self.dm_buttons[uname] = btn

    def _refresh_dm_button(self, username):
        if username not in self.dm_buttons:
            return
        count = self.unread_dms.get(username, 0)
        label = f"● {username}" if count == 0 else f"● {username}  ({count})"
        self.dm_buttons[username].configure(text=label)
