# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import types
import unittest

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import net_handlers
from maxbloks.tankbattle import states
from maxbloks.tankbattle.network import dead_reckoner


class _StubGame(net_handlers.NetworkHandlersMixin):
    """Minimal game stub that satisfies NetworkHandlersMixin's attribute requirements."""

    def __init__(self):
        self.local_player_index = 0
        self.tanks = [
            entities.Tank(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0, 135.0, player_id=1),
            entities.Tank(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0, 315.0, player_id=2),
        ]
        self.bullets = []
        self.mines = []
        self.powerups = []
        self.single_player = False
        self.lobby_is_host = False
        self._hp_sync_timer = 0.0
        self._round_seq = 0
        self._neutral_sync_timer = 0.0
        self.neutral_tanks = []
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1
        self.state = states.GameState.PLAYING
        self.state_timer = 0.0
        self.round_wins = [0, 0]
        self._match_over_option = 0
        self.match_seed = 0
        self.arena = arena.Arena(0)
        self._reliable_events_sent = []
        self.net = types.SimpleNamespace(
            should_send_update=lambda now: False,
            send_player_update=lambda pkt: None,
            receive_udp=lambda: [],
            dead_reckoner=dead_reckoner.DeadReckoner(),
            send_reliable_event=lambda name, payload=None: self._reliable_events_sent.append((name, payload)),
        )

    @property
    def local_tank(self):
        return self.tanks[self.local_player_index]

    @property
    def remote_tank(self):
        return self.tanks[1 - self.local_player_index]

    def _add_bullet(self, tank, angle, speed=constants.BULLET_SPEED, damage=constants.BULLET_DAMAGE, weapon=entities.WeaponType.PRIMARY, bounces=0):
        pass

    def _do_rematch(self):
        self.state = states.GameState.COUNTDOWN
        self.round_wins = [0, 0]


class TestNetworkHandlersMixin(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()

    # --- _apply_dead_reckoning ---

    def test_apply_dead_reckoning_does_nothing_without_packet(self):
        x_before = self.g.remote_tank.x
        self.g._apply_dead_reckoning()
        self.assertEqual(self.g.remote_tank.x, x_before)

    def test_apply_dead_reckoning_updates_remote_position(self):
        from maxbloks.tankbattle.network.packet import PlayerUpdatePacket
        pkt = PlayerUpdatePacket(2, 999.0, 888.0, 0.0, 0.0, 10, "primary", 0.0)
        self.g.net.dead_reckoner.push_update(pkt)
        self.g._apply_dead_reckoning()
        self.assertAlmostEqual(self.g.remote_tank.x, 999.0, places=0)
        self.assertAlmostEqual(self.g.remote_tank.y, 888.0, places=0)

    # --- _send_hp_sync ---

    def test_send_hp_sync_skips_when_not_host(self):
        self.g.lobby_is_host = False
        self.g._hp_sync_timer = -1.0
        self.g._send_hp_sync(0.0)
        self.assertEqual(len(self.g._reliable_events_sent), 0)

    def test_send_hp_sync_skips_when_timer_positive(self):
        self.g.lobby_is_host = True
        self.g._hp_sync_timer = 5.0
        self.g._send_hp_sync(0.1)
        self.assertEqual(len(self.g._reliable_events_sent), 0)

    def test_send_hp_sync_fires_when_host_and_timer_expired(self):
        self.g.lobby_is_host = True
        self.g._hp_sync_timer = 0.0
        self.g._send_hp_sync(0.1)
        self.assertEqual(len(self.g._reliable_events_sent), 1)
        self.assertEqual(self.g._reliable_events_sent[0][0], "hp_sync")

    def test_send_hp_sync_resets_timer(self):
        self.g.lobby_is_host = True
        self.g._hp_sync_timer = 0.0
        self.g._send_hp_sync(0.1)
        self.assertAlmostEqual(self.g._hp_sync_timer, constants.HP_SYNC_INTERVAL)

    # --- _handle_tcp_events_playing ---

    def test_handle_tcp_events_playing_ignored_by_host(self):
        self.g.lobby_is_host = True
        self.g.tanks[0].hp = 10
        self.g._handle_tcp_events_playing([("hp_sync", {"hp": [5, 10], "seq": self.g._round_seq})])
        self.assertEqual(self.g.tanks[0].hp, 10)

    def test_handle_tcp_events_playing_corrects_remote_hp(self):
        self.g.lobby_is_host = False
        self.g.local_player_index = 0
        self.g.tanks[1].hp = 10
        self.g._handle_tcp_events_playing([("hp_sync", {"hp": [10, 6], "seq": self.g._round_seq})])
        self.assertEqual(self.g.tanks[1].hp, 6)

    def test_handle_tcp_events_playing_local_tank_only_decreases(self):
        self.g.lobby_is_host = False
        self.g.local_player_index = 0
        self.g.tanks[0].hp = 5
        self.g._handle_tcp_events_playing([("hp_sync", {"hp": [10, 10], "seq": self.g._round_seq})])
        # Auth HP is higher than current; should NOT increase
        self.assertEqual(self.g.tanks[0].hp, 5)


    # --- Round sequence (stale message protection) ---

    def test_stale_hp_sync_ignored_after_round_reset(self):
        """Stale hp_sync from a previous round must not corrupt reset HP."""
        self.g.lobby_is_host = False
        self.g.local_player_index = 0
        # Simulate round 1: client dies (hp=0)
        self.g.tanks[0].hp = 0
        # Round resets: _round_seq increments, HP restored
        self.g._round_seq = 2
        self.g.tanks[0].hp = constants.TANK_MAX_HP
        self.g.tanks[1].hp = constants.TANK_MAX_HP
        # Late-arriving hp_sync from round 1 (seq=1) arrives in round 2
        self.g._handle_tcp_events_playing([("hp_sync", {"hp": [0, 10], "seq": 1})])
        # Client HP must NOT be lowered to 0 by the stale message
        self.assertEqual(self.g.tanks[0].hp, constants.TANK_MAX_HP)

    def test_current_round_hp_sync_is_applied(self):
        """hp_sync from the current round must still be applied."""
        self.g.lobby_is_host = False
        self.g.local_player_index = 0
        self.g._round_seq = 2
        self.g.tanks[1].hp = 10
        # hp_sync from the current round
        self.g._handle_tcp_events_playing([("hp_sync", {"hp": [10, 6], "seq": 2})])
        self.assertEqual(self.g.tanks[1].hp, 6)

    def test_stale_neutral_sync_ignored_after_round_reset(self):
        """Stale neutral_sync from a previous round must be ignored."""
        self.g.lobby_is_host = False
        # Create a neutral tank
        self.g.neutral_tanks = [entities.Tank(500.0, 500.0, player_id=0, is_neutral=True)]
        self.g.neutral_tanks[0].hp = 5
        # Round 2
        self.g._round_seq = 2
        # Late-arriving neutral_sync from round 1 (seq=1)
        payload = {"tanks": [[999.0, 888.0, 45.0, 90.0, 3, True]], "seq": 1}
        self.g._handle_tcp_events_playing([("neutral_sync", payload)])
        # Neutral tank position must NOT be overwritten
        self.assertAlmostEqual(self.g.neutral_tanks[0].x, 500.0)

    def test_send_hp_sync_includes_round_seq(self):
        """hp_sync payload must include the current round sequence number."""
        self.g.lobby_is_host = True
        self.g._hp_sync_timer = 0.0
        self.g._round_seq = 7
        self.g._send_hp_sync(0.1)
        self.assertEqual(self.g._reliable_events_sent[0][1]["seq"], 7)

    def test_send_neutral_sync_includes_round_seq(self):
        """neutral_sync payload must include the current round sequence number."""
        self.g.lobby_is_host = True
        self.g._neutral_sync_timer = 0.0
        self.g._round_seq = 5
        self.g.neutral_tanks = [entities.Tank(500.0, 500.0, player_id=0, is_neutral=True)]
        self.g._send_neutral_sync(0.1)
        self.assertEqual(self.g._reliable_events_sent[0][1]["seq"], 5)

    def test_stale_udp_packet_ignored_after_round_reset(self):
        """Stale UDP packet from a previous round must not corrupt tank HP."""
        from maxbloks.tankbattle.network.packet import PlayerUpdatePacket
        self.g.local_player_index = 0
        # Round 2
        self.g._round_seq = 2
        self.g.tanks[1].hp = constants.TANK_MAX_HP
        # Simulate receiving a stale UDP packet from round 1
        stale_pkt = PlayerUpdatePacket(
            2, 500.0, 500.0, 0.0, 0.0, 0, "primary", 0.0, round_seq=1,
        )
        # Override receive_udp to return the stale packet
        self.g.net = types.SimpleNamespace(
            should_send_update=lambda now: False,
            send_player_update=lambda pkt: None,
            receive_udp=lambda: [stale_pkt],
            dead_reckoner=dead_reckoner.DeadReckoner(),
            send_reliable_event=lambda name, payload=None: self.g._reliable_events_sent.append((name, payload)),
        )
        self.g._receive_network_updates()
        # HP must NOT be set to 0 from the stale packet
        self.assertEqual(self.g.tanks[1].hp, constants.TANK_MAX_HP)

    # --- _handle_tcp_events_match_over ---

    def test_handle_tcp_events_match_over_triggers_rematch_on_event(self):
        self.g._handle_tcp_events_match_over([("rematch", {"seed": 12345})])
        self.assertEqual(self.g.state, states.GameState.COUNTDOWN)

    def test_handle_tcp_events_match_over_updates_seed(self):
        self.g._handle_tcp_events_match_over([("rematch", {"seed": 99999})])
        self.assertEqual(self.g.match_seed, 99999)

    def test_handle_tcp_events_match_over_host_sends_seed_when_no_seed(self):
        self.g.lobby_is_host = True
        self.g._handle_tcp_events_match_over([("rematch", {})])
        sent_names = [e[0] for e in self.g._reliable_events_sent]
        self.assertIn("rematch", sent_names)
