import os
import platform
import socket

def is_anbernic_device() -> bool:
    # 1. Quick initial filter: must be running Linux
    if platform.system() != "Linux":
        return False

    # 2. Check the system hostname (Matches your 'root@ANBERNIC' terminal signature)
    try:
        hostname = socket.gethostname().upper()
        if "ANBERNIC" in hostname:
            return True
    except Exception:
        pass

    # 3. Fallback/Double-Verification: Check the specific Allwinner H700 hardware IDs
    # This covers cases where the hostname might be customized by a user later
    dt_paths = ["/proc/device-tree/model", "/proc/device-tree/compatible"]
    for path in dt_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read().lower()
                    if "sun50iw9" in content or "h616arm" in content:
                        return True
            except Exception:
                pass

    return False

if __name__ == "__main__":
    if is_anbernic_device():
        print("🎮 Hardware verified: Code is running on your Anbernic device.")
    else:
        print("💻 Standard system detected.")
