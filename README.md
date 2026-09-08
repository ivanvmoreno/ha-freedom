# Freedom.to Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Custom Home Assistant component for [Freedom.to](https://freedom.to/), providing real-time tracking and control over your focus sessions, locked mode, session history, and distraction blocking across all your devices.

## Features

- **Sensors & Monitoring**:
  - `binary_sensor.freedom_active_session`: State (`on`/`off`) indicating whether a focus session is actively running, with attributes for session duration, devices, blocklists, and time remaining.
  - `sensor.freedom_session_time_remaining`: Minutes remaining in current session.
  - `sensor.freedom_active_session_name`: Name of active session (e.g. "Deep Work", "Morning").
  - `sensor.freedom_concluded_sessions_count`: All-time completed focus sessions counter.
  - `sensor.freedom_focus_time_last_7_days`: Total focus hours accumulated during the past 7 days.
  - `sensor.freedom_latest_concluded_session`: Timestamp, duration, and notes of your most recent finished session.

- **Controls**:
  - `switch.freedom_locked_mode`: Toggles Freedom's **Locked Mode** on or off to prevent ending sessions early.
  - `button.freedom_end_active_sessions`: One-click button to stop running sessions immediately.

- **Automation Services**:
  - `freedom_to.start_session`: Start a session on-demand (custom duration, device filters, blocklists).
  - `freedom_to.end_all_sessions`: Stop all running sessions.
  - `freedom_to.end_session`: Stop a specific running session.
  - `freedom_to.set_locked_mode`: Turn locked mode on/off programmatically.
  - `freedom_to.add_session_note`: Append reflection notes to completed focus sessions.

---

## Installation

### Method 1: HACS (Recommended)
1. Open **HACS** in Home Assistant.
2. Click the 3 dots in the top-right corner and choose **Custom repositories**.
3. Add `https://github.com/ivanmoreno/ha-freedom` (or your repo URL) with category **Integration**.
4. Search for **Freedom.to** and click **Download**.
5. Restart Home Assistant.

### Method 2: Manual Installation
1. Copy the `custom_components/freedom_to/` folder into your Home Assistant `<config_dir>/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Freedom.to**.
3. Enter your Freedom.to **Email** and **Password**.
4. The integration will automatically discover your devices, blocklists, profile, and active sessions!

---

## Example Automations

### Automatically Start a Focus Session when "Work Mode" is Activated
```yaml
alias: "Start Focus Session on Work Mode"
trigger:
  - platform: state
    entity_id: input_boolean.work_mode
    to: "on"
action:
  - action: freedom_to.start_session
    data:
      duration: 50
      filter_list_names:
        - "Distracting Websites"
      block_everything: false
```

### Flash Lights or Announce when Focus Session Ends
```yaml
alias: "Notify when Freedom Focus Session Ends"
trigger:
  - platform: state
    entity_id: binary_sensor.freedom_active_session
    from: "on"
    to: "off"
action:
  - action: notify.notify
    data:
      title: "Focus Session Finished!"
      message: "Great work! Time for a 10-minute break."
```
