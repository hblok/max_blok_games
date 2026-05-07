# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import time

from maxbloks.networktest import connection_manager
from maxbloks.networktest import constants
from maxbloks.networktest import network_discovery
from maxbloks.networktest import ui_manager


class GameConsolePairingApp:
    """Main application class"""

    def __init__(self):
        self.discovered_devices = {}

        self.ui = ui_manager.UIManager(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self.ui.on_connect_pressed = self.handle_connect
        self.ui.on_disconnect_pressed = self.handle_disconnect

        self.connection_manager = connection_manager.ConnectionManager(
            on_connection_established=self.on_connection_established,
            on_connection_lost=self.on_connection_lost,
            on_message_received=self.on_message_received,
        )

        self.network_discovery = network_discovery.NetworkDiscovery(
            on_device_discovered=self.on_device_discovered
        )

        self.ui.set_local_ip(self.network_discovery.local_ip)
        self.ui.set_status("Starting services...", "info")

    def start(self):
        """Start all services"""
        self.connection_manager.start()
        self.network_discovery.start()
        self.ui.set_status("Searching for devices...", "info")

    def on_device_discovered(self, ip: str, device_info: dict):
        """Callback when a device is discovered"""
        self.discovered_devices[ip] = time.time()
        print(f"Device discovered: {ip}")

    def on_connection_established(self, peer_ip: str):
        """Callback when connection is established"""
        print(f"Connection established with {peer_ip}")
        self.ui.set_status(f"Connected to {peer_ip}", "success")

    def on_connection_lost(self, peer_ip: str):
        """Callback when connection is lost"""
        print(f"Connection lost with {peer_ip}")
        self.ui.set_status(f"Disconnected from {peer_ip}", "warning")

    def on_message_received(self, peer_ip: str, message: dict):
        """Callback when message is received from a peer"""
        print(f"Message from {peer_ip}: {message}")

        msg_type = message.get("type", "unknown")

        if msg_type == "chat":
            text = message.get("text", "")
            self.ui.set_status(f"{peer_ip}: {text}", "info")
        elif msg_type == "game_data":
            data = message.get("data", {})
            print(f"Game data received: {data}")

    def handle_connect(self, device_ip: str):
        """Handle connect button press"""
        print(f"Attempting to connect to {device_ip}")
        self.ui.set_status(f"Connecting to {device_ip}...", "info")

        success = self.connection_manager.connect_to_peer(device_ip)

        if not success:
            self.ui.set_status(f"Failed to connect to {device_ip}", "error")

    def handle_disconnect(self, device_ip: str):
        """Handle disconnect button press"""
        print(f"Disconnecting from {device_ip}")
        self.connection_manager.disconnect_peer(device_ip)

    def update_ui(self):
        """Update UI with current state"""
        current_time = time.time()
        stale_devices = [
            ip for ip, last_seen in self.discovered_devices.items()
            if current_time - last_seen > constants.DEVICE_TIMEOUT
        ]

        for ip in stale_devices:
            del self.discovered_devices[ip]
            print(f"Device {ip} timed out")

        self.ui.set_discovered_devices(sorted(self.discovered_devices.keys()))
        self.ui.set_connected_devices(self.connection_manager.get_connected_peers())

    def send_example_message(self, peer_ip: str):
        """Example method to send a custom message to a peer"""
        message = {
            "type": "chat",
            "text": "Hello from the game console!",
            "timestamp": time.time(),
        }
        self.connection_manager.send_message(peer_ip, message)

    def run(self):
        """Main application loop"""
        self.start()

        print("\n" + "=" * 60)
        print("Game Console Network Pairing")
        print("=" * 60)
        print(f"Local IP: {self.network_discovery.local_ip}")
        print(f"Listening on port: {connection_manager.ConnectionManager.LISTEN_PORT}")
        print("\nControls:")
        print("  UP/DOWN arrows - Select device")
        print("  A/Z/ENTER      - Connect to selected device")
        print("  B/X/ESC        - Disconnect selected if connected")
        print("  ESC            - Quit application")
        print("=" * 60 + "\n")

        try:
            while self.ui.running:
                if not self.ui.handle_events():
                    break

                self.update_ui()
                self.ui.render()
                self.ui.update(fps=constants.TARGET_FPS)

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        """Cleanup and shutdown"""
        print("Stopping services...")

        self.network_discovery.stop()
        self.connection_manager.stop()
        self.ui.quit()

        print("Shutdown complete")


def main():
    app = GameConsolePairingApp()
    app.run()
    sys.exit(0)


if __name__ == "__main__":
    main()
