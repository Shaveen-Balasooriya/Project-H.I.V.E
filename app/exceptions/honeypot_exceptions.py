# app/exceptions/honeypot_exceptions.py
class HoneypotError(Exception):
    """Base exception for honeypot errors"""
    pass

class HoneypotExistsError(HoneypotError):
    """Raised when attempting to create a honeypot that already exists"""
    pass

class HoneypotImageError(HoneypotError):
    """Raised when there's an error with the honeypot image"""
    pass

class HoneypotContainerError(HoneypotError):
    """Raised when there's an error with the honeypot container"""
    pass