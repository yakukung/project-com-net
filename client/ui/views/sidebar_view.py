import customtkinter as ctk

from client.services.block_service import build_unblock_user_payload
from client.services.group_service import build_group_create_payload
from client.ui.theme import BORDER_COLOR, SIDEBAR_BG, TEXT_MUTED


class SidebarViewMixin:
    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self.main_container,
            fg_color=SIDEBAR_BG,
            corner_radius=0,
            width=180,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(3, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="✨ AI Network\nChatRoom",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FF75D8",
        ).grid(row=0, column=0, padx=10, pady=(18, 4))

        ctk.CTkLabel(
            self.sidebar,
            text=f"👤 {self.username}",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, padx=10, pady=(0, 8))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).grid(
            row=2,
            column=0,
            sticky="ew",
            padx=8,
        )

        self.channel_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.channel_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=6)
        self.channel_frame.grid_columnconfigure(0, weight=1)

        channel_header = ctk.CTkFrame(self.channel_frame, fg_color="transparent")
        channel_header.grid(row=0, column=0, sticky="ew", padx=4, pady=(6, 2))
        channel_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            channel_header,
            text="ช่องสนทนา",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            channel_header,
            text="＋",
            width=24,
            height=24,
            fg_color="#FF75D8",
            hover_color="#C2185B",
            text_color="white",
            corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._open_create_group_dialog,
        ).grid(row=0, column=1, sticky="e")

        self.group_tab_btn = ctk.CTkButton(
            self.channel_frame,
            text="# แชทรวม",
            fg_color="#2A2E44",
            hover_color="#3A3E54",
            anchor="w",
            font=ctk.CTkFont(size=13),
            command=lambda: self.switch_tab("group"),
            height=32,
        )
        self.group_tab_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

        self.group_channel_buttons = {}
        self._group_channel_row = 2

        ctk.CTkFrame(self.channel_frame, height=1, fg_color=BORDER_COLOR).grid(
            row=50,
            column=0,
            sticky="ew",
            padx=4,
            pady=(8, 2),
        )

        ctk.CTkLabel(
            self.channel_frame,
            text="ข้อความส่วนตัว",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
        ).grid(row=51, column=0, sticky="w", padx=6, pady=(4, 2))

        self.dm_list_frame = ctk.CTkScrollableFrame(
            self.channel_frame,
            fg_color="transparent",
            height=150,
        )
        self.dm_list_frame.grid(row=52, column=0, sticky="nsew", padx=0, pady=0)
        self.dm_list_frame.grid_columnconfigure(0, weight=1)
        self.dm_buttons = {}

        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).grid(
            row=4,
            column=0,
            sticky="ew",
            padx=8,
        )

        self.blocked_users_button = ctk.CTkButton(
            self.sidebar,
            text="🚫 ที่บล็อค 0 คน",
            fg_color="transparent",
            hover_color="#2A2E44",
            anchor="w",
            font=ctk.CTkFont(size=12),
            height=30,
            command=self._open_blocked_users_dialog,
        )
        self.blocked_users_button.grid(row=5, column=0, padx=8, pady=(4, 0), sticky="ew")

        self.online_label = ctk.CTkLabel(
            self.sidebar,
            text="🟢 ออนไลน์ 0 คน",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self.online_label.grid(row=6, column=0, padx=10, pady=(6, 12))

        self.blocked_users_dialog = None
        self._refresh_blocked_users_button()

    def _open_create_group_dialog(self) -> None:
        from client.ui.dialogs.group_create_dialog import GroupCreateDialog

        GroupCreateDialog(self, list(getattr(self, "online_users", [])), self._on_create_group)

    def _on_create_group(self, name: str, members: list[str]) -> None:
        self.send_raw(build_group_create_payload(name, members))

    def _add_group_channel_button(self, group_id: str, group_name: str) -> None:
        if group_id in self.group_channel_buttons:
            return

        tab_key = f"group:{group_id}"
        button = ctk.CTkButton(
            self.channel_frame,
            text=f"# {group_name}",
            fg_color="transparent",
            hover_color="#2A2E44",
            anchor="w",
            font=ctk.CTkFont(size=13),
            command=lambda: self.switch_tab(tab_key),
            height=32,
        )
        button.grid(row=self._group_channel_row, column=0, sticky="ew", padx=2, pady=2)
        self._group_channel_row += 1
        self.group_channel_buttons[group_id] = button

    def _update_user_list(self, users: list[str]) -> None:
        blocked_lower = {name.lower() for name in getattr(self, "blocked_usernames", set())}
        self.online_users = [
            username
            for username in users
            if username != self.username and username.lower() not in blocked_lower
        ]
        self.online_label.configure(text=f"🟢 ออนไลน์ {len(self.online_users) + 1} คน")

        offline_users = [username for username in self.dm_buttons if username not in self.online_users]
        for username in offline_users:
            self.dm_buttons[username].destroy()
            del self.dm_buttons[username]

        for index, username in enumerate(self.online_users):
            if username in self.dm_buttons:
                continue

            button = ctk.CTkButton(
                self.dm_list_frame,
                text=f"● {username}",
                fg_color="transparent",
                hover_color="#2A2E44",
                anchor="w",
                font=ctk.CTkFont(size=13),
                command=lambda name=username: self.switch_tab(name),
                height=30,
            )
            button.grid(row=index, column=0, sticky="ew", padx=2, pady=1)
            self.dm_buttons[username] = button

    def _refresh_dm_button(self, username: str) -> None:
        if username not in self.dm_buttons:
            return

        unread_count = self.unread_dms.get(username, 0)
        label = f"● {username}" if unread_count == 0 else f"● {username}  ({unread_count})"
        self.dm_buttons[username].configure(text=label)

    def _refresh_blocked_users_button(self) -> None:
        blocked_count = len(getattr(self, "blocked_usernames", set()))
        label = f"🚫 ที่บล็อค {blocked_count} คน"
        self.blocked_users_button.configure(text=label)

    def _open_blocked_users_dialog(self) -> None:
        existing = getattr(self, "blocked_users_dialog", None)
        if existing:
            try:
                if existing.winfo_exists():
                    existing.focus_force()
                    return
            except Exception:
                self.blocked_users_dialog = None

        from client.ui.dialogs.blocked_users_dialog import BlockedUsersDialog

        blocked_users = sorted(getattr(self, "blocked_usernames", set()), key=str.lower)
        self.blocked_users_dialog = BlockedUsersDialog(
            self,
            blocked_users=blocked_users,
            on_unblock=self._on_unblock_from_blocked_list,
        )
        self.blocked_users_dialog.bind("<Destroy>", self._on_blocked_dialog_destroy, add="+")

    def _on_blocked_dialog_destroy(self, event) -> None:
        if event.widget is getattr(self, "blocked_users_dialog", None):
            self.blocked_users_dialog = None

    def _on_unblock_from_blocked_list(self, username: str) -> None:
        matched_name = next(
            (name for name in self.blocked_usernames if name.lower() == username.lower()),
            None,
        )
        if not matched_name:
            return

        self.blocked_usernames.discard(matched_name)
        self.send_raw(build_unblock_user_payload(matched_name))
        self._refresh_blocked_users_button()

        if self.active_tab.lower() == matched_name.lower() and hasattr(self, "_refresh_block_button"):
            self._refresh_block_button(matched_name)
