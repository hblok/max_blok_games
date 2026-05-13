# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Menu and lobby state handlers for TankBattleGame."""

import logging
import subprocess
import time

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle.states import GameState

logger = logging.getLogger(__name__)


def _get_wifi_ssid():
    """Best-effort retrieval of the current WiFi SSID.

    Works on typical Linux handhelds (nmcli) and falls back
    gracefully on other platforms or when not connected via WiFi.
    """
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            capture_output=True, text=True, timeout=2,
        )
        for line in result.stdout.strip().splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1]
    except Exception:
        pass
    return None


class MenuMixin:
    """Menu and lobby input/update methods."""

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def handle_input_menu(self, input_state):
        # Use edge-detected navigation so each button press moves
        # the cursor exactly one position, regardless of how long
        # the button is held.
        if input_state.menu_up_just_pressed:
            self.menu_index = (self.menu_index - 1) % len(constants.MENU_ITEMS)
        if input_state.menu_down_just_pressed:
            self.menu_index = (self.menu_index + 1) % len(constants.MENU_ITEMS)
        # Also support the legacy menu_y event (hat-based, one-shot)
        if input_state.menu_y != 0:
            self.menu_index = (self.menu_index + input_state.menu_y) % len(constants.MENU_ITEMS)
        if input_state.confirm_just_pressed:
            if self.menu_index == 0:
                self.single_player = True
                self.start_match()
            elif self.menu_index == 1:
                self._enter_lobby(is_host=True)
            elif self.menu_index == 2:
                self._enter_lobby(is_host=False)
            else:
                self.running = False

    def _enter_lobby(self, is_host):
        """Transition from MENU to LOBBY, starting discovery."""
        role = "host" if is_host else "client"
        logger.info("Entering lobby as %s", role)
        self.lobby_is_host = is_host
        self.lobby_index = 0
        self.lobby_host_select_index = 0
        self.lobby_discovered_clients.clear()
        self.lobby_connected_clients.clear()
        self.lobby_client_last_seen.clear()
        self.lobby_handshake_confirmed.clear()
        self.lobby_local_ip = self.net.local_ip
        self.lobby_wifi_ssid = _get_wifi_ssid()
        if is_host:
            self.net.start_host()
        self.net.start_discovery(is_host=is_host)
        self.state = GameState.LOBBY

    # ------------------------------------------------------------------
    # Lobby input
    # ------------------------------------------------------------------

    def handle_input_lobby(self, input_state):
        if self.lobby_is_host:
            # Host lobby: navigate lobby action menu
            if input_state.menu_up_just_pressed:
                self.lobby_index = (self.lobby_index - 1) % len(constants.LOBBY_ITEMS)
            if input_state.menu_down_just_pressed:
                self.lobby_index = (self.lobby_index + 1) % len(constants.LOBBY_ITEMS)
            if input_state.menu_y != 0:
                self.lobby_index = (self.lobby_index + input_state.menu_y) % len(constants.LOBBY_ITEMS)
        else:
            # Join lobby: navigate between host list and action menu
            hosts = [h for h in self.lobby_discovered_clients if h.get("hosting")]
            total_items = len(hosts) + len(constants.LOBBY_ITEMS)
            if input_state.menu_up_just_pressed:
                self.lobby_index = (self.lobby_index - 1) % max(1, total_items)
            if input_state.menu_down_just_pressed:
                self.lobby_index = (self.lobby_index + 1) % max(1, total_items)
            if input_state.menu_y != 0:
                self.lobby_index = (self.lobby_index + input_state.menu_y) % max(1, total_items)

        if input_state.pause_just_pressed:
            logger.info("Leaving lobby, returning to menu")
            self.net.stop_discovery()
            self.state = GameState.MENU
        if input_state.confirm_just_pressed:
            if self.lobby_is_host:
                # Host action menu
                if self.lobby_index == 0:  # Start
                    logger.info("Host starting match from lobby")
                    self.net.stop_discovery()
                    self.local_player_index = 0
                    self.single_player = False
                    # Send arena seed to client so it generates the same map.
                    # We only send the seed (not the full obstacle list)
                    # because Arena() generates deterministically from it,
                    # and the full serialised arena (~140 KB) caused the
                    # TCP recv buffer to overflow and lose the match_start
                    # event that follows.
                    if self.net.tcp_socket_client is not None:
                        self.net.send_reliable_event("arena_seed", {"seed": self.arena.seed})
                        logger.info("Host: Sent arena seed to client (seed=%d)", self.arena.seed)
                        self.net.send_reliable_event("match_start")
                        logger.info("Host: Sent match_start event to client")
                    self.start_match()
                elif self.lobby_index == 1:  # Manual IP — future work
                    pass
                else:  # Back
                    logger.info("Host leaving lobby, returning to menu")
                    self.net.stop_discovery()
                    self.state = GameState.MENU
            else:
                # Join lobby: check if a host is selected or an action item
                hosts = [h for h in self.lobby_discovered_clients if h.get("hosting")]
                num_hosts = len(hosts)
                if self.lobby_index < num_hosts and num_hosts > 0:
                    # A host was selected — connect to it
                    selected_host = hosts[self.lobby_index]
                    host_ip = selected_host["address"]
                    host_port = selected_host.get("port", constants.HOST_PORT)
                    self._connect_to_selected_host(host_ip, host_port)
                else:
                    # Action menu items (offset by number of hosts)
                    action_index = self.lobby_index - num_hosts
                    if action_index == 0:  # Manual IP — future work
                        pass
                    elif action_index == 1:  # Back
                        self.net.stop_discovery()
                        self.state = GameState.MENU

    def _connect_to_selected_host(self, host_ip, host_port):
        """Attempt to connect to a selected host from the join lobby."""
        logger.info("Connecting to host %s:%d", host_ip, host_port)
        try:
            self.net.connect_to_host(host_ip, host_port)
            self.lobby_connected_clients.append(host_ip)
            # NOTE: Do NOT mark handshake_confirmed yet — the welcome-ack
            # from the host has not been received.  The confirmation will
            # be set in update_lobby() once the ConnectionMonitor reports
            # the bidirectional handshake as complete.
            logger.info("TCP connection to host %s established, awaiting welcome-ack", host_ip)
        except Exception as e:
            logger.error("Connection to %s failed: %s", host_ip, e, exc_info=True)

    # ------------------------------------------------------------------
    # Lobby update
    # ------------------------------------------------------------------

    def update_lobby(self, dt):
        """Refresh lobby discovery data, accept host connections, and
        process welcome handshake messages."""
        now = time.monotonic()

        # Prune stale discovered peers (timeout > 10 s)
        stale = [
            ip for ip, ts in self.lobby_client_last_seen.items()
            if now - ts > constants.DISCOVERY_TIMEOUT
        ]
        for ip in stale:
            del self.lobby_client_last_seen[ip]
            # Also remove from handshake confirmed if stale
            self.lobby_handshake_confirmed.pop(ip, None)
            logger.debug("Pruned stale peer %s from lobby", ip)

        # Refresh discovered peer list from NetworkManager
        self.lobby_discovered_clients = list(self.net.discovered_hosts)

        # Track discovery timestamps for all discovered peers
        for host_info in self.lobby_discovered_clients:
            ip = host_info.get("address", "")
            if ip:
                self.lobby_client_last_seen[ip] = now

        # If host, try to accept a TCP connection
        if self.lobby_is_host and self.net.tcp_socket is not None:
            try:
                conn, addr = self.net.tcp_socket.accept()
                logger.info("Host: Accepted TCP connection from %s:%d", addr[0], addr[1])
                # Store the accepted connection immediately so that
                # process_tcp_messages() can read the welcome handshake
                # on the next frame.  The client sends TANKBATTLE_WELCOME
                # (not TANKBATTLE_HELLO), so we must NOT call
                # parse_handshake() here — that function expects the
                # legacy HELLO prefix and would silently discard the
                # connection.
                conn.setblocking(False)
                self.net.tcp_socket_client = conn
                self.net.remote_address = addr
                peer_ip = addr[0]
                if peer_ip not in self.lobby_connected_clients:
                    self.lobby_connected_clients.append(peer_ip)
                logger.info("Host: Stored client connection %s, waiting for welcome handshake", peer_ip)
                # Send host welcome handshake immediately; the client's
                # welcome will be processed by process_tcp_messages().
                self.net._send_welcome()
            except BlockingIOError:
                pass
            except Exception as e:
                logger.error("Host: Error accepting connection: %s", e, exc_info=True)

        # Process TCP messages (welcome handshake, reliable events)
        events = self.net.process_tcp_messages()
        for event_name, payload in events:
            logger.debug("Lobby TCP event: %s (payload keys=%s)", event_name, list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
            if event_name == "arena_seed" and not self.lobby_is_host:
                seed = payload.get("seed", 0)
                logger.info("Client: Received arena seed from host (seed=%d)", seed)
                # Rebuild arena from the host's seed so both sides play on identical map
                self.arena = arena.Arena(seed)
                logger.info("Client: Rebuilt arena from host seed")
            elif event_name == "match_start" and not self.lobby_is_host:
                logger.info("Client: Received match_start from host — starting match")
                self.net.stop_discovery()
                self.local_player_index = 1
                self.single_player = False
                self.start_match()
            # Handle other reliable game events if needed

        # Update handshake confirmation status based on connection monitor
        if self.net.monitor.connected:
            remote_ip = self.net.remote_address[0] if self.net.remote_address else None
            if remote_ip and remote_ip not in self.lobby_handshake_confirmed:
                self.lobby_handshake_confirmed[remote_ip] = True
