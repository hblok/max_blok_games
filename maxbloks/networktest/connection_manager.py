# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import threading
import json
import time
from typing import Dict, Callable, Optional

class Connection:
    """Represents a connection to a peer device"""
    
    def __init__(self, sock: socket.socket, peer_ip: str):
        self.socket = sock
        self.peer_ip = peer_ip
        self.connected = True
        self.last_activity = time.time()
        
    def send_message(self, message: dict) -> bool:
        """Send a JSON message to the peer"""
        try:
            data = json.dumps(message).encode('utf-8')
            # Prefix with length (4 bytes)
            length = len(data).to_bytes(4, byteorder='big')
            self.socket.sendall(length + data)
            self.last_activity = time.time()
            return True
        except Exception as e:
            print(f"Error sending message to {self.peer_ip}: {e}")
            self.connected = False
            return False
    
    def receive_message(self, timeout: float = 0.1) -> Optional[dict]:
        """Receive a JSON message from the peer"""
        try:
            self.socket.settimeout(timeout)
            
            # Read length prefix
            length_bytes = self._recv_exactly(4)
            if not length_bytes:
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read message data
            data = self._recv_exactly(length)
            if not data:
                return None
            
            message = json.loads(data.decode('utf-8'))
            self.last_activity = time.time()
            return message
            
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error receiving message from {self.peer_ip}: {e}")
            self.connected = False
            return None
    
    def _recv_exactly(self, n: int) -> Optional[bytes]:
        """Receive exactly n bytes from the socket"""
        data = b''
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def close(self):
        """Close the connection"""
        self.connected = False
        try:
            self.socket.close()
        except:
            pass


class ConnectionManager:
    """Manages TCP connections with multiple peer devices"""
    
    LISTEN_PORT = 19019
    HELLO_MESSAGE = "HELLO"
    HEARTBEAT_INTERVAL = 5.0
    CONNECTION_TIMEOUT = 15.0
    
    def __init__(self, on_connection_established: Callable[[str], None],
                 on_connection_lost: Callable[[str], None],
                 on_message_received: Callable[[str, dict], None]):
        """
        Initialize connection manager
        
        Args:
            on_connection_established: Callback when connection is established (peer_ip)
            on_connection_lost: Callback when connection is lost (peer_ip)
            on_message_received: Callback when message is received (peer_ip, message)
        """
        self.on_connection_established = on_connection_established
        self.on_connection_lost = on_connection_lost
        self.on_message_received = on_message_received
        
        self.connections: Dict[str, Connection] = {}
        self.connection_lock = threading.Lock()
        self.running = False
        
        # Server socket for accepting incoming connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.threads = []
        
    def start(self):
        """Start the connection manager"""
        self.running = True
        
        # Bind and listen for incoming connections
        try:
            self.server_socket.bind(('', self.LISTEN_PORT))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            print(f"Listening for connections on port {self.LISTEN_PORT}")
        except Exception as e:
            print(f"Error starting server: {e}")
            return
        
        # Start accept thread
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()
        self.threads.append(accept_thread)
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._send_heartbeats, daemon=True)
        heartbeat_thread.start()
        self.threads.append(heartbeat_thread)
        
        # Start connection monitor thread
        monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        monitor_thread.start()
        self.threads.append(monitor_thread)
    
    def connect_to_peer(self, peer_ip: str) -> bool:
        """
        Initiate connection to a peer device
        
        Args:
            peer_ip: IP address of the peer
            
        Returns:
            True if connection was successful, False otherwise
        """
        # Check if already connected
        with self.connection_lock:
            if peer_ip in self.connections and self.connections[peer_ip].connected:
                return True
        
        try:
            # Create socket and connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((peer_ip, self.LISTEN_PORT))
            
            # Send hello message
            connection = Connection(sock, peer_ip)
            hello = {
                "type": self.HELLO_MESSAGE,
                "timestamp": time.time()
            }
            
            if not connection.send_message(hello):
                sock.close()
                return False
            
            # Store connection
            with self.connection_lock:
                self.connections[peer_ip] = connection
            
            # Start receive thread for this connection
            recv_thread = threading.Thread(
                target=self._receive_messages,
                args=(peer_ip,),
                daemon=True
            )
            recv_thread.start()
            self.threads.append(recv_thread)
            
            self.on_connection_established(peer_ip)
            print(f"Connected to {peer_ip}")
            return True
            
        except Exception as e:
            print(f"Error connecting to {peer_ip}: {e}")
            return False
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                sock, addr = self.server_socket.accept()
                peer_ip = addr[0]
                
                print(f"Accepted connection from {peer_ip}")
                
                # Create connection object
                connection = Connection(sock, peer_ip)
                
                # Wait for hello message
                hello = connection.receive_message(timeout=5.0)
                if not hello or hello.get("type") != self.HELLO_MESSAGE:
                    print(f"Invalid hello from {peer_ip}")
                    sock.close()
                    continue
                
                # Store connection
                with self.connection_lock:
                    # Close existing connection if any
                    if peer_ip in self.connections:
                        self.connections[peer_ip].close()
                    self.connections[peer_ip] = connection
                
                # Start receive thread for this connection
                recv_thread = threading.Thread(
                    target=self._receive_messages,
                    args=(peer_ip,),
                    daemon=True
                )
                recv_thread.start()
                self.threads.append(recv_thread)
                
                self.on_connection_established(peer_ip)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")
    
    def _receive_messages(self, peer_ip: str):
        """Receive messages from a specific peer"""
        while self.running:
            with self.connection_lock:
                if peer_ip not in self.connections:
                    break
                connection = self.connections[peer_ip]
            
            if not connection.connected:
                break
            
            message = connection.receive_message()
            if message:
                # Handle heartbeat internally
                if message.get("type") == "HEARTBEAT":
                    continue
                
                # Notify application of message
                self.on_message_received(peer_ip, message)
    
    def _send_heartbeats(self):
        """Send periodic heartbeats to all connected peers"""
        while self.running:
            time.sleep(self.HEARTBEAT_INTERVAL)
            
            with self.connection_lock:
                peers = list(self.connections.keys())
            
            for peer_ip in peers:
                self.send_message(peer_ip, {"type": "HEARTBEAT"})
    
    def _monitor_connections(self):
        """Monitor connections and detect timeouts"""
        while self.running:
            time.sleep(2.0)
            
            with self.connection_lock:
                disconnected = []
                current_time = time.time()
                
                for peer_ip, connection in self.connections.items():
                    # Check if connection is still alive
                    if not connection.connected:
                        disconnected.append(peer_ip)
                    # Check for timeout
                    elif current_time - connection.last_activity > self.CONNECTION_TIMEOUT:
                        print(f"Connection to {peer_ip} timed out")
                        connection.close()
                        disconnected.append(peer_ip)
                
                # Remove disconnected peers
                for peer_ip in disconnected:
                    del self.connections[peer_ip]
            
            # Notify about disconnections
            for peer_ip in disconnected:
                self.on_connection_lost(peer_ip)
    
    def send_message(self, peer_ip: str, message: dict) -> bool:
        """
        Send a message to a specific peer
        
        Args:
            peer_ip: IP address of the peer
            message: Dictionary to send as JSON
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        with self.connection_lock:
            if peer_ip not in self.connections:
                return False
            connection = self.connections[peer_ip]
        
        return connection.send_message(message)
    
    def get_connected_peers(self) -> list:
        """Get list of currently connected peer IPs"""
        with self.connection_lock:
            return [ip for ip, conn in self.connections.items() if conn.connected]
    
    def disconnect_peer(self, peer_ip: str):
        """Disconnect from a specific peer"""
        with self.connection_lock:
            if peer_ip in self.connections:
                self.connections[peer_ip].close()
                del self.connections[peer_ip]
        
        self.on_connection_lost(peer_ip)
    
    def stop(self):
        """Stop the connection manager"""
        self.running = False
        
        # Close all connections
        with self.connection_lock:
            for connection in self.connections.values():
                connection.close()
            self.connections.clear()
        
        # Close server socket
        try:
            self.server_socket.close()
        except:
            pass
        
        # Wait for threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        print("Connection manager stopped")
