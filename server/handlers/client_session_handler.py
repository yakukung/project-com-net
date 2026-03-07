from shared.messages import parse_client_message
from shared.protocol import recv_msg
from server.repositories.chat_repository import get_chat_repository
from server.routes.message_router import MessageRouter


def handle_client(client_socket) -> None:
    """Handle one connected client socket."""
    repository = get_chat_repository()
    router = MessageRouter(repository)
    username = None

    while True:
        try:
            raw_message = recv_msg(client_socket)
            if raw_message is None:
                break

            print(f"Received: {raw_message}")
            parsed = parse_client_message(raw_message)
            username = router.route(parsed, raw_message, client_socket, username)
        except Exception as exc:
            print(f"Client error: {exc}")
            break

    repository.remove_client(client_socket)
