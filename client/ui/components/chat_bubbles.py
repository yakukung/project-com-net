import re
from datetime import datetime
from typing import Optional

import customtkinter as ctk

from client.ui.theme import (    BORDER_COLOR,
    BUBBLE_AI,
    BUBBLE_DM,
    BUBBLE_ME,
    BUBBLE_OTHER,
    DM_ACCENT,
    TEXT_MUTED,
)

AI_TYPING_PLACEHOLDER = "AI กำลังพิมพ์คำตอบ"


class ChatBubblesComponentMixin:
    def _strip_markdown(self, text: str) -> str:
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"_(.*?)_", r"\1", text)
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[\*-]\s+", "• ", text, flags=re.MULTILINE)
        return text.strip()

    def append_to_chat(self, message: str, panel_key: str = "group") -> None:
        sender = "System"
        text = message
        reply_quote = None

        if message.startswith("[") and "]: " in message:
            header, text = message.split("]: ", 1)
            sender = header[1:]
            if "|REPLY:" in sender:
                sender, reply_quote = sender.split("|REPLY:", 1)
                reply_quote = reply_quote.strip()

        is_me = sender == self.username
        is_system = sender == "System"
        is_ai = "AI" in sender

        if is_ai:
            text = self._strip_markdown(text)

        if is_system:
            text_color = TEXT_MUTED
            bubble_color = "transparent"
        else:
            text_color = "white"
            bubble_color = BUBBLE_ME if is_me else (BUBBLE_AI if is_ai else BUBBLE_OTHER)

        panel = self._resolve_panel(panel_key)
        if panel is None:
            return

        is_typing_placeholder = is_system and AI_TYPING_PLACEHOLDER in text
        if (is_ai or "AI Error" in text) and not is_typing_placeholder:
            self._remove_typing_placeholder(panel)

        self._append_bubble(
            panel,
            text,
            is_me=is_me,
            sender=sender,
            bubble_color=bubble_color,
            text_color=text_color,
            is_system=is_system,
            reply_quote=reply_quote,
            is_typing_placeholder=is_typing_placeholder,
        )

    def _resolve_panel(self, panel_key: str):
        if panel_key == "group":
            return self.group_panel

        if panel_key.startswith("group:"):
            group_id = panel_key[6:]
            return self.group_panels.get(group_id)

        return self.dm_tabs.get(panel_key)

    def _remove_typing_placeholder(self, panel: dict) -> None:
        placeholders = panel.get("typing_placeholders")
        if isinstance(placeholders, list):
            while placeholders:
                container = placeholders.pop(0)
                try:
                    if container.winfo_exists():
                        container.destroy()
                        return
                except Exception:
                    continue

        for child in panel["scroll"].winfo_children():
            try:
                bubble_frame = child.winfo_children()[0]
            except Exception:
                continue

            stack = [bubble_frame]
            while stack:
                widget = stack.pop()
                if isinstance(widget, ctk.CTkLabel):
                    try:
                        label_text = widget.cget("text")
                    except Exception:
                        label_text = ""
                    if AI_TYPING_PLACEHOLDER in str(label_text):
                        child.destroy()
                        return
                try:
                    stack.extend(widget.winfo_children())
                except Exception:
                    continue

    def _append_bubble(
        self,
        panel: dict,
        text: str,
        is_me: bool = False,
        sender: str = "",
        bubble_color: str = BUBBLE_OTHER,
        text_color: str = "white",
        is_system: bool = False,
        reply_quote: Optional[str] = None,
        accent_color: Optional[str] = None,
        tag: Optional[str] = None,
        is_typing_placeholder: bool = False,
    ) -> None:
        scroll = panel["scroll"]
        align = "e" if is_me else "w"

        border_kwargs = {}
        if not is_me and not is_system and bubble_color not in (BUBBLE_AI, BUBBLE_DM):
            border_kwargs = {"border_width": 1, "border_color": BORDER_COLOR}

        container = ctk.CTkFrame(scroll, fg_color="transparent")
        container.grid(row=panel["chat_row"], column=0, sticky="ew", pady=4, padx=6)
        panel["chat_row"] += 1
        
        # Grid layout for bubble and timestamp
        container.grid_columnconfigure(0, weight=1 if is_me else 0)
        container.grid_columnconfigure(1, weight=0 if is_me else 1)

        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=15, **border_kwargs)
        
        if not is_system:
            time_str = datetime.now().strftime("%H:%M")
            time_label = ctk.CTkLabel(
                container,
                text=time_str,
                font=ctk.CTkFont(size=10),
                text_color=TEXT_MUTED,
            )
            
            if is_me:
                bubble.grid(row=0, column=1, sticky="e")
                time_label.grid(row=0, column=0, sticky="se", padx=(0, 8), pady=(0, 5))
            else:
                bubble.grid(row=0, column=0, sticky="w")
                time_label.grid(row=0, column=1, sticky="sw", padx=(8, 0), pady=(0, 5))
        else:
            bubble.grid(row=0, column=0, columnspan=2)
            if sender == "System": # Center system messages
                 bubble.grid_configure(sticky="")
            else:
                 bubble.grid_configure(sticky=align)

        if tag:
            ctk.CTkLabel(
                bubble,
                text=tag,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=accent_color or DM_ACCENT,
            ).pack(anchor="w", padx=10, pady=(4, 0))

        if not is_me and not is_system:
            ctk.CTkLabel(
                bubble,
                text=sender,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#A0C4FF",
            ).pack(anchor="w", padx=10, pady=(5, 0))

        if reply_quote:
            display = reply_quote if len(reply_quote) <= 60 else f"{reply_quote[:57]}..."
            ctk.CTkLabel(
                bubble,
                text=f"│ {display}",
                font=ctk.CTkFont(size=11),
                text_color="#8A91A6",
                justify="left",
            ).pack(anchor="w", padx=10, pady=(6, 0))

        segments = re.split(r"(```.*?```)", text, flags=re.DOTALL)
        for segment in segments:
            if not segment:
                continue

            if segment.startswith("```") and segment.endswith("```"):
                lines = segment.strip().split("\n")
                language = lines[0][3:].strip()
                code = "\n".join(lines[1:-1]) if len(lines) >= 2 else segment[3:-3].strip()

                code_container = ctk.CTkFrame(bubble, fg_color="#1E1E1E", corner_radius=8)
                code_container.pack(padx=15, pady=5, fill="x", expand=True)

                header = ctk.CTkFrame(code_container, fg_color="#333333", height=30, corner_radius=8)
                header.pack(fill="x")

                ctk.CTkLabel(
                    header,
                    text=language or "code",
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                ).pack(side="left", padx=10)

                def copy_code(code_text: str = code) -> None:
                    self.clipboard_clear()
                    self.clipboard_append(code_text)

                ctk.CTkButton(
                    header,
                    text="คัดลอก",
                    width=50,
                    height=24,
                    font=ctk.CTkFont(size=12),
                    command=copy_code,
                ).pack(side="right", padx=5, pady=3)

                ctk.CTkLabel(
                    code_container,
                    text=code,
                    font=ctk.CTkFont(family="Courier", size=13),
                    text_color="#D4D4D4",
                    justify="left",
                ).pack(padx=10, pady=10, anchor="w")
            elif segment.strip():
                ctk.CTkLabel(
                    bubble,
                    text=segment.strip(),
                    font=ctk.CTkFont(size=14),
                    text_color=text_color,
                    justify="left",
                    wraplength=400,
                ).pack(padx=15, pady=(5, 10), anchor="w")

        self._bind_drag_recursive(container)
        scroll._parent_canvas.update_idletasks()
        scroll._parent_canvas.yview_moveto(1.0)

        if is_typing_placeholder:
            panel.setdefault("typing_placeholders", []).append(container)

    def _on_drag_start(self, event) -> None:
        self._drag_start_y = event.y_root
        self._drag_start_view = self._active_canvas().yview()[0]

    def _on_drag_motion(self, event) -> None:
        try:
            canvas = self._active_canvas()
            bbox = canvas.bbox("all")
            if not bbox or bbox[3] == 0:
                return

            delta = event.y_root - self._drag_start_y
            fraction = -delta / bbox[3]
            new_pos = max(0.0, min(1.0, self._drag_start_view + fraction))
            canvas.yview_moveto(new_pos)
        except Exception:
            return

    def _active_canvas(self):
        if self.active_tab == "group":
            return self.group_panel["scroll"]._parent_canvas

        if self.active_tab.startswith("group:"):
            group_id = self.active_tab[6:]
            panel = self.group_panels.get(group_id)
            if panel:
                return panel["scroll"]._parent_canvas

        panel = self.dm_tabs.get(self.active_tab)
        if panel:
            return panel["scroll"]._parent_canvas

        return self.group_panel["scroll"]._parent_canvas

    def _bind_drag_recursive(self, widget) -> None:
        widget.bind("<ButtonPress-1>", self._on_drag_start, add="+")
        widget.bind("<B1-Motion>", self._on_drag_motion, add="+")
        for child in widget.winfo_children():
            self._bind_drag_recursive(child)
