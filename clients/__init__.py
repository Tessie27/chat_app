"""
Client implementations (GUI and CLI)
"""
from .gui_client import ChatClient as GUIClient
from .cli_client import CLIClient

__all__ = ['GUIClient', 'CLIClient']