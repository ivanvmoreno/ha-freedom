# Freedom.to Integration for Home Assistant

<p align="center">
  <img src="custom_components/freedom_to/brand/logo.png" alt="Freedom.to Logo" width="360">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS Custom"></a>
  <a href="https://github.com/ivanvmoreno/ha-freedom/releases"><img src="https://img.shields.io/github/v/release/ivanvmoreno/ha-freedom?style=for-the-badge&color=blue" alt="Latest Release"></a>
  <a href="https://github.com/ivanvmoreno/ha-freedom/blob/main/LICENSE"><img src="https://img.shields.io/github/license/ivanvmoreno/ha-freedom?style=for-the-badge&color=green" alt="License"></a>
</p>

A custom Home Assistant integration for [Freedom.to](https://freedom.to/), providing real-time tracking, statistics, and full interactive control over your focus sessions, locked mode, devices, and distraction blocking.

---

## 🌟 Features

- ⏱️ **Focus Session Management**:
  - Start sessions directly from your dashboard or automations with customizable durations, blocklists, and target devices.
  - **Dynamic Session Templates**: Create one-click button templates (e.g. *Pomodoro 25m*, *Deep Work 60m*) with specific devices and blocklists via the integration's UI configuration popup.
  - Interactive **Duration Slider** (`number.freedom_session_duration`) and **Blocklist Dropdown** (`select.freedom_session_blocklist`) for instant ad-hoc session launching.
  - One-click **Emergency End Session** button.
- 🔒 **Locked Mode Toggle**:
  - Switch entity (`switch.freedom_locked_mode`) to enable or disable Freedom's **Locked Mode** (`strong_mode`).
- 📊 **Rich Sensors & Real-time State**:
  - `binary_sensor.freedom_active_session`: On/off state with detailed session metadata (remaining seconds, target devices, active blocklists, schedule details).
  - `sensor.freedom_session_time_remaining`: Minutes left in current session.
  - `sensor.freedom_active_session_name`: Name of active session.
  - `sensor.freedom_concluded_sessions_count`: All-time focus sessions completed.
  - `sensor.freedom_focus_time_last_7_days`: Total hours focused over the last 7 days.
  - `sensor.freedom_latest_concluded_session`: Details and reflection notes of your most recent finished session.
- ⚡ **Automations & Actions (`services.yaml`)**:
  - `freedom_to.start_session`
  - `freedom_to.end_all_sessions`
  - `freedom_to.end_session`
  - `freedom_to.set_locked_mode`
  - `freedom_to.add_session_note`

---

## 📦 Installation

### Option 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ivanvmoreno&repository=ha-freedom&category=integration)

1. Open **HACS** in your Home Assistant UI.
2. Click the three dots (**⋮**) in the top right corner and select **Custom repositories**.
3. In the dialog, enter:
   - **Repository**: `https://github.com/ivanvmoreno/ha-freedom`
   - **Type**: `Integration`
4. Click **Add**.
5. Search for **Freedom.to**, click on it, and select **Download**.
6. **Restart Home Assistant** (`Settings` -> `System` -> `Restart`).

### Option 2: Manual Installation

1. Download the latest release from the [Releases page](https://github.com/ivanvmoreno/ha-freedom/releases).
2. Extract the archive and copy the `custom_components/freedom_to` directory to your Home Assistant configuration directory under:
   ```text
   <config_dir>/custom_components/freedom_to/
   ```
3. **Restart Home Assistant**.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Freedom.to** and select it.
4. Enter your Freedom.to **Email** and **Password**.
5. Click **Submit**. The integration will discover your devices, blocklists, profile, and active sessions!

---

## 🚀 Creating Session Templates

Want dedicated buttons for your favorite focus routines?

1. Go to **Settings** > **Devices & Services** > **Freedom.to**.
2. Click the **Configure** button on the integration card.
3. Select **Add Session Template**.
4. Configure:
   - **Template Name**: e.g., *"Deep Work 60m"*
   - **Duration**: Duration in minutes
   - **Devices**: Select which of your synced devices should be locked down
   - **Blocklists**: Select which filter lists to activate
   - **Block Apps** / **Block Internet**: Optional toggles
5. Click **Submit**. A new button entity (`button.freedom_start_<template_name>`) will be generated automatically!

---

## 💡 Automation Examples

### 1. Automatically Start a Focus Session when "Work Mode" is Activated
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

### 2. Notify & Flash Lights when Focus Session Ends
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
      title: "Focus Session Finished! 🎯"
      message: "Time for a 10-minute break."
```

### 3. Start Session from an NFC Tag or Zigbee Button
```yaml
alias: "Desk NFC Tag - Start Pomodoro"
trigger:
  - platform: tag
    tag_id: "pomodoro-tag"
action:
  - action: button.press
    target:
      entity_id: button.freedom_start_pomodoro_25m
```

---

## 🛠️ Diagnostics & Troubleshooting

To enable debug logging for troubleshooting, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.freedom_to: debug
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
