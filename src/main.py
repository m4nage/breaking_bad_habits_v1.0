import sys
import threading
import time
import socket
import os
import subprocess
import tempfile
import stat
import json
import requests
import blocker
import browser_policy
import file_watcher
import tracker
import storage

# Global state
protection_active = False
activity_tracker = None
hosts_watcher = None
workout_pending = False
show_requested = False

# CONFIGURATION
# Default fallback if not in storage
DEFAULT_UNLOCK_DELAY_SECONDS = 60 

def on_workout_triggered():
    global workout_pending
    print("WORKOUT TRIGGERED!")
    workout_pending = True

def run_privileged_script(script_content):
    """Runs a bundled script via pkexec and waits for the result."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.sh') as tmp:
        tmp.write("#!/bin/bash\n" + script_content)
        tmp_path = tmp.name
    os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    # Get environment for GUI elevation
    env = os.environ.copy()
    if 'DISPLAY' not in env: env['DISPLAY'] = ':0'
    
    try:
        print(f"DEBUG: Running privileged script via pkexec...")
        # Use env -u to ensure we don't pass dangerous vars, but keep DISPLAY
        result = subprocess.run(["pkexec", "env", f"DISPLAY={env['DISPLAY']}", "bash", tmp_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"DEBUG: pkexec failed (code {result.returncode})")
            print(f"DEBUG: Stderr: {result.stderr}")
        return result.returncode == 0
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

def on_toggle_protection_cmd(delay_minutes=None):
    global protection_active
    data = storage.load_data()
    
    # Update settings if delay is provided
    if delay_minutes is not None:
        if "settings" not in data: data["settings"] = {}
        data["settings"]["unlock_delay_seconds"] = int(delay_minutes) * 60
        storage.save_data(data)
        print(f"Updated unlock delay to {data['settings']['unlock_delay_seconds']} seconds")
    
    unlock_delay = data.get("settings", {}).get("unlock_delay_seconds", DEFAULT_UNLOCK_DELAY_SECONDS)
    target_state = not protection_active
    
    if target_state:
        storage.clear_unlock_request()
        try:
            # 1. Get current hosts content
            hosts_path = blocker.get_hosts_path()
            with open(hosts_path, 'r') as f:
                original_lines = f.readlines()
            
            # 2. Download blocklist
            print("Downloading blocklist...")
            resp = requests.get(blocker.BLOCKLIST_URL, timeout=20)
            resp.raise_for_status()
            
            # 3. Process blocklist (Filter out localhost/standard entries to avoid conflicts)
            print("Processing blocklist...")
            blocked_lines = []
            for line in resp.text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'): continue
                # Skip common entries that should stay as they are in the original file
                if "localhost" in line or "127.0.0.1" in line or "::1" in line: continue
                blocked_lines.append(line + "\n")

            # 4. Create new hosts content (Original + Marker + Blocked)
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as h_tmp:
                # Keep original lines, but remove our old block if it exists (self-healing)
                in_our_block = False
                for line in original_lines:
                    if "# BEGIN BREAKING BAD HABITS" in line: in_our_block = True
                    if not in_our_block: h_tmp.write(line)
                    if "# END BREAKING BAD HABITS" in line: in_our_block = False
                
                # Append new block
                h_tmp.write("\n# BEGIN BREAKING BAD HABITS\n")
                h_tmp.write("# This section is managed by Breaking Bad Habits. Do not edit manually.\n")
                h_tmp.writelines(blocked_lines)
                h_tmp.write("# END BREAKING BAD HABITS\n")
                h_tmp_path = h_tmp.name
            
            # 5. Create Browser Policy
            policy_data = {"policies": {"Proxy": {"Mode": "system", "Locked": True}, "DNSOverHTTPS": {"Enabled": False, "Locked": True}, "ExtensionSettings": {}}}
            for ext_id in browser_policy.BLOCKED_EXTENSIONS:
                policy_data["policies"]["ExtensionSettings"][ext_id] = {"installation_mode": "blocked", "blocked_install_message": "Blocked."}
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as p_tmp:
                json.dump(policy_data, p_tmp, indent=4)
                p_tmp_path = p_tmp.name

            # 6. Build the privileged script
            script = f"cp -n {hosts_path} {hosts_path}.bak_breakingbadhabits\n" # Safe backup
            script += f"cp {h_tmp_path} {hosts_path}\nchmod 644 {hosts_path}\nrm -f {h_tmp_path}\n"
            for path in browser_policy.POLICY_PATHS:
                script += f"mkdir -p {os.path.dirname(path)} && cp {p_tmp_path} {path} && chmod 644 {path}\n"
            script += f"rm -f {p_tmp_path}\n"
            script += "resolvectl flush-caches || true\n"
            
            if run_privileged_script(script):
                protection_active = True
                storage.set_protection_status(True)
                if hosts_watcher: hosts_watcher.start()
                return "OK_ACTIVATED"
            return "ERROR_CANCELLED"
        except Exception as e: 
            print(f"Activation failed: {e}")
            return f"ERROR_{str(e)}"
    else:
        req_time = storage.get_unlock_request()
        if req_time is None:
            storage.set_unlock_request(time.time())
            return "LOCKED_TIMER_STARTED"
        if (time.time() - req_time) < unlock_delay:
            return f"LOCKED_WAIT_{int(unlock_delay - (time.time() - req_time))}s"
            
        # DEACTIVATION: Remove our block from hosts
        try:
            hosts_path = blocker.get_hosts_path()
            with open(hosts_path, 'r') as f:
                lines = f.readlines()
            
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as h_tmp:
                in_our_block = False
                for line in lines:
                    if "# BEGIN BREAKING BAD HABITS" in line:
                        in_our_block = True
                        continue
                    if "# END BREAKING BAD HABITS" in line:
                        in_our_block = False
                        continue
                    if not in_our_block:
                        h_tmp.write(line)
                h_tmp_path = h_tmp.name

            script = f"cp {h_tmp_path} {hosts_path}\nchmod 644 {hosts_path}\nrm -f {h_tmp_path}\n"
            for path in browser_policy.POLICY_PATHS: script += f"rm -f {path}\n"
            script += "resolvectl flush-caches || true\n"
            
            if run_privileged_script(script):
                if hosts_watcher: hosts_watcher.stop()
                protection_active = False
                storage.set_protection_status(False)
                storage.clear_unlock_request()
                return "OK_DEACTIVATED"
            return "ERROR_CANCELLED"
        except Exception as e:
            return f"ERROR_{str(e)}"

def on_quit_cmd():
    if activity_tracker: activity_tracker.stop()
    if hosts_watcher: hosts_watcher.stop()
    os._exit(0)

def start_command_listener():
    def listener_loop():
        global workout_pending, show_requested
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 65432))
        server_socket.listen(5)
        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    data = conn.recv(1024).strip()
                    if not data: continue
                    cmd_str = data.decode('utf-8')
                    print(f"DEBUG: Received command: {cmd_str}")
                    parts = cmd_str.split()
                    cmd = parts[0]
                    
                    if cmd == "TOGGLE": 
                        delay = parts[1] if len(parts) > 1 else None
                        res = on_toggle_protection_cmd(delay)
                        print(f"DEBUG: TOGGLE response: {res}")
                        conn.sendall(res.encode('utf-8'))
                    elif cmd == "CANCEL_UNLOCK":
                        storage.clear_unlock_request()
                        conn.sendall(b"OK_CANCELLED")
                    elif cmd == "QUIT":
                        conn.sendall(b"OK")
                        on_quit_cmd()
                    elif cmd == "STATUS":
                        status = "ACTIVE" if protection_active else "INACTIVE"
                        if workout_pending: status += ":WORKOUT"
                        if activity_tracker: status += f":W{activity_tracker.get_status()['seconds_to_trigger']}"
                        
                        # Logic to show wait timer
                        data = storage.load_data()
                        unlock_delay = data.get("settings", {}).get("unlock_delay_seconds", DEFAULT_UNLOCK_DELAY_SECONDS)
                        req_time = storage.get_unlock_request()
                        
                        if protection_active and req_time:
                            elapsed = time.time() - req_time
                            remaining = int(unlock_delay - elapsed)
                            if remaining > 0:
                                status += f":U{remaining}"
                            else:
                                status += ":U0" # Timer finished
                            
                        if show_requested:
                            status += ":SHOW"
                            show_requested = False
                            
                        conn.sendall(status.encode('utf-8'))
                    elif cmd == "WORKOUT_DONE":
                        workout_pending = False
                        conn.sendall(b"OK")
                    elif cmd == "SHOW":
                        show_requested = True
                        conn.sendall(b"OK")
            except Exception as e:
                print(f"DEBUG: Listener error: {e}")
    threading.Thread(target=listener_loop, daemon=True).start()

def main():
    global activity_tracker, protection_active, hosts_watcher
    print("Main: Starting...")
    
    # Self-Healing: Check actual system state
    try:
        hp = blocker.get_hosts_path()
        print(f"Main: Checking hosts at {hp}")
        if os.path.exists(hp):
            with open(hp, 'r') as f:
                content = f.read()
                # If we find our blocklist marker or massive blocked entries
                if "0.0.0.0" in content and len(content.splitlines()) > 1000:
                    print("Self-Heal: Detected active protection in hosts file. Syncing state.")
                    storage.set_protection_status(True)
    except Exception as e:
        print(f"Self-Heal Check Failed: {e}")

    print("Main: Loading data")
    data = storage.load_data()
    protection_active = data.get("protection_active", False)
    
    # Ensure local variable matches self-heal if it triggered
    if protection_active: 
        print("Main: Protection confirmed active.")
        hosts_watcher = file_watcher.FileWatcher()
        hosts_watcher.start()
    else:
        hosts_watcher = None
    
    print("Main: Starting activity tracker")
    activity_tracker = tracker.ActivityTracker(trigger_limit_seconds=3600, idle_threshold=60, initial_active_time=storage.get_active_seconds())
    activity_tracker.start(on_workout_triggered, periodic_save_callback=storage.set_active_seconds)
    
    print("Main: Starting command listener")
    start_command_listener()
    print("Main: Entering wait loop")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: on_quit_cmd()

if __name__ == "__main__":
    main()
