import time
import threading
from pynput import mouse, keyboard

class ActivityTracker:
    def __init__(self, trigger_limit_seconds=3600, idle_threshold=60, initial_active_time=0):
        """
        Tracks active PC usage.
        :param trigger_limit_seconds: Cumulative active time before triggering callback (default 1 hour).
        :param idle_threshold: Seconds of inactivity before stopping the timer.
        """
        self.trigger_limit = trigger_limit_seconds
        self.idle_threshold = idle_threshold
        self.cumulative_active_time = initial_active_time
        self.last_activity_time = time.time()
        self.is_running = False
        self.callback = None
        
        self.mouse_listener = None
        self.key_listener = None
        self.tracking_thread = None

    def _on_activity(self, *args, **kwargs):
        """Updates the last activity timestamp."""
        self.last_activity_time = time.time()

    def start(self, callback, periodic_save_callback=None):
        """Starts the listeners and the tracking thread."""
        if self.is_running:
            return
            
        self.callback = callback
        self.periodic_save_callback = periodic_save_callback
        self.is_running = True
        
        # Start input listeners
        self.mouse_listener = mouse.Listener(
            on_move=self._on_activity,
            on_click=self._on_activity,
            on_scroll=self._on_activity)
        
        self.key_listener = keyboard.Listener(
            on_press=self._on_activity)
        
        self.mouse_listener.start()
        self.key_listener.start()
        
        # Start the monitoring loop in a background thread
        self.tracking_thread = threading.Thread(target=self._track_loop, daemon=True)
        self.tracking_thread.start()
        print(f"Activity tracker started. Threshold: {self.idle_threshold}s, Trigger: {self.trigger_limit}s")

    def _track_loop(self):
        """Internal loop to accumulate active time."""
        last_check_time = time.time()
        last_save_time = time.time()
        
        while self.is_running:
            time.sleep(1)
            now = time.time()
            
            # Check if user was active recently
            if now - self.last_activity_time < self.idle_threshold:
                elapsed = now - last_check_time
                self.cumulative_active_time += elapsed
            
            # Periodic save (every 30 seconds)
            if now - last_save_time > 30:
                if self.periodic_save_callback:
                    self.periodic_save_callback(self.cumulative_active_time)
                last_save_time = now

            # Check if limit reached
            if self.cumulative_active_time >= self.trigger_limit:
                print("Trigger limit reached! Executing callback.")
                if self.callback:
                    threading.Thread(target=self.callback, daemon=True).start()
                
                # Reset cumulative time
                self.cumulative_active_time = 0
                if self.periodic_save_callback:
                    self.periodic_save_callback(0)
            
            last_check_time = now

    def stop(self):
        """Stops all tracking and listeners."""
        self.is_running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.key_listener:
            self.key_listener.stop()
        print("Activity tracker stopped.")

    def get_status(self):
        """Returns the current state of tracking."""
        return {
            "active_seconds": int(self.cumulative_active_time),
            "is_idle": (time.time() - self.last_activity_time) >= self.idle_threshold,
            "seconds_to_trigger": int(self.trigger_limit - self.cumulative_active_time)
        }

if __name__ == "__main__":
    # Test script
    def test_callback():
        print("\n*** WORKOUT TRIGGERED! GO DO 10 PUSHUPS! ***\n")

    tracker = ActivityTracker(trigger_limit_seconds=10, idle_threshold=5)
    tracker.start(test_callback)
    
    try:
        while True:
            status = tracker.get_status()
            print(f"Status: {status['active_seconds']}s active, "
                  f"Idle: {status['is_idle']}, "
                  f"Next trigger in: {status['seconds_to_trigger']}s", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        tracker.stop()
