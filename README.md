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

