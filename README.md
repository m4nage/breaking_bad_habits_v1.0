# Breaking Bad Habits

A robust Linux tool to aid in behavioral change. It combines system-level blocking with activity monitoring and workout reminders.

## 🚀 Key Features

- **VPN-Resistant Blocking:** Enforces domain blocking at the OS level via the `/etc/hosts` file.
- **Auto-Start on Boot:** Automatically ensures the app starts when you log in if protection is ACTIVE.
- **Activity Tracking:** Monitors mouse/keyboard usage to detect active screen time.
- **Workout Reminders:** Prompts you to exercise after 1 hour of active usage.
- **Panic Button:** Instant motivation available in the Dashboard and System Tray.
- **System Tray:** Quick access to features (Panic, Show, Quit) from the top bar.
- **Dashboard:** Track your streak and manage protection settings.

## 🛠 Installation

### Option 1: Debian/Ubuntu (Recommended)
This will install the app system-wide and add it to your application menu.
```bash
sudo apt install ./breakingbadhabits_1.0.deb
```

### Option 2: Portable/Developer Mode
Run it directly from the folder without installing.
```bash
# Install dependencies first
pip install -r requirements.txt
# Run the launcher
./launch.sh
```

## 💻 Usage Guide

### 1. Start the Application
- **Installed via .deb:** Search for **"Breaking Bad Habits"** in your applications menu or type `breakingbadhabits` in the terminal.
- **Portable:** Run `./launch.sh`.

### 2. System Tray & Hiding
- Clicking the **"X"** on the dashboard hides it to the **System Tray**.
- Right-click the Tray Icon (Blue Circle) to open the Panic Window or restore the Dashboard.

### 3. Deactivating Protection (Security Timer)
To prevent impulsive decisions, the app uses a **user-defined cool-down timer**:
1.  **Setting the Timer:** When you toggle protection **ON**, you will be asked to set a delay (e.g., 60 minutes).
2.  **Starting Deactivation:** To turn protection **OFF**, toggle the switch. This starts the countdown for the delay you chose earlier.
3.  **Waiting:** You must wait for the timer to reach zero. The dashboard will show the remaining time.
4.  **Confirming:** Once the timer is finished, toggle the switch to **OFF** again. You will then be prompted for your password to restore system files.

### 4. Stop the Application
To fully exit:
- Right-click the Tray Icon and select **"Quit BreakingBadHabits"**.
- This stops both the UI and the background service.
- **Note:** Quit is disabled if protection is currently ACTIVE. You must deactivate first.

**Kill from Terminal (Force Stop):**
If the app is frozen or you prefer the command line:
```bash
pkill -f breakingbadhabits
```

## ⚠️ System Impact & Restoration

This application modifies system files to enforce blocking. Below is a list of all files touched and how to restore them manually if needed.

### 1. System Files (Requires Root/Sudo)
These files are modified ONLY when protection is **ACTIVE**.
- **`/etc/hosts`**: The main system hosts file.
- **`/etc/hosts.bak_breakingbadhabits`**: A backup of your original hosts file.
- **Firefox Policies**:
    - `/etc/firefox/policies/policies.json`
    - `/usr/lib/firefox/distribution/policies.json`
    - `/usr/share/firefox/distribution/policies.json`

**Manual Restoration Command:**
```bash
# Restore hosts file
sudo cp /etc/hosts.bak_breakingbadhabits /etc/hosts

# Remove Firefox policies
sudo rm -f /etc/firefox/policies/policies.json
sudo rm -f /usr/lib/firefox/distribution/policies.json
sudo rm -f /usr/share/firefox/distribution/policies.json
```

### 2. User Data & Logs
Stored in `~/.local/share/breakingbadhabits/`
- **`data.json`**: Stores streak, timers, and settings.
- **`app.log`**: Useful for troubleshooting.

**Troubleshooting Log Access:**
```bash
tail -f ~/.local/share/breakingbadhabits/app.log
```

**Full Cleanup (User Data):**
```bash
# Remove autostart entry
rm ~/.config/autostart/breakingbadhabits.desktop

# Remove all app data and logs
rm -rf ~/.local/share/breakingbadhabits/
```
