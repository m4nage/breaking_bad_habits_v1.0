import os

# Target policy paths for Firefox
# We target multiple locations to ensure coverage across Snap, Flatpak, and Apt versions
POLICY_PATHS = [
    "/etc/firefox/policies/policies.json",
    "/usr/lib/firefox/distribution/policies.json",
    "/usr/share/firefox/distribution/policies.json"
]

# IDs of common VPN extensions to block
BLOCKED_EXTENSIONS = [
    "nordvpnproxy@nordvpn.com",      # NordVPN
    "zenmate@zenmate.com",           # ZenMate
    "jid1-4P0kohSJxU1qGg@jetpack",   # Hola VPN
    "expressvpn-browser-extension@expressvpn.com", # ExpressVPN
    "touch-vpn@anchorfree.com",      # Touch VPN
    "{4483e589-985f-4098-9b88-5c425712f534}", # Bitdefender VPN
    "uVPN@uvpn.me"                   # uVPN
]

def get_apply_cmds(tmp_path):
    cmds = []
    for path in POLICY_PATHS:
        directory = os.path.dirname(path)
        cmds.append(f"mkdir -p {directory} && cp {tmp_path} {path} && chmod 644 {path}")
    return " && ".join(cmds)

def get_remove_cmds():
    cmds = []
    for path in POLICY_PATHS:
        cmds.append(f"rm -f {path}")
    return " && ".join(cmds)
