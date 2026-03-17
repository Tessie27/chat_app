import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing Secure Chat imports...")
    print("-" * 40)
    
    modules = [
        ("core.protocol", ["SecureProtocol", "send", "recv", "ts"]),
        ("core.client_base", ["ChatClientBase"]),
        ("utils.crypto", ["CryptoUtils", "MessageEncryptor"]),
        ("utils.portable", ["is_portable", "get_config_dir"]),
        ("config.settings", ["Settings", "ServerConfig", "UserProfile"]),
    ]
    
    success = True
    
    for module_name, attrs in modules:
        try:
            module = __import__(module_name, fromlist=attrs)
            print(f"✓ {module_name} - imported")
            
            for attr in attrs:
                if hasattr(module, attr):
                    print(f"  ✓ {attr}")
                else:
                    print(f"  ✗ {attr} missing")
                    success = False
        except ImportError as e:
            print(f"✗ {module_name} - {e}")
            success = False
    
    print("-" * 40)
    return success

if __name__ == "__main__":
    sys.exit(0 if test_imports() else 1)