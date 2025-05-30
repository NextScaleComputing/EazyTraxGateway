import os
import socket
import subprocess
import logging

def get_current_hostname():
    """
    Get the current hostname of the device
    """
    return socket.gethostname()

def validate_hostname(hostname):
    """
    Validate that the hostname follows the naming rules:
    - Only alphanumeric characters and hyphens
    - Cannot start or end with a hyphen
    - Cannot be longer than 63 characters
    - Cannot be empty
    """
    if not hostname or len(hostname) > 63:
        return False
    
    if hostname[0] == '-' or hostname[-1] == '-':
        return False
    
    # Check that hostname only contains allowed characters
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    return all(c in allowed_chars for c in hostname)

def change_hostname(new_hostname):
    """
    Change the system hostname with immediate effect and make it persistent across reboots
    Returns a tuple of (success, message)
    """
    if not validate_hostname(new_hostname):
        return False, "Invalid hostname. Must be alphanumeric with hyphens (not at start/end) and max 63 chars."

    current_hostname = get_current_hostname()
    
    # Don't do anything if the hostname is already set to the requested value
    if current_hostname == new_hostname:
        return True, f"Hostname is already set to {new_hostname}"
    
    result = {"success": True, "message": "", "requires_reboot": False}
    system_type = os.name
    
    try:
        # For Linux systems (Raspberry Pi)
        if system_type == "posix":
            # Change the hostname immediately using hostname command
            subprocess.run(['sudo', 'hostnamectl', 'set-hostname', new_hostname], check=True)
            
            # Update /etc/hostname
            try:
                with open('/etc/hostname', 'w') as f:
                    f.write(f"{new_hostname}\n")
            except Exception as e:
                logging.warning(f"Failed to update /etc/hostname: {str(e)}. Using alternate method.")
                subprocess.run(['sudo', 'sh', '-c', f'echo "{new_hostname}" > /etc/hostname'], check=True)
            
            # Update /etc/hosts file
            hosts_updated = update_hosts_file(current_hostname, new_hostname)
            if not hosts_updated:
                result["message"] = f"Hostname changed to {new_hostname}, but failed to update /etc/hosts. Some applications may not work correctly."
                result["requires_reboot"] = True
                result["success"] = False
            else:
                result["message"] = f"Hostname successfully changed from {current_hostname} to {new_hostname}"
        
        # For other operating systems - only Windows and Mac support here
        elif system_type == "nt":  # Windows
            result["success"] = False
            result["message"] = "Changing hostname on Windows is not supported by this application."
        else:  # MacOS or other
            result["success"] = False
            result["message"] = f"Changing hostname not supported on this operating system ({system_type})."
            
    except Exception as e:
        logging.error(f"Error changing hostname: {str(e)}")
        return False, f"Error changing hostname: {str(e)}"
    
    return result["success"], result["message"]

def update_hosts_file(old_hostname, new_hostname):
    """
    Update the /etc/hosts file to replace the old hostname with the new one
    """
    try:
        # Read the current hosts file
        hosts_content = []
        try:
            with open('/etc/hosts', 'r') as f:
                hosts_content = f.readlines()
        except Exception as e:
            logging.error(f"Failed to read /etc/hosts: {str(e)}")
            return False
        
        # Update the hostname in the file
        new_hosts_content = []
        for line in hosts_content:
            if old_hostname in line:
                new_hosts_content.append(line.replace(old_hostname, new_hostname))
            else:
                new_hosts_content.append(line)
        
        # Write the updated content back with sudo
        try:
            with open('/tmp/new_hosts', 'w') as f:
                f.writelines(new_hosts_content)
            
            # Use sudo to copy the file to /etc/hosts
            subprocess.run(['sudo', 'cp', '/tmp/new_hosts', '/etc/hosts'], check=True)
            subprocess.run(['sudo', 'rm', '/tmp/new_hosts'], check=True)
            
        except Exception as e:
            logging.error(f"Failed to update /etc/hosts: {str(e)}")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Error in update_hosts_file: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the module when run directly
    print(f"Current hostname: {get_current_hostname()}")