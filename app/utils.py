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
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

