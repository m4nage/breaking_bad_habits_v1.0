#!/bin/bash
# Get the REAL directory where the script is located (following symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
cd "$DIR"

# Ensure log directory exists
LOG_DIR="$HOME/.local/share/breakingbadhabits"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app.log"

# Clear log on fresh start if not backgrounded
if [[ "$*" != *"--background"* ]]; then
    echo "--- New Session: $(date) ---" > "$LOG_FILE"
fi

# 1. Start the service first
if ! pgrep -f "src/main.py" > /dev/null; then
    echo "Starting background service..."
    # Start as normal user
    "$DIR/venv/bin/python" "$DIR/src/main.py" >> "$LOG_FILE" 2>&1 &
    
    # 2. Wait explicitly for the service port to open
    echo "Waiting for service to initialize..."
    MAX_RETRIES=45
    COUNT=0
    while ! "$DIR/venv/bin/python" -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', 65432))" 2>/dev/null; do
        sleep 1
        COUNT=$((COUNT + 1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            if command -v kdialog >/dev/null; then
                kdialog --error "Service failed to start. Check $LOG_FILE for details."
            else
                echo "Service failed to start. Check $LOG_FILE for details."
            fi
            exit 1
        fi
    done
fi

# 3. Start the dashboard (with logging)
"$DIR/venv/bin/python" "$DIR/src/gui_client.py" "$@" >> "$LOG_FILE" 2>&1 &
