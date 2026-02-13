import os

BLOCKLIST_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn/hosts"

def get_hosts_path():
    return "/etc/hosts"

def is_admin():
    """Check if the script has administrative/root privileges."""
    try:
        return os.getuid() == 0
    except AttributeError:
        return False

def get_apply_cmd(tmp_path):
    hosts_path = get_hosts_path()
    return f"mv {tmp_path} {hosts_path} && chmod 644 {hosts_path} && resolvectl flush-caches"

def get_remove_cmd():
    hosts_path = get_hosts_path()
    backup = hosts_path + ".bak_breakingbadhabits"
    return f"cp {backup} {hosts_path} && resolvectl flush-caches"

if __name__ == "__main__":
    # Test check
    print(f"Hosts Path: {get_hosts_path()}")
    print(f"Is Admin: {is_admin()}")
