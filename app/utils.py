"""Utility functions for the Super Admin Service."""
import secrets
import string


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Length of the password (default: 16)
        
    Returns:
        A secure random password containing letters, digits, and symbols
        Note: Password is limited to 72 bytes for bcrypt compatibility
    """
    # Bcrypt has a 72-byte limit, so we'll generate a password that's safely under that
    # Using ASCII characters, each is 1 byte, so max 72 characters
    # We'll use 16 characters by default, which is well under the limit
    max_length = min(length, 72)  # Ensure we don't exceed bcrypt's 72-byte limit
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(max_length))
    return password

