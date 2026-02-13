#!/bin/bash
# Try to signal the service to show the window
./venv/bin/python src/show.py 2>/dev/null

# Check if the GUI client process is actually running
if ! pgrep -f "src/gui_client.py" > /dev/null; then
    echo "Starting Dashboard Client..."
    ./venv/bin/python src/gui_client.py "$@" &
else
    echo "Dashboard is already running and has been signaled to show."
fi
