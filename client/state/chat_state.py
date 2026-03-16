from shared.network_constants import DEFAULT_CLIENT_HOST, SERVER_PORT


def initialize_client_state(app) -> None:
    """Initialize client network and UI runtime state on app startup."""
    app.host = DEFAULT_CLIENT_HOST
    app.port = SERVER_PORT
    app.client_socket = None
    app.username = ""
    app.online_users = []
    app.dm_tabs = {}
    app.active_tab = "group"
    app.unread_dms = {}
    app.dm_buttons = {}
    app.group_channel_buttons = {}
    app.blocked_usernames = set()


def reset_runtime_state(app) -> None:
    """Reset runtime-only UI/session state after disconnect."""
    app.unread_dms = {}
    app.dm_buttons = {}
    app.group_channel_buttons = {}
    app.online_users = []
    app.dm_tabs = {}
    app.active_tab = "group"
    app.blocked_usernames = set()
