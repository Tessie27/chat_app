"""
GUI Chat Client using Tkinter
"""
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import socket
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.client_base import ChatClientBase
from core.protocol import ts
from utils.portable import get_config_path, save_config, load_config

# Color scheme
BG = "#0d1117"
BG2 = "#161b22"
BG3 = "#21262d"
BORDER = "#30363d"
FG = "#e6edf3"
FG_DIM = "#8b949e"
GREEN = "#3fb950"
BLUE = "#58a6ff"
RED = "#f85149"
PINK = "#ff7eb3"

class ConnectDialog(tk.Toplevel):
    def __init__(self, parent, saved_config=None):
        super().__init__(parent)
        self.title("Connect to Server")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.saved_config = saved_config or {}
        self._build()
        self.grab_set()
        self.transient(parent)
        self.wait_window()

    def _build(self):
        pad = dict(padx=14, pady=6)

        tk.Label(self, text="Connect to Secure Chat", font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=FG).grid(row=0, column=0, columnspan=2, pady=(16, 10), padx=16)

        fields = [
            ("Username", "username", self.saved_config.get("username", "")),
            ("Password", "password", self.saved_config.get("password", "")),
            ("Server IP", "host", self.saved_config.get("host", "127.0.0.1")),
            ("Port", "port", self.saved_config.get("port", "5555")),
            ("Room", "room", self.saved_config.get("room", "General")),
        ]
        self.vars = {}
        self.entries = {}
        
        for i, (label, key, default) in enumerate(fields, start=1):
            tk.Label(self, text=label, font=("Segoe UI", 11),
                     bg=BG, fg=FG_DIM, anchor="e", width=10).grid(
                row=i, column=0, **pad)
            
            var = tk.StringVar(value=default)
            self.vars[key] = var
            
            if key == "password":
                entry = tk.Entry(self, textvariable=var, font=("Segoe UI", 11),
                               bg=BG3, fg=FG, insertbackground=FG, relief="flat",
                               highlightbackground=BORDER, highlightthickness=1,
                               width=24, show="*")
            else:
                entry = tk.Entry(self, textvariable=var, font=("Segoe UI", 11),
                               bg=BG3, fg=FG, insertbackground=FG, relief="flat",
                               highlightbackground=BORDER, highlightthickness=1,
                               width=24)
            entry.grid(row=i, column=1, **pad)
            self.entries[key] = entry

        # Save password checkbox
        self.save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="Save credentials locally", variable=self.save_var,
                      bg=BG, fg=FG, selectcolor=BG, activebackground=BG,
                      font=("Segoe UI", 10)).grid(
            row=len(fields)+1, column=0, columnspan=2, pady=(0, 10))

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=(8, 16))
        
        tk.Button(btn_frame, text="Connect", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg=BG, relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._connect).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                  bg=BG3, fg=FG, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=6)

        self.bind("<Return>", lambda e: self._connect())

    def _connect(self):
        self.result = {k: v.get().strip() for k, v in self.vars.items()}
        if self.save_var.get():
            save_config("last_connection.json", self.result)
        self.destroy()

class ChatClient(tk.Tk, ChatClientBase):
    def __init__(self):
        tk.Tk.__init__(self)
        ChatClientBase.__init__(self)
        
        self.title("Secure Chat")
        self.geometry("900x620")
        self.minsize(700, 480)
        self.configure(bg=BG)
        
        self.pm_target = None
        self.saved_config = load_config("last_connection.json")
        
        self._build_ui()
        self.after(100, self._prompt_connect)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill="x")

        self.title_lbl = tk.Label(top, text="Secure Chat", font=("Segoe UI", 13, "bold"),
                                  bg=BG2, fg=FG, padx=16, pady=8)
        self.title_lbl.pack(side="left")

        self.room_lbl = tk.Label(top, text="", font=("Segoe UI", 11),
                                 bg=BG2, fg=BLUE, padx=8)
        self.room_lbl.pack(side="left")

        self.conn_lbl = tk.Label(top, text="Not connected", font=("Segoe UI", 10),
                                 bg=BG2, fg=RED, padx=16)
        self.conn_lbl.pack(side="right")

        tk.Button(top, text="Connect", font=("Segoe UI", 10),
                  bg=BG3, fg=FG, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._prompt_connect).pack(side="right", padx=(0, 6))

        # Main area
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(main, bg=BG2, width=180,
                           highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        # Rooms section
        tk.Label(sidebar, text="ROOMS", font=("Segoe UI", 9, "bold"),
                 bg=BG2, fg=FG_DIM, anchor="w").pack(fill="x", padx=12, pady=(12, 4))

        self.room_list = tk.Listbox(
            sidebar, font=("Segoe UI", 11), bg=BG2, fg=FG,
            selectbackground=BG3, selectforeground=BLUE,
            relief="flat", highlightthickness=0, bd=0,
            activestyle="none"
        )
        self.room_list.pack(fill="x", padx=8)
        self.room_list.bind("<Double-Button-1>", self._switch_room)

        room_btns = tk.Frame(sidebar, bg=BG2)
        room_btns.pack(fill="x", padx=8, pady=(4, 8))
        tk.Button(room_btns, text="Join", font=("Segoe UI", 9),
                  bg=BG3, fg=FG, relief="flat", padx=8, pady=2,
                  cursor="hand2", command=self._join_room).pack(side="left", padx=(0, 4))
        tk.Button(room_btns, text="New", font=("Segoe UI", 9),
                  bg=BG3, fg=FG, relief="flat", padx=8, pady=2,
                  cursor="hand2", command=self._create_room).pack(side="left")

        # Divider
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)

        # Users section
        tk.Label(sidebar, text="ONLINE", font=("Segoe UI", 9, "bold"),
                 bg=BG2, fg=FG_DIM, anchor="w").pack(fill="x", padx=12, pady=(4, 4))

        self.user_list = tk.Listbox(
            sidebar, font=("Segoe UI", 11), bg=BG2, fg=GREEN,
            selectbackground=BG3, relief="flat",
            highlightthickness=0, bd=0, activestyle="none"
        )
        self.user_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.user_list.bind("<Double-Button-1>", self._start_private)

        tk.Label(sidebar, text="Double-click user to DM", font=("Segoe UI", 8),
                 bg=BG2, fg=FG_DIM).pack(padx=8, pady=(0, 8))

        # Chat area
        chat_area = tk.Frame(main, bg=BG)
        chat_area.pack(side="left", fill="both", expand=True)

        self.output = scrolledtext.ScrolledText(
            chat_area, font=("Segoe UI", 11), bg=BG, fg=FG,
            relief="flat", wrap="word", padx=14, pady=10,
            state="disabled", selectbackground=BG3,
            insertbackground=FG
        )
        self.output.pack(fill="both", expand=True)

        # Text tags for styling
        self.output.tag_config("ts", foreground=FG_DIM, font=("Segoe UI", 9))
        self.output.tag_config("name", foreground=BLUE, font=("Segoe UI", 11, "bold"))
        self.output.tag_config("self", foreground=GREEN, font=("Segoe UI", 11, "bold"))
        self.output.tag_config("msg", foreground=FG)
        self.output.tag_config("system", foreground=FG_DIM, font=("Segoe UI", 10, "italic"))
        self.output.tag_config("private", foreground=PINK, font=("Segoe UI", 11, "bold"))
        self.output.tag_config("pm_msg", foreground=PINK)
        self.output.tag_config("err", foreground=RED)

        # Input row
        input_row = tk.Frame(chat_area, bg=BG2,
                             highlightbackground=BORDER, highlightthickness=1)
        input_row.pack(fill="x")

        self.pm_label = tk.Label(input_row, text="", font=("Segoe UI", 10),
                                 bg=BG2, fg=PINK)
        self.pm_label.pack(side="left", padx=(10, 0))

        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            input_row, textvariable=self.input_var,
            font=("Segoe UI", 12), bg=BG2, fg=FG,
            insertbackground=FG, relief="flat",
            highlightthickness=0
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.input_box.bind("<Return>", lambda e: self._send_message())

        tk.Button(input_row, text="Send", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg=BG, relief="flat",
                  padx=16, pady=6, cursor="hand2",
                  command=self._send_message).pack(side="right", padx=(0, 10))

    def _prompt_connect(self):
        if self.sock:
            return
        dialog = ConnectDialog(self, self.saved_config)
        if not dialog.result:
            return
        r = dialog.result
        try:
            self.connect(r["host"], int(r["port"]), r["username"], r["room"], r["password"])
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    # Base class callbacks
    def on_connected(self):
        self.conn_lbl.configure(text=f"Connected as {self.username}", fg=GREEN)
        self.title(f"Secure Chat - {self.username}")
        if self.crypto:
            self._write_system("Secure connection enabled")

    def on_joined(self, packet):
        self.current_room = packet.get("room", self.current_room)
        self.room_lbl.configure(text=f"#{self.current_room}")
        self._clear_chat()
        self.request_room_list()

    def on_message(self, packet):
        ptype = packet.get("type")
        
        if ptype in ("message", "private", "system"):
            self._render(packet)
        elif ptype == "user_list":
            self._update_users(packet.get("users", []))
        elif ptype == "room_list":
            self._update_rooms(packet.get("rooms", []))

    def on_error(self, error_msg):
        messagebox.showerror("Error", error_msg)

    def on_disconnect(self):
        self.sock = None
        self.conn_lbl.configure(text="Disconnected", fg=RED)
        self.pm_target = None
        self.pm_label.configure(text="")
        self._write_system("Disconnected from server.")

    # GUI-specific methods
    def _render(self, packet):
        ptype = packet.get("type")
        time = packet.get("ts", ts())

        if ptype == "system":
            self._write(f"  {packet.get('msg', '')}\n", "system")

        elif ptype == "message":
            sender = packet.get("username", "?")
            msg = packet.get("msg", "")
            is_me = sender == self.username
            name_tag = "self" if is_me else "name"
            self._write(f"[{time}] ", "ts")
            self._write(f"{sender}: ", name_tag)
            self._write(f"{msg}\n", "msg")

        elif ptype == "private":
            sender = packet.get("from", "?")
            to = packet.get("to", "?")
            msg = packet.get("msg", "")
            is_sent = packet.get("self", False)
            if is_sent:
                self._write(f"[{time}] ", "ts")
                self._write(f"[DM to {to}] ", "private")
                self._write(f"{msg}\n", "pm_msg")
            else:
                self._write(f"[{time}] ", "ts")
                self._write(f"[DM from {sender}] ", "private")
                self._write(f"{msg}\n", "pm_msg")

        self.output.see("end")

    def _write(self, text, tag=None):
        self.output.configure(state="normal")
        if tag:
            self.output.insert("end", text, tag)
        else:
            self.output.insert("end", text)
        self.output.configure(state="disabled")

    def _write_system(self, msg):
        self._write(f"  {msg}\n", "system")

    def _clear_chat(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _update_users(self, users):
        self.user_list.delete(0, "end")
        for u in users:
            self.user_list.insert("end", f"  {u}")

    def _update_rooms(self, rooms):
        self.room_list.delete(0, "end")
        for r in rooms:
            self.room_list.insert("end", f"  #{r}")

    def _send_message(self):
        if not self.sock:
            messagebox.showwarning("Not Connected", "Connect to a server first.")
            return
        msg = self.input_var.get().strip()
        if not msg:
            return
        self.input_var.set("")

        if self.pm_target:
            self.send_private(self.pm_target, msg)
        else:
            self.send_message(msg)

    def _switch_room(self, event=None):
        if not self.sock:
            return
        sel = self.room_list.curselection()
        if not sel:
            return
        room = self.room_list.get(sel[0]).strip().lstrip("#")
        self.switch_room(room)

    def _join_room(self):
        if not self.sock:
            return
        room = simpledialog.askstring("Join Room", "Room name:", parent=self)
        if room:
            self.switch_room(room.strip())

    def _create_room(self):
        if not self.sock:
            return
        room = simpledialog.askstring("Create Room", "New room name:", parent=self)
        if room:
            self.create_room(room.strip())

    def _start_private(self, event=None):
        sel = self.user_list.curselection()
        if not sel:
            return
        target = self.user_list.get(sel[0]).strip()
        if target == self.username:
            return
        self.pm_target = target
        self.pm_label.configure(text=f"DM -> {target}  [Esc to cancel]")
        self.input_box.focus()
        self.bind("<Escape>", self._cancel_private)

    def _cancel_private(self, event=None):
        self.pm_target = None
        self.pm_label.configure(text="")
        self.unbind("<Escape>")

    def _on_closing(self):
        self.disconnect()
        self.destroy()

def main():
    app = ChatClient()
    app.mainloop()

if __name__ == "__main__":
    main()