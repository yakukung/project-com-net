import socket
import re

class NetworkMixin:
    def _handle_disconnect(self, error_msg):
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None

        if hasattr(self, 'main_container') and self.main_container.winfo_exists():
            self.main_container.destroy()

        self.online_users = []
        self.dm_tabs = {}
        self.active_tab = "group"
        self.unread_dms = {}
        
        self.show_login_frame()
        self.error_label.configure(text=error_msg)

    def connect_to_server(self):
        username = self.username_entry.get().strip()
        host = self.host_entry.get().strip() or "127.0.0.1"
        
        if not username:
            self.error_label.configure(text="Username cannot be empty")
            return
            
        self.username = username
        self.host = host
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.settimeout(None)
            
            self.show_chat_frame()

            join_msg = f"{self.username} has joined the chat!"
            msg_bytes = join_msg.encode('utf-8')
            self.client_socket.send(f"{len(msg_bytes):<10}".encode('utf-8'))
            self.client_socket.send(msg_bytes)
        except Exception as e:
            self.error_label.configure(text=f"Connection failed: {str(e)}")

    def send_message(self):
        message = self.message_input.get().strip()
        if not message:
            return
        try:
            if self.active_tab != "group" and not message.startswith("@"):
                message = f"@{self.active_tab} {message}"

            if not message.startswith("@"):
                message = f"[{self.username}]: {message}"

            msg_bytes = message.encode('utf-8')
            self.client_socket.send(f"{len(msg_bytes):<10}".encode('utf-8'))
            self.client_socket.send(msg_bytes)
            self.message_input.delete(0, 'end')
        except Exception as e:
            self.append_to_chat(f"[System]: Error sending message ({e})", "group")
            if self.client_socket:
                try:
                    self.client_socket.close()
                except Exception:
                    pass
                self.client_socket = None

    def receive_messages(self):
        while True:
            try:
                length_str = self.client_socket.recv(10).decode('utf-8').strip()
                if not length_str:
                    break
                msg_length = int(length_str)

                chunks, received = [], 0
                while received < msg_length:
                    chunk = self.client_socket.recv(min(msg_length - received, 4096))
                    if not chunk:
                        raise RuntimeError("Connection broken")
                    chunks.append(chunk)
                    received += len(chunk)

                message = b''.join(chunks).decode('utf-8')

                if message == "[System|ERROR]: Username already taken.":
                    self.after(0, lambda: self._handle_disconnect("Username already taken. Please choose another."))
                    break

                user_list_match = re.match(r'^\[System\|USERS:(.*?)\]$', message)
                if user_list_match:
                    users = [u for u in user_list_match.group(1).split(",") if u]
                    self.after(0, lambda u=users: self._update_user_list(u))
                    continue

                dm_from = re.match(r'^\[DM\|FROM:(.+?)\]: (.+)$', message, re.DOTALL)
                if dm_from:
                    sender = dm_from.group(1)
                    text   = dm_from.group(2)
                    self.after(0, lambda s=sender, t=text: self._handle_dm_received(s, t))
                    continue

                dm_to = re.match(r'^\[DM\|TO:(.+?)\]: (.+)$', message, re.DOTALL)
                if dm_to:
                    recipient = dm_to.group(1)
                    text      = dm_to.group(2)
                    self.after(0, lambda r=recipient, t=text: self._handle_dm_sent(r, t))
                    continue

                self.after(0, lambda m=message: self.append_to_chat(m, "group"))

            except Exception as e:
                print(f"Disconnected: {e}")
                if hasattr(self, 'main_container') and self.main_container.winfo_exists():
                    self.after(0, lambda: self._handle_disconnect("Disconnected from server. Please reconnect."))
                break

        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None

    def _handle_dm_received(self, sender, text):
        if sender not in self.dm_tabs:
            self._create_dm_tab(sender)
        from shared.config import BUBBLE_DM, DM_ACCENT
        self._append_bubble(self.dm_tabs[sender], text, is_me=False, sender=sender,
                            bubble_color=BUBBLE_DM, accent_color=DM_ACCENT)
        if self.active_tab != sender:
            self.unread_dms[sender] = self.unread_dms.get(sender, 0) + 1
            self._refresh_dm_button(sender)

    def _handle_dm_sent(self, recipient, text):
        if recipient not in self.dm_tabs:
            self._create_dm_tab(recipient)
        from shared.config import BUBBLE_ME
        self._append_bubble(self.dm_tabs[recipient], text, is_me=True,
                            sender=self.username, bubble_color=BUBBLE_ME)
