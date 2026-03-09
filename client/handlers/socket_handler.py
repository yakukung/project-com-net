import socket

import customtkinter as ctk

from client.handlers.inbound_router import dispatch_server_message
from client.services.group_service import (
    build_add_group_members_payload,
    build_group_kick_payload,
    build_group_owner_transfer_payload,
)
from client.services.message_service import build_outbound_message
from client.state.chat_state import reset_runtime_state
from shared.network_constants import DEFAULT_CLIENT_HOST
from shared.validation import validate_username
from shared.messages import build_join_message
from shared.protocol import recv_msg, send_msg as protocol_send_msg


class SocketHandlerMixin:
    def _close_client_socket(self) -> None:
        if not self.client_socket:
            return

        try:
            self.client_socket.close()
        except Exception:
            pass

        self.client_socket = None

    def _reset_runtime_state(self) -> None:
        reset_runtime_state(self)

    def _handle_disconnect(self, error_msg: str) -> None:
        self._close_client_socket()

        if hasattr(self, "main_container") and self.main_container.winfo_exists():
            self.main_container.destroy()

        self._reset_runtime_state()
        self.show_login_frame()
        self.error_label.configure(text=error_msg)

    def connect_to_server(self) -> None:
        username = self.username_entry.get().strip()
        host = self.host_entry.get().strip() or DEFAULT_CLIENT_HOST

        if not username:
            self.error_label.configure(text="Username cannot be empty")
            return

        invalid_reason = validate_username(username)
        if invalid_reason:
            error_map = {
                "empty": "ชื่อผู้ใช้ต้องไม่ว่าง",
                "too_long": "ชื่อผู้ใช้ยาวเกินไป (สูงสุด 24 ตัวอักษร)",
                "invalid_chars": "ชื่อผู้ใช้มีอักขระที่ไม่อนุญาต หรือมีช่องว่าง",
                "reserved": "ชื่อผู้ใช้นี้ไม่สามารถใช้งานได้ (คำสงวน)"
            }
            msg = error_map.get(invalid_reason, "ชื่อผู้ใช้ไม่ถูกต้อง")
            self.error_label.configure(text=msg)
            return

        self.username = username
        self.host = host

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.settimeout(None)

            self.show_chat_frame()
            self.send_raw(build_join_message(self.username))
        except Exception as exc:
            self._close_client_socket()
            self._show_connection_error(host, str(exc))

    def _show_connection_error(self, host: str, reason: str) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title("ไม่สามารถเชื่อมต่อได้")
        popup.geometry("380x220")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(fg_color="#1A1D2E")

        popup.update_idletasks()
        pos_x = self.winfo_x() + (self.winfo_width() // 2) - 190
        pos_y = self.winfo_y() + (self.winfo_height() // 2) - 110
        popup.geometry(f"+{pos_x}+{pos_y}")

        ctk.CTkLabel(
            popup,
            text="⚠️  ไม่พบ Server",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FF5370",
        ).pack(pady=(28, 6))

        ctk.CTkLabel(
            popup,
            text=f"ไม่สามารถเชื่อมต่อ  {host}  ได้",
            font=ctk.CTkFont(size=13),
            text_color="#A0A8CC",
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            popup,
            text=reason,
            font=ctk.CTkFont(size=11),
            text_color="#6B728E",
            wraplength=320,
        ).pack(pady=(0, 18))

        ctk.CTkButton(
            popup,
            text="ตกลง",
            width=120,
            height=36,
            fg_color="#FF4081",
            hover_color="#C2185B",
            corner_radius=18,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=popup.destroy,
        ).pack()

    def send_raw(self, message: str) -> None:
        if not self.client_socket:
            return

        try:
            protocol_send_msg(self.client_socket, message)
        except Exception as exc:
            print(f"send_raw error: {exc}")

    def send_message(self) -> None:
        message = self.message_input.get().strip()
        if not message:
            return

        try:
            outbound = build_outbound_message(self.active_tab, self.username, message)
            self.send_raw(outbound)
            self.message_input.delete(0, "end")
        except Exception as exc:
            self.append_to_chat(f"[System]: Error sending message ({exc})", "group")
            self._close_client_socket()

    def receive_messages(self) -> None:
        while True:
            try:
                if not self.client_socket:
                    break

                message = recv_msg(self.client_socket)
                if message is None:
                    break

                action = dispatch_server_message(self, message)
                if action == "stop":
                    break
                if action == "unhandled":
                    self.after(0, lambda m=message: self.append_to_chat(m, "group"))
            except Exception as exc:
                print(f"Disconnected: {exc}")
                if hasattr(self, "main_container") and self.main_container.winfo_exists():
                    self.after(
                        0,
                        lambda: self._handle_disconnect("Disconnected from server. Please reconnect."),
                    )
                break

        self._close_client_socket()

    def _on_kick_group_member(self, group_id: str, username: str) -> None:
        self.send_raw(build_group_kick_payload(group_id, username))

    def _on_transfer_group_owner(self, group_id: str, members: list[str]) -> None:
        from client.ui.dialogs.group_owner_transfer_dialog import GroupOwnerTransferDialog

        GroupOwnerTransferDialog(
            self,
            members,
            self.username,
            on_confirm=lambda username: self._on_confirm_transfer(group_id, username),
        )

    def _on_confirm_transfer(self, group_id: str, new_owner: str) -> None:
        self.send_raw(build_group_owner_transfer_payload(group_id, new_owner))

    def _on_click_add_member(self, group_id: str, existing_members: list[str]) -> None:
        from client.ui.dialogs.group_create_dialog import GroupMemberAddDialog

        GroupMemberAddDialog(
            self,
            self.online_users,
            existing_members,
            on_confirm=lambda members: self._on_confirm_add_members(group_id, members),
        )

    def _on_confirm_add_members(self, group_id: str, new_members: list[str]) -> None:
        self.send_raw(build_add_group_members_payload(group_id, new_members))

    def _remove_group_tab(self, group_id: str) -> None:
        if group_id in self.group_panels:
            self.group_panels[group_id]["frame"].destroy()
            del self.group_panels[group_id]

        if group_id in self.group_channel_buttons:
            self.group_channel_buttons[group_id].destroy()
            del self.group_channel_buttons[group_id]

        if group_id in self.group_names:
            del self.group_names[group_id]

        if self.active_tab == f"group:{group_id}":
            self.switch_tab("group")
