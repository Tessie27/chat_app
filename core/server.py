"""
Chat Server with encryption support
"""

import socket
import threading
import json
import sys
import hashlib
import secrets
from datetime import datetime
from .protocol import send, recv, SecureProtocol, ts

HOST = "0.0.0.0"
DEFAULT_PORT = 5555
BUFFER = 4096


def log(msg):
    print(f"[{ts()}] {msg}")


class Room:
    def __init__(self, name):
        self.name = name
        self.clients = {}  # socket -> username
        self.history = []  # last 50 messages

    def add(self, sock, username):
        self.clients[sock] = username

    def remove(self, sock):
        self.clients.pop(sock, None)

    def broadcast(self, packet, exclude=None):
        dead = []
        for s in list(self.clients):
            if s == exclude:
                continue
            try:
                send(s, packet)
            except Exception:
                dead.append(s)
        for s in dead:
            self.clients.pop(s, None)

    def user_list(self):
        return sorted(self.clients.values())

    def store(self, packet):
        self.history.append(packet)
        if len(self.history) > 50:
            self.history.pop(0)


class Server:
    def __init__(self, port, password=None):
        self.port = port
        self.password = password
        self.crypto = SecureProtocol(password) if password else None
        self.clients = {}  # socket -> {username, room}
        self.rooms = {}  # name -> Room
        self.auth_tokens = {}  # token -> username
        self.lock = threading.Lock()
        self._get_room("General")  # default room

    def _get_room(self, name):
        if name not in self.rooms:
            self.rooms[name] = Room(name)
            log(f"Room created: #{name}")
        return self.rooms[name]

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, self.port))
        server_sock.listen()
        log(f"Server listening on port {self.port}")
        if self.password:
            log("Password protection enabled")

        while True:
            try:
                conn, addr = server_sock.accept()
                log(f"New connection from {addr[0]}:{addr[1]}")
                threading.Thread(
                    target=self._handle_client, args=(conn, addr), daemon=True
                ).start()
            except KeyboardInterrupt:
                log("Server shutting down.")
                break

    def _handle_client(self, sock, addr):
        username = None
        token = None
        try:
            # Authentication phase if password is set
            if self.password:
                # Send challenge
                challenge = secrets.token_hex(16)
                send(sock, {"type": "auth_challenge", "challenge": challenge})

                # Receive response
                response = recv(sock)
                if not response or response.get("type") != "auth_response":
                    sock.close()
                    return

                # Verify password hash
                expected = hashlib.sha256(
                    (challenge + self.password).encode()
                ).hexdigest()
                if response.get("hash") != expected:
                    send(sock, {"type": "error", "msg": "Invalid password"})
                    sock.close()
                    return

                # Generate auth token
                token = secrets.token_urlsafe(32)
                self.auth_tokens[token] = response.get("username")
                send(sock, {"type": "auth_success", "token": token})

            # Expect a JOIN packet
            packet = recv(sock, self.crypto)
            if not packet or packet.get("type") != "join":
                sock.close()
                return

            # Verify token if using password
            if self.password and packet.get("token") != token:
                sock.close()
                return

            username = packet.get("username", "").strip()
            room_name = packet.get("room", "General").strip() or "General"

            if not username:
                send(sock, {"type": "error", "msg": "Username cannot be empty."})
                sock.close()
                return

            with self.lock:
                # Check username not taken
                taken = any(
                    c["username"].lower() == username.lower()
                    for c in self.clients.values()
                )
                if taken:
                    send(
                        sock,
                        {
                            "type": "error",
                            "msg": f"Username '{username}' is already taken.",
                        },
                    )
                    sock.close()
                    return

                room = self._get_room(room_name)
                room.add(sock, username)
                self.clients[sock] = {"username": username, "room": room_name}

            log(f"{username} joined #{room_name} from {addr[0]}")

            # Confirm join + send history + user list
            send(
                sock,
                {
                    "type": "joined",
                    "room": room_name,
                    "users": room.user_list(),
                    "history": room.history,
                },
            )

            # Announce to room
            announce = {
                "type": "system",
                "msg": f"{username} joined #{room_name}",
                "ts": ts(),
            }
            room.store(announce)
            room.broadcast(announce, exclude=sock)
            self._send_user_list(room)

            # Main loop
            while True:
                packet = recv(sock, self.crypto)
                if not packet:
                    break
                self._route(sock, packet)

        except Exception as e:
            log(f"Error with {username or addr}: {e}")
        finally:
            self._disconnect(sock, username)

    def _route(self, sock, packet):
        ptype = packet.get("type")

        if ptype == "message":
            self._handle_message(sock, packet)
        elif ptype == "private":
            self._handle_private(sock, packet)
        elif ptype == "switch_room":
            self._handle_switch(sock, packet)
        elif ptype == "create_room":
            self._handle_create_room(sock, packet)
        elif ptype == "list_rooms":
            self._send_room_list(sock)

    def _handle_message(self, sock, packet):
        with self.lock:
            info = self.clients.get(sock)
            if not info:
                return
            room = self.rooms.get(info["room"])
            if not room:
                return

        out = {
            "type": "message",
            "username": info["username"],
            "msg": packet.get("msg", "").strip(),
            "room": info["room"],
            "ts": ts(),
        }
        if not out["msg"]:
            return

        room.store(out)
        room.broadcast(out)

    def _handle_private(self, sock, packet):
        with self.lock:
            sender = self.clients.get(sock, {}).get("username", "?")
            target_name = packet.get("to", "").strip()
            target_sock = next(
                (
                    s
                    for s, c in self.clients.items()
                    if c["username"].lower() == target_name.lower()
                ),
                None,
            )

        if not target_sock:
            send(
                sock,
                {
                    "type": "system",
                    "msg": f"User '{target_name}' not found.",
                    "ts": ts(),
                },
            )
            return

        out = {
            "type": "private",
            "from": sender,
            "to": target_name,
            "msg": packet.get("msg", "").strip(),
            "ts": ts(),
        }
        send(target_sock, out)
        send(sock, {**out, "self": True})

    def _handle_switch(self, sock, packet):
        new_room_name = packet.get("room", "General").strip() or "General"

        with self.lock:
            info = self.clients.get(sock)
            if not info:
                return
            old_room = self.rooms.get(info["room"])
            username = info["username"]

            if old_room:
                old_room.remove(sock)
                leave_msg = {
                    "type": "system",
                    "msg": f"{username} left #{info['room']}",
                    "ts": ts(),
                }
                old_room.broadcast(leave_msg)
                self._send_user_list(old_room)

            new_room = self._get_room(new_room_name)
            new_room.add(sock, username)
            info["room"] = new_room_name

        log(f"{username} switched to #{new_room_name}")

        send(
            sock,
            {
                "type": "switched",
                "room": new_room_name,
                "users": new_room.user_list(),
                "history": new_room.history,
            },
        )

        join_msg = {
            "type": "system",
            "msg": f"{username} joined #{new_room_name}",
            "ts": ts(),
        }
        new_room.store(join_msg)
        new_room.broadcast(join_msg, exclude=sock)
        self._send_user_list(new_room)

    def _handle_create_room(self, sock, packet):
        name = packet.get("room", "").strip()
        if name:
            with self.lock:
                self._get_room(name)
            send(
                sock,
                {
                    "type": "system",
                    "msg": f"Room #{name} is ready.",
                    "ts": ts(),
                },
            )
            self._send_room_list(sock)

    def _send_user_list(self, room):
        room.broadcast(
            {
                "type": "user_list",
                "users": room.user_list(),
                "room": room.name,
            }
        )

    def _send_room_list(self, sock):
        with self.lock:
            rooms = list(self.rooms.keys())
        send(sock, {"type": "room_list", "rooms": rooms})

    def _disconnect(self, sock, username):
        with self.lock:
            info = self.clients.pop(sock, None)
            if info:
                room = self.rooms.get(info["room"])
                if room:
                    room.remove(sock)
                    msg = {
                        "type": "system",
                        "msg": f"{username} left the chat",
                        "ts": ts(),
                    }
                    room.store(msg)
                    room.broadcast(msg)
                    self._send_user_list(room)
        try:
            sock.close()
        except Exception:
            pass
        if username:
            log(f"{username} disconnected")
