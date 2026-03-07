import customtkinter as ctk
import re

from shared.config import BORDER_COLOR, BUBBLE_ME, BUBBLE_OTHER, BUBBLE_AI, BUBBLE_DM, DM_ACCENT, TEXT_MUTED

class BubblesMixin:
    def _strip_markdown(self, text):
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__',     r'\1', text)
        text = re.sub(r'\*(.*?)\*',     r'\1', text)
        text = re.sub(r'_(.*?)_',       r'\1', text)
        text = re.sub(r'^#{1,6}\s*',    '',    text, flags=re.MULTILINE)
        text = re.sub(r'^[-*_]{3,}\s*$','',    text, flags=re.MULTILINE)
        text = re.sub(r'^[\*\-]\s+',    '• ',  text, flags=re.MULTILINE)
        return text.strip()

    def append_to_chat(self, message, panel_key="group"):
        def update_gui():
            sender = "System"
            text   = message
            reply_quote = None

            if message.startswith("[") and "]: " in message:
                parts  = message.split("]: ", 1)
                sender = parts[0][1:]
                text   = parts[1]
                if "|REPLY:" in sender:
                    sender, reply_quote = sender.split("|REPLY:", 1)
                    reply_quote = reply_quote.strip()

            is_me     = (sender == self.username)
            is_system = (sender == "System")
            is_ai     = ("AI" in sender)

            if is_ai:
                text = self._strip_markdown(text)

            if is_system:
                text_color  = TEXT_MUTED
                bubble_color = "transparent"
            else:
                text_color  = "white"
                bubble_color = BUBBLE_ME if is_me else (BUBBLE_AI if is_ai else BUBBLE_OTHER)

            panel = self.group_panel if panel_key == "group" else self.dm_tabs.get(panel_key)
            if panel is None:
                return

            self._append_bubble(panel, text, is_me=is_me, sender=sender,
                                 bubble_color=bubble_color, text_color=text_color,
                                 is_system=is_system, reply_quote=reply_quote)

            if is_ai or "AI Error" in text:
                for child in panel["scroll"].winfo_children():
                    try:
                        bf = child.winfo_children()[0]
                        for w in bf.winfo_children():
                            if isinstance(w, ctk.CTkLabel) and w.cget("text") == "AI กำลังพิมพ์คำตอบ...":
                                child.destroy(); break
                    except Exception:
                        pass

        update_gui()

    def _append_bubble(self, panel, text, is_me=False, sender="",
                        bubble_color=BUBBLE_OTHER, text_color="white",
                        is_system=False, reply_quote=None,
                        accent_color=None, tag=None):
        scroll = panel["scroll"]
        align  = "e" if is_me else "w"
        border_kwargs = {"border_width": 1, "border_color": BORDER_COLOR} \
            if (not is_me and not is_system and bubble_color not in (BUBBLE_AI, BUBBLE_DM)) else {}

        container = ctk.CTkFrame(scroll, fg_color="transparent")
        container.grid(row=panel["chat_row"], column=0, sticky="ew", pady=4, padx=6)
        panel["chat_row"] += 1
        container.grid_columnconfigure(0, weight=1)

        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=15, **border_kwargs)
        bubble.grid(row=0, column=0, sticky=align)

        if tag:
            ctk.CTkLabel(bubble, text=tag, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=accent_color or DM_ACCENT).pack(anchor="w", padx=10, pady=(4,0))

        if not is_me and not is_system:
            ctk.CTkLabel(bubble, text=sender,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#A0C4FF").pack(anchor="w", padx=10, pady=(5,0))

        if reply_quote:
            display = reply_quote if len(reply_quote) <= 60 else reply_quote[:57] + "..."
            ctk.CTkLabel(bubble, text=f"│ {display}",
                         font=ctk.CTkFont(size=11), text_color="#8A91A6",
                         justify="left").pack(anchor="w", padx=10, pady=(6,0))

        segments = re.split(r'(```.*?```)', text, flags=re.DOTALL)
        for seg in segments:
            if not seg:
                continue
            if seg.startswith('```') and seg.endswith('```'):
                lines = seg.strip().split('\n')
                lang  = lines[0][3:].strip()
                code  = '\n'.join(lines[1:-1]) if len(lines) >= 2 else seg[3:-3].strip()

                cc = ctk.CTkFrame(bubble, fg_color="#1E1E1E", corner_radius=8)
                cc.pack(padx=15, pady=5, fill="x", expand=True)
                hf = ctk.CTkFrame(cc, fg_color="#333333", height=30, corner_radius=8)
                hf.pack(fill="x")
                ctk.CTkLabel(hf, text=lang or "code", font=ctk.CTkFont(size=12),
                             text_color="gray").pack(side="left", padx=10)
                def _copy(c=code):
                    self.clipboard_clear(); self.clipboard_append(c)
                ctk.CTkButton(hf, text="Copy", width=50, height=24, font=ctk.CTkFont(size=12),
                              command=_copy).pack(side="right", padx=5, pady=3)
                ctk.CTkLabel(cc, text=code, font=ctk.CTkFont(family="Courier", size=13),
                             text_color="#D4D4D4", justify="left").pack(padx=10, pady=10, anchor="w")
            else:
                if seg.strip():
                    ctk.CTkLabel(bubble, text=seg.strip(), font=ctk.CTkFont(size=14),
                                 text_color=text_color, justify="left",
                                 wraplength=400).pack(padx=15, pady=(5,10), anchor="w")

        self._bind_drag_recursive(container)
        scroll._parent_canvas.update_idletasks()
        scroll._parent_canvas.yview_moveto(1.0)

    def _on_drag_start(self, event):
        self._drag_start_y    = event.y_root
        self._drag_start_view = self._active_canvas().yview()[0]

    def _on_drag_motion(self, event):
        try:
            canvas = self._active_canvas()
            bbox   = canvas.bbox("all")
            if not bbox or bbox[3] == 0:
                return
            delta    = event.y_root - self._drag_start_y
            fraction = -delta / bbox[3]
            new_pos  = max(0.0, min(1.0, self._drag_start_view + fraction))
            canvas.yview_moveto(new_pos)
        except Exception:
            pass

    def _active_canvas(self):
        if self.active_tab == "group":
            return self.group_panel["scroll"]._parent_canvas
        panel = self.dm_tabs.get(self.active_tab)
        if panel:
            return panel["scroll"]._parent_canvas
        return self.group_panel["scroll"]._parent_canvas

    def _bind_drag_recursive(self, widget):
        widget.bind("<ButtonPress-1>", self._on_drag_start, add="+")
        widget.bind("<B1-Motion>",     self._on_drag_motion, add="+")
        for child in widget.winfo_children():
            self._bind_drag_recursive(child)
