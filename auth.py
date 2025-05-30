import hmac
import hashlib
import base64
import time
import os
from functools import wraps
from flask import request, jsonify
import logging

# We'll use the device's MAC address as the SECRET_KEY
# This will be set by app.py when it initializes
_MAC_ADDRESS = None

def set_mac_address(mac_address):
    """Set the MAC address to be used as SECRET_KEY"""
    global _MAC_ADDRESS
    if mac_address:
        # Clean the MAC address (remove colons, convert to uppercase)
        _MAC_ADDRESS = mac_address.replace(':', '').upper()
        logging.info(f"auth:: MAC address set for token generation: {_MAC_ADDRESS}")
    else:
        logging.warning("auth:: Attempted to set empty MAC address for token generation")

def get_mac_address():
    """Get the current MAC address being used"""
    return _MAC_ADDRESS

def get_secret_key():
    """Get the secret key based on MAC address or fallback to environment variable"""
    # If MAC address is set, use it as the primary secret key
    if _MAC_ADDRESS:
        # Create a more complex key by combining MAC address with a salt
        mac_based_key = f"{_MAC_ADDRESS}_eazytrax_secure_salt_{_MAC_ADDRESS[::-1]}"
        return mac_based_key
    
    # Fallback to environment variable or default value
    return os.getenv("AUTH_SECRET_KEY", "eazytrax_gateway_default_secret")

# Token expiration time in seconds (default: 24 hours)
TOKEN_EXPIRY = int(os.getenv("AUTH_TOKEN_EXPIRY", 86400))

def generate_token(mac_address):
    """
    Generate a bearer token based on the MAC address
    Format: base64(mac_address:timestamp:signature)
    Where signature is HMAC-SHA256(mac_address:timestamp, SECRET_KEY)
    """
    if not mac_address:
        return None
    
    # Clean the MAC address (remove colons, convert to uppercase)
    mac = mac_address.replace(':', '').upper()
    
    # Create timestamp for expiration
    timestamp = str(int(time.time()) + TOKEN_EXPIRY)
    
    # Create message to sign (mac:timestamp)
    message = f"{mac}:{timestamp}"
    
    # Get the secret key (will use MAC address if set)
    secret_key = get_secret_key()
    
    # Create signature using HMAC-SHA256
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Combine the elements and encode as base64
    token_data = f"{message}:{signature}"
    token = base64.b64encode(token_data.encode()).decode()
    
    return token

def validate_token(token):
    """
    Validate the token format, signature, and expiration time
    Returns (valid, mac_address, message)
    """
    try:
        # Decode from base64
        decoded = base64.b64decode(token).decode()
        
        # Split into parts
        parts = decoded.split(':')
        
        if len(parts) != 3:
            return False, None, "Invalid token format"
        
        mac, timestamp, provided_signature = parts
        
        # Check if token has expired
        current_time = int(time.time())
        if current_time > int(timestamp):
            return False, None, "Token expired"
        
        # Get the secret key (will use MAC address if set)
        secret_key = get_secret_key()
        
        # Regenerate the signature to verify
        message = f"{mac}:{timestamp}"
        expected_signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Validate signature
        if not hmac.compare_digest(expected_signature, provided_signature):
            return False, None, "Invalid signature"
        
        return True, mac, "Valid token"
    
    except Exception as e:
        logging.error(f"Token validation error: {str(e)}")
        return False, None, f"Token validation error: {str(e)}"

def token_required(f):
    """
    Decorator for routes that need token authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing'
            }), 401
        
        # Validate the token
        valid, mac, message = validate_token(token)
        if not valid:
            return jsonify({
                'success': False,
                'message': message
            }), 401
        
        # Add the MAC address to the request for use in the route
        request.mac_address = mac
        return f(*args, **kwargs)
    
    return decorated_function

# Function to get current token (used for getting a valid token)
def get_current_token(mac_address):
    return generate_token(mac_address)