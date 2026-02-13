import json
import os
import time
import fcntl
import getpass

# Use a generic path in the user's home directory
DATA_DIR = os.path.expanduser("~/.local/share/breakingbadhabits")
DATA_FILE = os.path.join(DATA_DIR, "data.json")

def ensure_data_dir():
    """Ensures the data directory exists and has correct permissions."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, mode=0o755, exist_ok=True)

DEFAULT_DATA = {
    "streak_start": time.time(),
    "protection_active": False,
    "unlock_request_time": None,
    "active_seconds": 0,
    "settings": {
        "workout_interval": 3600,
        "unlock_delay_seconds": 3600,
        "theme": "dark"
    }
}

def get_active_seconds():
    data = load_data()
    return data.get("active_seconds", 0)

def set_active_seconds(seconds):
    # Optimistic locking retry loop could be better, but blocking lock is safer
    data = load_data()
    data["active_seconds"] = int(seconds)
    save_data(data)

def load_data():
    """Loads application data from JSON file with shared lock."""
    ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    
    try:
        with open(DATA_FILE, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
                # Merge with defaults
                for key, value in DEFAULT_DATA.items():
                    if key not in data:
                        data[key] = value
                return data
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except (json.JSONDecodeError, IOError, ValueError):
        return DEFAULT_DATA

def save_data(data):
    """Saves application data to JSON file with exclusive lock."""
    try:
        # Check write permission explicitly for better error reporting
        if os.path.exists(DATA_FILE) and not os.access(DATA_FILE, os.W_OK):
            print(f"CRITICAL: No write permission for {DATA_FILE}. Current user: {getpass.getuser()}")
        
        with open(DATA_FILE, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=4)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except IOError as e:
        print(f"Error saving data to {DATA_FILE}: {e}")

def get_streak_duration(start_time):
    """Calculates streak duration in days, hours, minutes."""
    diff = time.time() - start_time
    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    minutes = int((diff % 3600) // 60)
    return days, hours, minutes

def reset_streak():
    """Resets the streak start time to now."""
    data = load_data()
    data["streak_start"] = time.time()
    save_data(data)
    return data["streak_start"]

def set_protection_status(is_active):
    """Updates the protection status in storage."""
    data = load_data()
    data["protection_active"] = is_active
    save_data(data)

def set_unlock_request(timestamp):
    """Sets the timestamp for when the user requested to unlock."""
    data = load_data()
    data["unlock_request_time"] = timestamp
    save_data(data)

def get_unlock_request():
    """Returns the timestamp of the unlock request, or None."""
    data = load_data()
    return data.get("unlock_request_time")

def clear_unlock_request():
    """Clears the unlock request timestamp."""
    data = load_data()
    data["unlock_request_time"] = None
    save_data(data)
