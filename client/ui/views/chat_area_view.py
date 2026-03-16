import unicodedata

import customtkinter as ctk

from client.services.block_service import build_block_user_payload, build_unblock_user_payload
from client.services.group_service import (
    build_group_delete_payload,
    build_group_leave_payload,
    build_group_members_request_payload,
)
from client.ui.theme import (
    AI_BTN,
    BORDER_COLOR,
    INPUT_BG,
    PANEL_BG,
    PRIMARY_BTN,
    PRIMARY_BTN_HOVER,
    TEXT_MUTED,
)


_EMOJI_BASE_RANGES = (
    (0x1F600, 0x1F64F),  # Smileys
    (0x1F300, 0x1F3FF),  # Symbols, weather, activities
    (0x1F680, 0x1F6FF),  # Transport and map symbols
    (0x1F900, 0x1FA95),  # Newer faces/gestures/objects
    (0x2600, 0x26FF),    # Misc symbols
)
_EMOJI_MAX_ITEMS = 192
_EMOJI_PICKER_HEIGHT = 280
_EMOJI_BUTTON_SIZE = 32
_EMOJI_BUTTON_PAD_X = 4
_EMOJI_BUTTON_PAD_Y = 4
_EMOJI_MIN_COLUMNS = 7
_EMOJI_MAX_COLUMNS = 28
_EMOJI_BUILD_BATCH = 24


def _to_emoji_presentation(cp: int) -> str:
    base = chr(cp)
    if cp <= 0x2BFF:
        return f"{base}\ufe0f"
    return base


def _build_emoji_options() -> tuple[str, ...]:
    options: list[str] = []
    seen: set[str] = set()

    for start, end in _EMOJI_BASE_RANGES:
        for cp in range(start, end + 1):
            if cp in {0xFE0F, 0x200D}:
                continue

            char = chr(cp)
            if unicodedata.category(char) not in {"So", "Sk"}:
                continue

            if not unicodedata.name(char, ""):
                continue

            emoji = _to_emoji_presentation(cp)
            if emoji in seen:
                continue
            seen.add(emoji)
            options.append(emoji)

            if len(options) >= _EMOJI_MAX_ITEMS:
                return tuple(options)

    return tuple(options)


EMOJI_OPTIONS = _build_emoji_options()


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
        self.emoji_picker = None
        self.emoji_scroll = None
        self.emoji_loading_label = None
        self.emoji_buttons = []
        self.emoji_columns = 0
        self._emoji_build_in_progress = False
        self._emoji_build_index = 0
        self._emoji_picker_ready = False
        self._emoji_preload_after_id = None

        if not getattr(self, "_emoji_global_bindings_ready", False):
            self.bind_all("<Button-1>", self._on_global_click_for_emoji, add="+")
            self.bind_all("<Escape>", self._on_global_escape_for_emoji, add="+")
            self._emoji_global_bindings_ready = True

        import threading

        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()
        self.message_input.focus()
        # Preload emoji widgets after UI settles so first open is much faster.
        self._schedule_emoji_preload()

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

        self.header_block_btn = ctk.CTkButton(
            header,
            text="บล็อคผู้ใช้",
            width=92,
            height=30,
            fg_color="#553410",
            hover_color="#6B4315",
            text_color="#FFD58A",
            corner_radius=15,
            font=ctk.CTkFont(size=12),
            command=self._on_toggle_block_dm,
        )
        self.header_block_btn.pack(side="right", pady=(0, 4), padx=(0, 5))
        self.header_block_btn.pack_forget()

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
        self.input_wrapper = wrapper
        ctk.CTkFrame(wrapper, height=1, fg_color=BORDER_COLOR).pack(fill="x")

        input_container = ctk.CTkFrame(
            wrapper,
            fg_color=INPUT_BG,
            corner_radius=25,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.input_container = input_container
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

        self.emoji_button = ctk.CTkButton(
            input_container,
            text="😊",
            command=self._toggle_emoji_picker,
            width=44,
            height=35,
            fg_color="#2A2E44",
            hover_color="#3A3E54",
            text_color="white",
            corner_radius=15,
            font=ctk.CTkFont(size=16),
        )
        self.emoji_button.grid(row=0, column=2, padx=(5, 5), pady=10)

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
        ).grid(row=0, column=3, padx=(5, 10), pady=10)

    def _toggle_emoji_picker(self) -> None:
        if not self._is_widget_alive(getattr(self, "input_wrapper", None)):
            return
        if self._is_emoji_picker_open():
            self._close_emoji_picker()
            return
        self._open_emoji_picker()

    def _is_widget_alive(self, widget) -> bool:
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def _schedule_emoji_preload(self) -> None:
        self._cancel_emoji_preload()
        try:
            self._emoji_preload_after_id = self.after(120, self._preload_emoji_picker)
        except Exception:
            self._emoji_preload_after_id = None

    def _cancel_emoji_preload(self) -> None:
        after_id = getattr(self, "_emoji_preload_after_id", None)
        if not after_id:
            return
        try:
            self.after_cancel(after_id)
        except Exception:
            pass
        self._emoji_preload_after_id = None

    def _cleanup_emoji_runtime(self) -> None:
        self._cancel_emoji_preload()
        self.emoji_picker = None
        self.emoji_scroll = None
        self.emoji_loading_label = None
        self.emoji_buttons = []
        self.emoji_columns = 0
        self._emoji_build_in_progress = False
        self._emoji_build_index = 0
        self._emoji_picker_ready = False

    def _is_emoji_picker_open(self) -> bool:
        picker = getattr(self, "emoji_picker", None)
        if not self._is_widget_alive(picker):
            return False
        try:
            return picker.winfo_manager() == "pack"
        except Exception:
            return False

    def _ensure_emoji_picker(self) -> None:
        if self._is_widget_alive(self.emoji_picker):
            return
        self.emoji_picker = None

        wrapper = getattr(self, "input_wrapper", None)
        if not self._is_widget_alive(wrapper):
            return

        try:
            picker = ctk.CTkFrame(
                wrapper,
                fg_color=INPUT_BG,
                border_width=1,
                border_color=BORDER_COLOR,
                corner_radius=12,
                height=_EMOJI_PICKER_HEIGHT,
            )
        except Exception:
            return
        picker.pack_propagate(False)
        self.emoji_picker = picker

        header = ctk.CTkFrame(picker, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(6, 2))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=f"เลือกอีโมจิ ({len(EMOJI_OPTIONS)} รายการ)",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="w", padx=(2, 0))

        ctk.CTkButton(
            header,
            text="✕",
            width=28,
            height=24,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#2A2E44",
            text_color=TEXT_MUTED,
            command=self._close_emoji_picker,
        ).grid(row=0, column=1, sticky="e")

        scroll = ctk.CTkScrollableFrame(
            picker,
            fg_color="transparent",
        )
        scroll.pack(fill="both", expand=True, padx=(8, 16), pady=(0, 10))
        self.emoji_scroll = scroll
        self.emoji_loading_label = ctk.CTkLabel(
            scroll,
            text="กำลังโหลดอีโมจิ...",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.emoji_loading_label.grid(row=0, column=0, pady=20, padx=8, sticky="w")
        self.emoji_buttons = []
        self.emoji_columns = 0
        self._emoji_build_index = 0
        self._emoji_picker_ready = False

        scroll.bind("<Configure>", self._on_emoji_scroll_configure, add="+")
        self._kick_emoji_build()

    def _kick_emoji_build(self) -> None:
        if self._emoji_picker_ready or self._emoji_build_in_progress:
            return
        scroll = getattr(self, "emoji_scroll", None)
        if not self._is_widget_alive(scroll):
            return
        self._emoji_build_in_progress = True
        self.after(0, self._build_emoji_batch)

    def _build_emoji_batch(self) -> None:
        scroll = getattr(self, "emoji_scroll", None)
        if not self._is_widget_alive(scroll):
            self._emoji_build_in_progress = False
            return

        start = self._emoji_build_index
        end = min(start + _EMOJI_BUILD_BATCH, len(EMOJI_OPTIONS))

        for idx in range(start, end):
            emoji = EMOJI_OPTIONS[idx]
            button = ctk.CTkButton(
                scroll,
                text=emoji,
                width=_EMOJI_BUTTON_SIZE,
                height=_EMOJI_BUTTON_SIZE,
                fg_color="transparent",
                hover_color="#2A2E44",
                corner_radius=8,
                font=ctk.CTkFont(size=18),
                command=lambda value=emoji: self._insert_emoji(value),
            )
            self.emoji_buttons.append(button)

        self._emoji_build_index = end

        if self.emoji_loading_label and self.emoji_loading_label.winfo_exists():
            if end < len(EMOJI_OPTIONS):
                self.emoji_loading_label.configure(text=f"กำลังโหลดอีโมจิ... {end}/{len(EMOJI_OPTIONS)}")
            else:
                self.emoji_loading_label.destroy()
                self.emoji_loading_label = None

        width = int(scroll.winfo_width())
        if width > 0:
            self._layout_emoji_buttons(width)

        if end >= len(EMOJI_OPTIONS):
            self._emoji_build_in_progress = False
            self._emoji_picker_ready = True
            return

        self.after(1, self._build_emoji_batch)

    def _calculate_emoji_columns(self, width: int) -> int:
        usable_width = max(width - 12, _EMOJI_BUTTON_SIZE + (_EMOJI_BUTTON_PAD_X * 2))
        cell_width = _EMOJI_BUTTON_SIZE + (_EMOJI_BUTTON_PAD_X * 2)
        cols = max(1, usable_width // cell_width)
        cols = max(_EMOJI_MIN_COLUMNS, cols)
        cols = min(_EMOJI_MAX_COLUMNS, cols)
        return int(cols)

    def _layout_emoji_buttons(self, width: int) -> None:
        scroll = getattr(self, "emoji_scroll", None)
        if not self._is_widget_alive(scroll):
            return
        if not self.emoji_buttons:
            return

        columns = self._calculate_emoji_columns(width)
        if columns == self.emoji_columns:
            return
        self.emoji_columns = columns

        for col in range(_EMOJI_MAX_COLUMNS):
            scroll.grid_columnconfigure(col, weight=0)
        for col in range(columns):
            scroll.grid_columnconfigure(col, weight=1)

        for idx, button in enumerate(self.emoji_buttons):
            row, col = divmod(idx, columns)
            button.grid(
                row=row,
                column=col,
                padx=_EMOJI_BUTTON_PAD_X,
                pady=_EMOJI_BUTTON_PAD_Y,
            )

    def _on_emoji_scroll_configure(self, event) -> None:
        width = int(getattr(event, "width", 0) or 0)
        if width > 0:
            self._layout_emoji_buttons(width)

    def _open_emoji_picker(self) -> None:
        if not self._is_widget_alive(getattr(self, "emoji_button", None)):
            return

        self._ensure_emoji_picker()
        picker = getattr(self, "emoji_picker", None)
        if not self._is_widget_alive(picker):
            return
        if not self._is_widget_alive(getattr(self, "input_container", None)):
            return

        self._kick_emoji_build()
        try:
            picker.pack(before=self.input_container, fill="x", padx=20, pady=(8, 0))
            picker.lift()
        except Exception:
            return
        scroll = getattr(self, "emoji_scroll", None)
        if self._is_widget_alive(scroll):
            self.after(0, lambda: self._layout_emoji_buttons(scroll.winfo_width()))

    def _preload_emoji_picker(self) -> None:
        self._emoji_preload_after_id = None
        if not self._is_widget_alive(getattr(self, "input_wrapper", None)):
            return
        try:
            self._ensure_emoji_picker()
            self._close_emoji_picker()
        except Exception:
            return

    def _close_emoji_picker(self) -> None:
        picker = getattr(self, "emoji_picker", None)
        if not self._is_widget_alive(picker):
            return

        try:
            picker.pack_forget()
        except Exception:
            pass

    def _is_widget_descendant_of(self, widget, ancestor) -> bool:
        current = widget
        while current is not None:
            if current is ancestor:
                return True
            current = getattr(current, "master", None)
        return False

    def _on_global_click_for_emoji(self, event) -> None:
        if not self._is_emoji_picker_open():
            return

        picker = getattr(self, "emoji_picker", None)
        if not self._is_widget_alive(picker):
            return

        target = getattr(event, "widget", None)
        if target is None:
            self._close_emoji_picker()
            return

        if self._is_widget_descendant_of(target, picker):
            return

        if hasattr(self, "emoji_button") and self._is_widget_descendant_of(target, self.emoji_button):
            return

        self._close_emoji_picker()

    def _on_global_escape_for_emoji(self, _event) -> None:
        if self._is_emoji_picker_open():
            self._close_emoji_picker()

    def _insert_emoji(self, emoji: str) -> None:
        self.message_input.focus_set()
        self.message_input.insert("insert", emoji)

    def switch_tab(self, tab_key: str) -> None:
        self.active_tab = tab_key
        self._close_emoji_picker()

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
            self.header_block_btn.pack_forget()
        elif tab_key.startswith("group:"):
            group_id = tab_key[6:]
            if group_id not in self.group_panels:
                self._create_group_panel(group_id)
            self.group_panels[group_id]["frame"].grid(row=0, column=0, sticky="nsew")
            group_name = self.group_names.get(group_id, group_id)
            self.header_title.configure(text=f"👥 {group_name}")
            self.header_members_btn.pack(side="right", pady=(0, 4), padx=(5, 0))
            self.header_leave_btn.pack(side="right", pady=(0, 4))
            self.header_block_btn.pack_forget()
        else:
            if tab_key not in self.dm_tabs:
                self._create_dm_tab(tab_key)
            self.dm_tabs[tab_key]["frame"].grid(row=0, column=0, sticky="nsew")
            self.header_title.configure(text=f"🔒 DM - {tab_key}")
            self.unread_dms[tab_key] = 0
            self._refresh_dm_button(tab_key)
            self.header_members_btn.pack_forget()
            self.header_leave_btn.pack_forget()
            self._refresh_block_button(tab_key)
            self.header_block_btn.pack(side="right", pady=(0, 4), padx=(0, 5))

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
        if messagebox.askyesno("ยืนยัน", "คุณต้องการออกจากช่องแชทหรือไม่?", parent=self):
            self.send_raw(build_group_leave_payload(group_id))

    def _on_click_delete_group(self) -> None:
        if not self.active_tab.startswith("group:"):
            return

        group_id = self.active_tab[6:]
        self._on_delete_group_by_id(group_id)

    def _on_delete_group_by_id(self, group_id: str) -> None:
        from tkinter import messagebox

        if messagebox.askyesno("ยืนยัน", "คุณต้องการลบช่องแชทย่อยนี้หรือไม่?", parent=self):
            self.send_raw(build_group_delete_payload(group_id))

    def _is_username_blocked(self, username: str) -> bool:
        target = username.strip().lower()
        if not target:
            return False
        return any(name.lower() == target for name in getattr(self, "blocked_usernames", set()))

    def _remove_dm_tab_by_username(self, username: str) -> None:
        target = username.strip().lower()
        if not target:
            return

        for dm_name in list(self.dm_tabs.keys()):
            if dm_name.lower() != target:
                continue
            panel = self.dm_tabs.pop(dm_name, None)
            if not panel:
                continue
            frame = panel.get("frame")
            try:
                if frame and frame.winfo_exists():
                    frame.destroy()
            except Exception:
                pass

        for dm_name in list(self.dm_buttons.keys()):
            if dm_name.lower() != target:
                continue
            button = self.dm_buttons.pop(dm_name, None)
            try:
                if button and button.winfo_exists():
                    button.destroy()
            except Exception:
                pass

        for dm_name in list(self.unread_dms.keys()):
            if dm_name.lower() == target:
                self.unread_dms.pop(dm_name, None)

    def _remove_sender_messages_from_panel(self, panel: dict | None, username: str) -> None:
        if not panel:
            return

        target = username.strip().lower()
        if not target:
            return

        scroll = panel.get("scroll")
        if not scroll:
            return

        removed_any = False
        for child in list(scroll.winfo_children()):
            sender_key = getattr(child, "_chat_sender_key", "")
            if sender_key != target:
                continue
            try:
                child.destroy()
                removed_any = True
            except Exception:
                pass

        if removed_any:
            try:
                scroll._parent_canvas.update_idletasks()
            except Exception:
                pass

    def _hide_blocked_user_locally(self, username: str) -> None:
        target = username.strip().lower()
        if not target:
            return

        if self.active_tab.strip().lower() == target:
            self.switch_tab("group")

        self._remove_dm_tab_by_username(username)
        self._remove_sender_messages_from_panel(self.group_panel, username)
        for panel in self.group_panels.values():
            self._remove_sender_messages_from_panel(panel, username)

    def _refresh_block_button(self, username: str) -> None:
        is_blocked = self._is_username_blocked(username)
        if is_blocked:
            self.header_block_btn.configure(
                text="เลิกบล็อค",
                fg_color="#26573A",
                hover_color="#2E6E48",
                text_color="#B8F7CF",
            )
            return

        self.header_block_btn.configure(
            text="บล็อคผู้ใช้",
            fg_color="#553410",
            hover_color="#6B4315",
            text_color="#FFD58A",
        )

    def _on_toggle_block_dm(self) -> None:
        if self.active_tab == "group" or self.active_tab.startswith("group:"):
            return

        from tkinter import messagebox

        target_username = self.active_tab
        is_blocked = self._is_username_blocked(target_username)

        if is_blocked:
            if messagebox.askyesno("ยืนยัน", f"เลิกบล็อค '{target_username}' หรือไม่?", parent=self):
                matched_name = next(
                    (name for name in self.blocked_usernames if name.lower() == target_username.lower()),
                    target_username,
                )
                self.blocked_usernames.discard(matched_name)
                self.send_raw(build_unblock_user_payload(matched_name))
                self._refresh_block_button(target_username)
                if hasattr(self, "_refresh_blocked_users_button"):
                    self._refresh_blocked_users_button()
            return

        if messagebox.askyesno(
            "ยืนยัน",
            f"บล็อค '{target_username}' แบบผูก IP หรือไม่?\nคุณจะไม่เห็นข้อความของผู้ใช้นี้ทุกห้องแชท",
            parent=self,
        ):
            self.blocked_usernames.add(target_username)
            self.send_raw(build_block_user_payload(target_username))
            self._hide_blocked_user_locally(target_username)
            self._refresh_block_button(target_username)
            if hasattr(self, "_refresh_blocked_users_button"):
                self._refresh_blocked_users_button()

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
