# Secure Chat

A secure, encrypted chat application with both GUI and CLI interfaces. Features end-to-end encryption, private messaging, and multi-room support.

## 📋 Features

- **End-to-End Encryption** - Password-based encryption for secure communication
- **Multi-Room Support** - Create and join multiple chat rooms
- **Private Messaging** - Direct messages between users
- **Dual Interface** - GUI (Tkinter) and CLI (curses/text) clients
- **Portable Mode** - Run from USB drive without installation
- **User Authentication** - Optional password protection for servers
- **Message History** - View recent messages when joining rooms
- **Cross-Platform** - Works on Windows, macOS, and Linux

## 📁 Project Structure

```
secure-chat/
├── chat.py                 # Main launcher script
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── core/                   # Core networking modules
│   ├── __init__.py
│   ├── protocol.py         # Encryption & communication protocol
│   ├── server.py           # Chat server implementation
│   └── client_base.py      # Shared client functionality
├── clients/                # Client implementations
│   ├── __init__.py
│   ├── gui_client.py       # Tkinter GUI client
│   └── cli_client.py       # Curses/Text CLI client
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── crypto.py           # Cryptographic functions
│   └── portable.py         # Portable mode helpers
└── config/                 # Configuration management
    ├── __init__.py
    └── settings.py         # Settings manager
```

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Install

1. **Clone or download** the application
2. **Open a terminal** in the application folder
3. **Install dependencies:**

```bash
pip install cryptography
```

For CLI client on Windows (optional):
```bash
pip install windows-curses
```

## 🚀 Usage

### Starting the Server

First, start a server instance:

```bash
# Basic server
python chat.py server

# Server with password protection
python chat.py server --password mysecret

# Server on different port
python chat.py server --port 8888 --password mysecret
```

The server will display:
```
[10:30:15] Server listening on port 5555
```

**Keep this terminal window open** while clients connect.

### Starting a Client

Open a **new terminal window** for each client:

#### GUI Client (Recommended)
```bash
python chat.py gui
```

#### CLI Client
```bash
python chat.py cli
```

#### Portable Mode (Run from USB)
```bash
python chat.py gui --portable
```

### Connecting to the Server

#### In GUI Mode:
A connection dialog will appear. Enter:
- **Server IP**: `127.0.0.1` (for local) or server's IP address
- **Port**: `5555` (unless changed)
- **Username**: Your chosen name
- **Room**: `General` (or any room name)
- **Password**: Required if server has password protection

Click **Connect** to join the chat.

#### In CLI Mode:
You'll be prompted for:
```
Server: 127.0.0.1
Port (5555): 5555
Username: YourName
Room (General): General
Password (optional):
```

## 💬 CLI Commands

Once connected in CLI mode, use these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `/join <room>` | Switch to a different room | `/join gaming` |
| `/create <room>` | Create a new room | `/create music` |
| `/dm <user> <msg>` | Send private message | `/dm Alice Hello!` |
| `/quit` | Exit the chat | `/quit` |
| `/help` | Show available commands | `/help` |

## 🎨 GUI Features

The GUI client includes:
- **Dark theme** for comfortable viewing
- **User list sidebar** showing online users
- **Room list** with available channels
- **Double-click** users to start private messaging
- **Message history** when joining rooms
- **Connection status indicator**
- **Secure connection** notification when encryption is enabled

## 🔐 Security Features

- **Password-based encryption** using PBKDF2 key derivation
- **Fernet symmetric encryption** for messages
- **Challenge-response authentication** prevents replay attacks
- **Secure token-based sessions**
- **No plaintext password storage**
- **Optional server password** protection

## 🌐 Network Configuration

### Local Network Usage
To connect from another computer on your network:
1. Find server's IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. Use that IP in client connection dialog
3. Ensure firewall allows the port (default 5555)

### Internet Usage
To connect over the internet:
1. Configure port forwarding on your router
2. Use your public IP address
3. Consider using a VPN for security

## 🐛 Troubleshooting

### Common Issues

**"No module named 'cryptography'"**
```bash
pip install cryptography
```

**"No module named 'windows-curses'"** (Windows CLI)
```bash
pip install windows-curses
```

**GUI won't start on Linux**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

**"Address already in use"**
- Another server is running on the same port
- Change port with `--port` option
- Wait a few minutes for the port to clear

**Can't connect to server**
- Verify server is running
- Check IP address and port
- Disable firewall temporarily to test
- Use `127.0.0.1` for local connections

## 📝 Examples

### Example 1: Local Chat with Two Users

**Terminal 1 (Server):**
```bash
python chat.py server
```

**Terminal 2 (Alice):**
```bash
python chat.py gui
# Connect as "Alice" to 127.0.0.1:5555
```

**Terminal 3 (Bob):**
```bash
python chat.py cli
# Connect as "Bob" to 127.0.0.1:5555
```

### Example 2: Password-Protected Server

**Server:**
```bash
python chat.py server --password secret123
```

**Client:**
```bash
python chat.py gui
# Enter "secret123" in password field
```

### Example 3: Portable Mode from USB

```bash
# On USB drive
E:\secure-chat> python chat.py gui --portable
# All settings saved to E:\secure-chat\chat_data\
```

## 🔧 Development

### Running Tests
```bash
# Install development dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/

# Check code style
black .
flake8
```

### Creating a Portable Package
```bash
# Install PyInstaller
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile --windowed chat.py
```

## 📜 License

This project is open-source software. Use at your own risk.

## 🙏 Acknowledgments

- Built with Python's standard library
- Encryption provided by `cryptography` library
- GUI built with Tkinter
- CLI interface using curses

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Ensure all dependencies are installed
3. Verify Python version (3.8+ required)
4. Check firewall settings

---

**Happy Secure Chatting!** 🔒