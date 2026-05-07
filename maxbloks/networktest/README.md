# Game Console Network Pairing Application

A Python application for local network device discovery and peer-to-peer pairing, designed for handheld game consoles.

## Features

- **Automatic Device Discovery**: Uses UDP broadcasts to discover devices on the local network
- **Peer-to-Peer Connections**: Establishes reliable TCP connections between devices
- **Handheld Console UI**: Built with pygame, designed for directional pad and action button controls
- **Multiple Connections**: Support for connecting to multiple devices simultaneously
- **Connection Management**: Automatic heartbeat monitoring and timeout detection
- **Visual Feedback**: Clear status indicators for searching, connected, and disconnected states

## Technical Details

### Network Protocol

- **Discovery**: UDP broadcasts on port 19019
- **Connections**: TCP on port 19019
- **Message Format**: Length-prefixed JSON messages
- **Heartbeat**: 5-second intervals to maintain connections
- **Timeout**: 15 seconds of inactivity triggers disconnect

### Architecture

┌─────────────────┐
│ Main App        │
│ (main.py)       │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────────┐
    │         │          │             │
┌───▼────┐ ┌─▼───────┐ ┌▼──────────┐ ┌▼─────────┐
│     UI │ │Discovery│ │Connection │ │ Network  │
│Manager │ │ (UDP)   │ │ Manager   │ │ Layer    │
│(pygame)│ │Broadcast│ │ (TCP)     │ │          │
└────────┘ └─────────┘ └───────────┘ └──────────┘
