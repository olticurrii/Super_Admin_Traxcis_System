"""Security utilities for password hashing and verification."""
import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt directly.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Note:
        Bcrypt has a 72-byte limit. Passwords are automatically truncated if needed.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    
    # Bcrypt has a 72-byte limit. Truncate if longer.
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to exactly 72 bytes
        password_bytes = password_bytes[:72]
    
    # Hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False
    
    # Truncate password if needed before verification
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Convert hashed_password to bytes if it's a string
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hashed_password)


