import time
import os
import threading
import blocker

class FileWatcher:
    def __init__(self, check_interval=2.0):
        self.check_interval = check_interval
        self.is_running = False
        self.target_file = blocker.get_hosts_path()
        self.last_known_size = 0
        self._thread = None

    def start(self):
        if self.is_running: return
        self.is_running = True
        if os.path.exists(self.target_file):
            self.last_known_size = os.path.getsize(self.target_file)
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        print(f"Monitoring {self.target_file}")

    def stop(self):
        self.is_running = False
        if self._thread: self._thread.join(timeout=1.0)

    def _watch_loop(self):
        while self.is_running:
            time.sleep(self.check_interval)
            try:
                if not os.path.exists(self.target_file):
                    print("WARNING: Hosts file missing!")
                    continue
                current_size = os.path.getsize(self.target_file)
                if current_size < (self.last_known_size - 1024):
                    print("WARNING: Hosts file tampered with (shrunk)!")
                self.last_known_size = current_size
            except: pass