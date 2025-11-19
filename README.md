# Suntech Message Parser

A Python application that listens for Suntech ST6560 device messages on port 18160, parses them using the Suntech binary protocol, and displays them in a web interface.

## Features

- **Socket Server**: Listens on port 18160 for incoming Suntech messages
- **Message Parser**: Parses STT (Status Report) and BDA/SNB (BLE Sensor Data Report) messages
- **Web Interface**: Displays parsed messages in a beautiful, real-time web interface
- **Thread-Safe**: Handles multiple concurrent connections

## Installation

1. Navigate to the suntech directory:
```bash
cd Queclink/SunTech/suntech
```

2. No external dependencies required - uses only Python standard library!

## Usage

Run the main application:

```bash
python main.py
```

The application will:
- Start a socket server on port **18160** to receive messages
- Start a web server on port **8080** to display messages

Open your browser and navigate to: **http://localhost:8080**

## Message Types

### STT (Status Report) - Header 0x81
- GPS coordinates and status
- Cellular network information
- Device status and mode
- Input/output states

### BDA/SNB (BLE Sensor Data Report) - Header 0xAA
- BLE scan status
- Scanned sensor count
- Sensor location data
- Multi-packet support

## Project Structure

```
suntech/
├── main.py              # Main entry point
├── server.py            # Socket server (port 18160)
├── suntech_parser.py    # Message parser
├── web_server.py        # Web server (port 8080)
├── templates/
│   └── index.html      # Web interface
├── requirements.txt     # Dependencies (none required)
├── push_to_github.ps1  # PowerShell script to push to GitHub
└── README.md           # This file
```

## Protocol Reference

The parser is based on the Suntech ST6560 communication protocol as documented in:
- Universal Reporting Guide
- ST6560 Product Description
- Other protocol documentation in the SunTech folder

## Notes

- Messages are stored in memory (last 1000 messages)
- The socket server echoes back received data to the client
- The web interface auto-refreshes every 2 seconds
- All timestamps are displayed in local time

## GitHub Setup

This project is configured to push to GitHub. To push the code:

1. **Create the repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `Suntech`
   - Description: "Suntech Message Parser - Socket server and web interface for ST6560 device messages"
   - Choose Public or Private
   - **Do NOT** initialize with README, .gitignore, or license (we already have these)
   - Click "Create repository"

2. **Push the code:**
   ```powershell
   # Option 1: Use the provided script
   .\push_to_github.ps1
   
   # Option 2: Manual push
   git branch -M main
   git push -u origin main
   ```

3. **If authentication is required:**
   - For HTTPS: You'll be prompted for username and password (use a Personal Access Token as password)
   - For SSH: Set up SSH keys on GitHub
   - Or use: `git config credential.helper store` to save credentials

Repository URL: https://github.com/shafiqnik/Suntech

