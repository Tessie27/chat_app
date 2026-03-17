#!/usr/bin/env python3
"""
Secure Chat - Portable Application
Usage:
    python chat.py gui     # Launch GUI
    python chat.py cli      # Launch CLI
    python chat.py server   # Start server
    python chat.py --help   # Show help
"""

import os
import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Check and install missing dependencies"""
    try:
        import cryptography
    except ImportError:
        print("Installing cryptography library...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        print("Done!")


def launch_gui():
    """Launch GUI client"""
    try:
        # Use absolute import
        from clients.gui_client import ChatClient

        app = ChatClient()
        app.mainloop()
    except ImportError as e:
        print(f"Import Error in GUI: {e}")
        print("Make sure you're running from the secure-chat root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


def launch_cli():
    """Launch CLI client"""
    try:
        # Check if curses is available on Windows
        if sys.platform == "win32":
            try:
                import curses
            except ImportError:
                print("Curses module not found. Installing windows-curses...")
                import subprocess

                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "windows-curses"]
                )
                import curses

        # Use absolute import
        from clients.cli_client import main as cli_main
        import curses

        curses.wrapper(cli_main)
    except ImportError as e:
        print(f"Import Error in CLI: {e}")
        print("Make sure you're running from the secure-chat root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching CLI: {e}")
        sys.exit(1)


def launch_server():
    """Launch server"""
    try:
        # Use absolute import
        from core.server import Server

        # Parse server-specific arguments
        port = 5555
        password = None

        # Simple argument parsing for server
        if len(sys.argv) > 2:
            for i in range(2, len(sys.argv)):
                if sys.argv[i] == "--port" and i + 1 < len(sys.argv):
                    port = int(sys.argv[i + 1])
                elif sys.argv[i] == "--password" and i + 1 < len(sys.argv):
                    password = sys.argv[i + 1]

        print(f"Secure Chat Server starting on port {port}")
        if password:
            print("Password protection enabled")

        server = Server(port, password)
        server.start()
    except ImportError as e:
        print(f"Import Error in Server: {e}")
        print("Make sure you're running from the secure-chat root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching server: {e}")
        sys.exit(1)


def main():
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python chat.py [gui|cli|server] [options]")
        print("  python chat.py gui")
        print("  python chat.py cli")
        print("  python chat.py server [--port PORT] [--password PASSWORD]")
        sys.exit(1)

    mode = sys.argv[1]

    # Check for portable mode
    portable = "--portable" in sys.argv

    # Set portable mode if requested
    if portable:
        os.environ["CHAT_PORTABLE"] = "1"
        config_dir = Path("./chat_data")
        config_dir.mkdir(exist_ok=True)
        os.environ["CHAT_CONFIG"] = str(config_dir)

    # Check dependencies
    check_dependencies()

    # Launch appropriate mode
    if mode == "gui":
        launch_gui()
    elif mode == "cli":
        launch_cli()
    elif mode == "server":
        launch_server()
    else:
        print(f"Unknown mode: {mode}")
        print("Use: gui, cli, or server")
        sys.exit(1)


if __name__ == "__main__":
    main()
