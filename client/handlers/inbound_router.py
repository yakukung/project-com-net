from client.ui.theme import BUBBLE_DM, BUBBLE_ME, DM_ACCENT
from shared.models import MessageKind
from shared.messages import parse_server_message


def _handle_dm_received(app, sender: str, text: str) -> None:
    blocked = getattr(app, "blocked_usernames", set())
    blocked_lower = {name.lower() for name in blocked}
    if sender.lower() in blocked_lower:
        return

    if sender not in app.dm_tabs:
        app._create_dm_tab(sender)

    app._append_bubble(
        app.dm_tabs[sender],
        text,
        is_me=False,
        sender=sender,
        bubble_color=BUBBLE_DM,
        accent_color=DM_ACCENT,
    )

    if app.active_tab != sender:
        app.unread_dms[sender] = app.unread_dms.get(sender, 0) + 1
        app._refresh_dm_button(sender)


def _handle_dm_sent(app, recipient: str, text: str) -> None:
    blocked = getattr(app, "blocked_usernames", set())
    blocked_lower = {name.lower() for name in blocked}
    if recipient.lower() in blocked_lower:
        return

    if recipient not in app.dm_tabs:
        app._create_dm_tab(recipient)

    app._append_bubble(
        app.dm_tabs[recipient],
        text,
        is_me=True,
        sender=app.username,
        bubble_color=BUBBLE_ME,
    )


def dispatch_server_message(app, message: str) -> str:
    parsed = parse_server_message(message)

    if parsed.kind == MessageKind.USERNAME_TAKEN_ERROR:
        app.after(0, lambda: app._handle_disconnect("Username already taken. Please choose another."))
        return "stop"

    if parsed.kind == MessageKind.LOGIN_ERROR:
        reason = parsed.data.get("reason", "Login failed")
        app.after(0, lambda r=reason: app._handle_disconnect(r))
        return "stop"

    if parsed.kind == MessageKind.USERS:
        users = parsed.data["users"]
        app.online_users = users
        app.after(0, lambda users=users: app._update_user_list(users))
        return "handled"

    if parsed.kind == MessageKind.DM_FROM:
        sender, text = parsed.data["sender"], parsed.data["text"]
        app.after(0, lambda sender=sender, text=text: _handle_dm_received(app, sender, text))
        return "handled"

    if parsed.kind == MessageKind.DM_TO:
        recipient, text = parsed.data["target"], parsed.data["text"]
        app.after(0, lambda recipient=recipient, text=text: _handle_dm_sent(app, recipient, text))
        return "handled"

    if parsed.kind == MessageKind.DM_AI:
        partner, inner = parsed.data["partner"], parsed.data["inner"]

        def show_ai_dm(partner_name=partner, inner_message=inner) -> None:
            if partner_name not in app.dm_tabs:
                app._create_dm_tab(partner_name)
            app.append_to_chat(inner_message, partner_name)

        app.after(0, show_ai_dm)
        return "handled"

    if parsed.kind == MessageKind.GROUP_CREATED:
        group_id, group_name = parsed.data["group_id"], parsed.data["group_name"]

        def on_group_created(new_group_id=group_id, new_group_name=group_name) -> None:
            app.group_names[new_group_id] = new_group_name
            app._create_group_panel(new_group_id)
            app._add_group_channel_button(new_group_id, new_group_name)
            app.switch_tab(f"group:{new_group_id}")

        app.after(0, on_group_created)
        return "handled"

    if parsed.kind == MessageKind.ERROR:
        reason = parsed.data.get("reason", "เกิดข้อผิดพลาดขึ้น")
        def show_error(r=reason):
            if hasattr(app, "_show_error_popup"):
                app._show_error_popup("ข้อผิดพลาดจาก Server", r)
        app.after(0, show_error)
        return "handled"

    if parsed.kind == MessageKind.GROUP_MEMBERS:
        group_id = parsed.data["group_id"]
        members = parsed.data["members"]
        owner_name = parsed.data["owner"]
        group_name = app.group_names.get(group_id, group_id)

        def show_members() -> None:
            from client.ui.dialogs.group_members_dialog import GroupMembersDialog

            GroupMembersDialog(
                app,
                group_id,
                group_name,
                members,
                owner_name,
                app.username,
                app._on_kick_group_member,
                app._on_transfer_group_owner,
                app._on_click_add_member,
                app._on_delete_group_by_id,
            )

        app.after(0, show_members)
        return "handled"

    if parsed.kind == MessageKind.GROUP_OWNERSHIP_CHANGED:
        group_id = parsed.data["group_id"]
        new_owner = parsed.data["new_owner"]
        panel_key = f"group:{group_id}"

        def show_ownership_changed() -> None:
            if group_id not in app.group_panels:
                app._create_group_panel(group_id)
            app.append_to_chat(f"[System]: 👑 {new_owner} เป็นเจ้าของช่องแชทคนใหม่", panel_key)

        app.after(0, show_ownership_changed)
        return "handled"

    if parsed.kind == MessageKind.GROUP_KICKED:
        group_id = parsed.data["group_id"]
        app.after(0, lambda group_id=group_id: app._remove_group_tab(group_id))
        return "handled"

    if parsed.kind == MessageKind.GROUP_DELETED:
        group_id = parsed.data["group_id"]
        app.after(0, lambda group_id=group_id: app._remove_group_tab(group_id))
        return "handled"

    if parsed.kind == MessageKind.GROUP_CHAT:
        group_id = parsed.data["group_id"]
        sender_name = parsed.data["sender"]
        reply_quote = parsed.data["reply_quote"]
        text = parsed.data["text"]
        panel_key = f"group:{group_id}"
        inner_message = f"[{sender_name}]: {text}"
        if reply_quote:
            inner_message = f"[{sender_name}|REPLY:{reply_quote}]: {text}"

        def show_group_message() -> None:
            if group_id not in app.group_panels:
                app._create_group_panel(group_id)
            app.append_to_chat(inner_message, panel_key)

        app.after(0, show_group_message)
        return "handled"

    return "unhandled"
