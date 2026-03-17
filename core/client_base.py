"""
Base client functionality shared between GUI and CLI clients
"""

import socket
import threading
import hashlib
from .protocol import send, recv, SecureProtocol


class ChatClientBase:
    """Base class for chat clients with common functionality"""

    def __init__(self):
        self.sock = None
        self.username = ""
        self.current_room = ""
        self.rooms = []
        self.crypto = None
        self.running = False
        self.listen_thread = None
        self.token = None

    def connect(self, host, port, username, room, password=None):
        """Establish connection to server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(8)
            self.sock.connect((host, port))
            self.sock.settimeout(None)

            self.username = username
            self.current_room = room

            # Handle authentication if password provided
            if password:
                self.crypto = SecureProtocol(password)
                # Wait for auth challenge
                packet = recv(self.sock)
                if packet and packet.get("type") == "auth_challenge":
                    challenge = packet["challenge"]
                    hash_response = hashlib.sha256(
                        (challenge + password).encode()
                    ).hexdigest()
                    send(
                        self.sock,
                        {
                            "type": "auth_response",
                            "hash": hash_response,
                            "username": username,
                        },
                    )
                    # Get auth token
                    auth_packet = recv(self.sock)
                    if auth_packet and auth_packet.get("type") == "auth_success":
                        self.token = auth_packet["token"]
                    else:
                        raise Exception("Authentication failed")

            # Send join request
            join_packet = {"type": "join", "username": username, "room": room}
            if self.token:
                join_packet["token"] = self.token

            send(self.sock, join_packet, self.crypto)

            # Wait for join confirmation
            response = recv(self.sock, self.crypto)
            if not response or response.get("type") == "error":
                error_msg = response.get("msg") if response else "No response"
                raise Exception(error_msg)

            # Start listening thread
            self.running = True
            self.listen_thread = threading.Thread(target=self._listen, daemon=True)
            self.listen_thread.start()

            self.on_connected()
            self.on_joined(response)

        except Exception as e:
            self.on_error(str(e))
            self.disconnect()
            raise

    def _listen(self):
        """Background thread to receive messages"""
        try:
            while self.running and self.sock:
                packet = recv(self.sock, self.crypto)
                if not packet:
                    break
                self.on_message(packet)
        except Exception as e:
            if self.running:
                self.on_error(f"Connection lost: {e}")
        finally:
            self.disconnect()

    def send_message(self, message):
        """Send a public message"""
        if self.sock and self.running:
            send(self.sock, {"type": "message", "msg": message}, self.crypto)

    def send_private(self, target, message):
        """Send a private message"""
        if self.sock and self.running:
            send(
                self.sock,
                {"type": "private", "to": target, "msg": message},
                self.crypto,
            )

    def switch_room(self, room_name):
        """Switch to different room"""
        if self.sock and self.running and room_name != self.current_room:
            send(self.sock, {"type": "switch_room", "room": room_name}, self.crypto)

    def create_room(self, room_name):
        """Create a new room"""
        if self.sock and self.running and room_name:
            send(self.sock, {"type": "create_room", "room": room_name}, self.crypto)

    def request_room_list(self):
        """Request list of available rooms"""
        if self.sock and self.running:
            send(self.sock, {"type": "list_rooms"}, self.crypto)

    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        self.on_disconnect()

    # Callback methods to be overridden by clients
    def on_connected(self):
        """Called when connection established"""
        pass

    def on_joined(self, packet):
        """Called after joining a room"""
        if "room" in packet:
            self.current_room = packet["room"]
        if "users" in packet:
            self.on_user_list(packet["users"])
        if "history" in packet:
            for msg in packet["history"]:
                self.on_message(msg)

    def on_message(self, packet):
        """Called when a message is received"""
        pass

    def on_user_list(self, users):
        """Called when user list is updated"""
        pass

    def on_room_list(self, rooms):
        """Called when room list is updated"""
        self.rooms = rooms

    def on_error(self, error_msg):
        """Called when an error occurs"""
        pass

    def on_disconnect(self):
        """Called when disconnected"""
        pass
