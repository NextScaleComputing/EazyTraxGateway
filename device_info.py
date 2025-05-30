import os
import platform
import subprocess

def get_device_info():
    """Retrieve system hardware, model, and revision information across different OS types."""
    info = {
        "Hardware": "Unknown",
        "Revision": "Unknown",
        "Model": "Unknown",
        "OS": platform.system(),
        "OS_Version": platform.version(),
    }

    system = platform.system().lower()

    if system == "linux":
        # Detect Raspberry Pi or Radxa
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if ":" in line:
                        key, value = line.strip().split(":", 1)
                        info[key.strip()] = value.strip()

        # Prioritize /proc/device-tree/model for Raspberry Pi & Radxa detection
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model", "r") as f:
                model = f.read().strip()
                info["Model"] = model

                if "Raspberry Pi" in model:
                    info["Hardware"] = "Raspberry Pi"
                elif "Radxa" in model:
                    info["Hardware"] = "Radxa"

        # Identify Radxa using /proc/device-tree/compatible
        if os.path.exists("/proc/device-tree/compatible"):
            with open("/proc/device-tree/compatible", "r") as f:
                compatible_info = f.read().strip().lower()
                if "radxa" in compatible_info:
                    info["Hardware"] = "Radxa"

        # Extract OS details from /etc/os-release
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.strip().split("=")[1].replace('"', '')
                        info["OS_Version"] = os_name

        # Ensure revision is properly extracted
        info["Revision"] = info.get("Revision", "Unknown")

    elif system == "windows":
        info["Hardware"] = "Windows"

    elif system == "darwin":
        # macOS system info
        try:
            info["Model"] = subprocess.check_output("sysctl -n hw.model", shell=True).decode().strip()
            info["Hardware"] = "Apple"
        except Exception:
            info["Model"] = "Mac"
            info["Hardware"] = "Apple"

    return info

if __name__ == "__main__":
    device_info = get_device_info()
    print(device_info)
