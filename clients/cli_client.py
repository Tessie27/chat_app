"""
Command-line chat client with curses interface
"""
import sys
import os
import threading
import time
import socket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.protocol import ts
from core.client_base import ChatClientBase

class CLIClient(ChatClientBase):
    """Curses-based terminal chat client"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.messages = []
        self.input_buffer = ""
        self.current_channel = "General"
        self.users = []
        self.running = True
        
        # Initialize curses
        curses.curs_set(1)
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Timestamp
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Username
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # System
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Private
        
        super().__init__()
    
    def connect(self, host, port, username, room, password=None):
        """Connect to server with encryption"""
        super().connect(host, port, username, room, password)
    
    def start(self):
        """Start the CLI interface"""
        self._draw_screen()
        
        # Input thread
        while self.running:
            try:
                key = self.stdscr.getch()
                if key == 10:  # Enter
                    self._send_message()
                elif key == 27:  # Escape
                    self.running = False
                elif key == curses.KEY_BACKSPACE or key == 127:
                    self.input_buffer = self.input_buffer[:-1]
                elif 32 <= key <= 126:  # Printable characters
                    self.input_buffer += chr(key)
                self._draw_screen()
            except:
                break
    
    def _draw_screen(self):
        """Draw the curses interface"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Title bar
        title = f" Secure Chat - {self.username} @ #{self.current_channel} "
        self.stdscr.addstr(0, 0, title, curses.A_REVERSE)
        
        # Messages area
        msg_height = height - 3
        start_idx = max(0, len(self.messages) - msg_height)
        for i, msg in enumerate(self.messages[start_idx:]):
            if i >= msg_height:
                break
            color = 0
            if msg.startswith("[DM"):
                color = curses.color_pair(4)
            elif msg.startswith("  "):
                color = curses.color_pair(3)
            try:
                self.stdscr.addstr(i + 1, 0, msg[:width-1], color)
            except:
                pass
        
        # Users sidebar
        user_x = width - 20
        self.stdscr.addstr(1, user_x, "-" * 19, curses.A_DIM)
        self.stdscr.addstr(2, user_x, " Online Users ", curses.A_BOLD)
        for i, user in enumerate(self.users[:height-5]):
            self.stdscr.addstr(i + 3, user_x, f" {user}")
        
        # Input line
        self.stdscr.addstr(height-2, 0, "> " + self.input_buffer)
        self.stdscr.addstr(height-2, len(self.input_buffer) + 2, " ")
        
        self.stdscr.refresh()
    
    def _send_message(self):
        """Send message from input buffer"""
        if self.input_buffer.startswith("/"):
            self._handle_command(self.input_buffer)
        elif self.input_buffer.strip():
            self.send_message(self.input_buffer)
        self.input_buffer = ""
    
    def _handle_command(self, cmd):
        """Handle slash commands"""
        parts = cmd.split()
        if parts[0] == "/join" and len(parts) > 1:
            self.switch_room(parts[1])
        elif parts[0] == "/create" and len(parts) > 1:
            self.create_room(parts[1])
        elif parts[0] == "/dm" and len(parts) > 2:
            self.send_private(parts[1], " ".join(parts[2:]))
        elif parts[0] == "/quit":
            self.running = False
        elif parts[0] == "/help":
            self._show_help()
    
    def _show_help(self):
        """Show help message"""
        help_msg = [
            "Commands:",
            "  /join <room>     - Switch to room",
            "  /create <room>   - Create new room",
            "  /dm <user> <msg> - Send private message",
            "  /quit           - Exit chat",
            "  /help           - Show this help"
        ]
        for msg in help_msg:
            self.messages.append(f"  {msg}")
    
    def on_message(self, packet):
        """Handle incoming messages"""
        if packet["type"] == "message":
            self.messages.append(
                f"[{packet['ts']}] {packet['username']}: {packet['msg']}"
            )
        elif packet["type"] == "private":
            if packet.get("self"):
                self.messages.append(
                    f"[{packet['ts']}] [DM to {packet['to']}]: {packet['msg']}"
                )
            else:
                self.messages.append(
                    f"[{packet['ts']}] [DM from {packet['from']}]: {packet['msg']}"
                )
        elif packet["type"] == "system":
            self.messages.append(f"  {packet['msg']}")
        elif packet["type"] == "user_list":
            self.users = packet.get("users", [])
    
    def on_connected(self):
        """Handle successful connection"""
        self.messages.append(f"  Connected as {self.username}")
        if self.crypto:
            self.messages.append("  Secure connection enabled")
    
    def on_disconnect(self):
        """Handle disconnection"""
        self.messages.append("  Disconnected from server")
        time.sleep(2)
        self.running = False

def main(stdscr):
    client = CLIClient(stdscr)
    
    # Connection dialog in terminal
    stdscr.clear()
    stdscr.addstr(0, 0, "=== Secure Chat Client ===")
    stdscr.addstr(2, 0, "Server: ")
    curses.echo()
    host = stdscr.getstr(2, 8).decode()
    stdscr.addstr(3, 0, "Port (5555): ")
    port_str = stdscr.getstr(3, 13).decode()
    port = int(port_str) if port_str else 5555
    stdscr.addstr(4, 0, "Username: ")
    username = stdscr.getstr(4, 10).decode()
    stdscr.addstr(5, 0, "Room (General): ")
    room = stdscr.getstr(5, 16).decode() or "General"
    stdscr.addstr(6, 0, "Password (optional): ")
    curses.noecho()
    password = stdscr.getstr(6, 22).decode() or None
    curses.noecho()
    
    try:
        client.connect(host, port, username, room, password)
        client.start()
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Error: {e}")
        stdscr.addstr(2, 0, "Press any key to exit...")
        stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)