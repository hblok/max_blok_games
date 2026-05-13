# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared helpers for network integration tests.

Uses socket.socketpair() (AF_UNIX stream) for the TCP path so tests
never need to bind a real port or depend on loopback timing.  UDP
sockets are created with bind("127.0.0.1", 0) so the OS assigns an
ephemeral port with no risk of conflicts between tests.
"""

import socket

from maxbloks.tankbattle.network import manager as _manager

NetworkManager = _manager.NetworkManager


def make_tcp_pipe():
    """Return a pair of pre-connected non-blocking AF_UNIX stream sockets."""
    a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    a.setblocking(False)
    b.setblocking(False)
    return a, b


def make_udp_socket():
    """Return a non-blocking UDP socket bound to an ephemeral loopback port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    s.setblocking(False)
    return s


def wire_pair(host_net, client_net):
    """Connect two NetworkManagers without any real TCP stack involvement.

    Injects socketpair sockets directly and sends the initial WELCOME
    handshake messages so the pair is ready for pump_tcp() to complete.
    """
    host_sock, client_sock = make_tcp_pipe()

    host_net.role = "host"
    host_net.tcp_socket_client = host_sock
    host_net.remote_address = ("127.0.0.1", 0)

    client_net.role = "client"
    client_net.tcp_socket = client_sock
    client_net.remote_address = ("127.0.0.1", 0)

    host_net._send_welcome()
    client_net._send_welcome()


def wire_udp(host_net, client_net):
    """Attach ephemeral UDP sockets and cross-wire the peer ports."""
    host_udp = make_udp_socket()
    client_udp = make_udp_socket()

    host_net.udp_socket = host_udp
    client_net.udp_socket = client_udp

    host_net._peer_game_data_port = client_udp.getsockname()[1]
    client_net._peer_game_data_port = host_udp.getsockname()[1]


def pump_tcp(host_net, client_net, n=10):
    """Drive both sides through n TCP message-processing iterations."""
    for _ in range(n):
        host_net.process_tcp_messages()
        client_net.process_tcp_messages()
