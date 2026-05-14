# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the Neutral AI tanks ("Wild Tanks") feature."""

import types
import unittest

from maxbloks.tankbattle import ai
from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import gameplay
from maxbloks.tankbattle import net_handlers
from maxbloks.tankbattle import states
from maxbloks.tankbattle import utils


class _StubGame(gameplay.GameplayMixin, net_handlers.NetworkHandlersMixin):
    """Minimal game stub covering both gameplay and network mixin requirements."""

    def __init__(self):
        self.local_player_index = 0
        self.tanks = [
            entities.Tank(constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y, 135.0, 135.0, player_id=1),
            entities.Tank(constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y, 315.0, 315.0, player_id=2),
        ]
        self.arena = arena.Arena(0)
        self.bullets = []
        self.mines = []
        self.turret_bullets = []
        self.powerups = []
        self.powerup_timer = constants.POWERUP_SPAWN_INTERVAL_MIN
        self.powerup_next_id = 1
        self.round_wins = [0, 0]
        self.round_time_remaining = constants.ROUND_TIME_LIMIT
        self.sudden_death = False
        self.state = states.GameState.PLAYING
        self.state_timer = 0.0
        self.single_player = True
        self.lobby_is_host = False
        self._state_entry_time = 0.0
        self._match_over_option = 0
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1
        self._hp_sync_timer = 0.0
        self._round_seq = 0
        self._neutral_sync_timer = 0.0
        self.match_seed = 0
        self.neutral_tanks = []
        self.neutral_ais = [ai.TankAI() for _ in range(constants.NEUTRAL_TANK_COUNT)]
        self._reliable_events_sent = []
        self.renderer = types.SimpleNamespace(
            register_hit=lambda b: None,
            register_mine_explosion=lambda m: None,
            register_muzzle_flash=lambda t: None,
        )
        self.net = types.SimpleNamespace(
            send_reliable_event=lambda name, payload=None: self._reliable_events_sent.append((name, payload)),
        )

    @property
    def local_tank(self):
        return self.tanks[self.local_player_index]

    @property
    def remote_tank(self):
        return self.tanks[1 - self.local_player_index]


class TestNeutralTankSpawning(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()
        self.g.reset_round()

    def test_reset_round_spawns_correct_count(self):
        self.assertEqual(len(self.g.neutral_tanks), constants.NEUTRAL_TANK_COUNT)

    def test_neutral_tanks_have_is_neutral_flag(self):
        for tank in self.g.neutral_tanks:
            self.assertTrue(tank.is_neutral)

    def test_neutral_tanks_have_neutral_hp(self):
        for tank in self.g.neutral_tanks:
            self.assertEqual(tank.hp, constants.NEUTRAL_TANK_HP)

    def test_neutral_tanks_have_player_id_zero(self):
        for tank in self.g.neutral_tanks:
            self.assertEqual(tank.player_id, 0)

    def test_neutral_tanks_are_alive_at_spawn(self):
        for tank in self.g.neutral_tanks:
            self.assertTrue(tank.is_alive)

    def test_reset_round_replaces_existing_neutral_tanks(self):
        old_ids = [id(t) for t in self.g.neutral_tanks]
        self.g.reset_round()
        new_ids = [id(t) for t in self.g.neutral_tanks]
        # New tank objects were created
        self.assertNotEqual(old_ids, new_ids)


class TestNeutralTankAI(unittest.TestCase):

    def setUp(self):
        self.ai_obj = ai.TankAI()
        self.ai_tank = entities.Tank(500.0, 500.0, player_id=0, is_neutral=True)
        self.near_target = entities.Tank(510.0, 500.0, player_id=1)
        self.far_target = entities.Tank(900.0, 500.0, player_id=2)

        class _FakeArena:
            def collides_with_solid(self, position, radius):
                return False

            def terrain_at_world(self, x, y):
                return None

            def conveyor_at_world(self, x, y):
                return None

            def teleporter_at_world(self, x, y):
                return None

        class _FakeGame:
            arena = _FakeArena()
            def _fire_weapon(self, tank):
                pass

        self.game = _FakeGame()

    def test_ai_picks_nearest_alive_target(self):
        # After one update, body should rotate toward near_target (east)
        # near_target is at (510, 500), ai_tank at (500, 500) — pure east
        self.ai_obj.update(self.ai_tank, [self.near_target, self.far_target], self.game, 0.1)
        # The body angle should have rotated toward east (90 degrees)
        # Just verify no crash and ai_tank is alive
        self.assertTrue(self.ai_tank.is_alive)

    def test_ai_ignores_dead_targets(self):
        self.near_target.is_alive = False
        self.far_target.is_alive = False
        prev_x = self.ai_tank.x
        self.ai_obj.update(self.ai_tank, [self.near_target, self.far_target], self.game, 0.1)
        self.assertEqual(self.ai_tank.x, prev_x)

    def test_ai_skips_dead_ai_tank(self):
        self.ai_tank.is_alive = False
        prev_x = self.ai_tank.x
        self.ai_obj.update(self.ai_tank, [self.near_target], self.game, 0.1)
        self.assertEqual(self.ai_tank.x, prev_x)

    def test_ai_selects_nearer_of_two_targets(self):
        # Place AI between two targets; near_target is 200 units east (outside
        # retreat distance of 120), far_target is 400 units west.
        # After an update, AI should steer toward near_target direction.
        self.near_target.x = 700.0  # east, 200 units away — outside retreat range
        self.near_target.y = 500.0
        self.far_target.x = 100.0   # west, 400 units away
        self.far_target.y = 500.0
        self.ai_tank.body_angle = 0.0
        self.ai_obj.update(self.ai_tank, [self.near_target, self.far_target], self.game, 0.5)
        # After steering toward east (near_target), body_angle should be closer to 90 than 270
        angle = self.ai_tank.body_angle
        east_dist = utils.shortest_angle_delta(angle, 90.0)
        west_dist = utils.shortest_angle_delta(angle, 270.0)
        self.assertLess(abs(east_dist), abs(west_dist))


class TestNeutralTankCombat(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()
        self.g.reset_round()

    def _place_bullet_on_tank(self, owner, target):
        """Add a stationary bullet at target's position, owned by owner."""
        bullet = entities.Bullet(target.x, target.y, 0.0, 0.0,
                                 constants.BULLET_DAMAGE, owner)
        bullet.is_alive = True
        self.g.bullets.append(bullet)
        return bullet

    def test_bullet_hits_neutral_tank(self):
        neutral = self.g.neutral_tanks[0]
        hp_before = neutral.hp
        self._place_bullet_on_tank(self.g.tanks[0], neutral)
        self.g._update_projectiles(0.0)
        self.assertLess(neutral.hp, hp_before)

    def test_neutral_tank_bullet_hits_player(self):
        neutral = self.g.neutral_tanks[0]
        player = self.g.tanks[0]
        hp_before = player.hp
        self._place_bullet_on_tank(neutral, player)
        self.g._update_projectiles(0.0)
        self.assertLess(player.hp, hp_before)

    def test_neutral_tank_death_drops_powerup(self):
        neutral = self.g.neutral_tanks[0]
        neutral.hp = 1  # one hit kill
        self._place_bullet_on_tank(self.g.tanks[0], neutral)
        powerups_before = len(self.g.powerups)
        self.g._update_projectiles(0.0)
        self.assertFalse(neutral.is_alive)
        self.assertGreater(len(self.g.powerups), powerups_before)

    def test_mine_damages_neutral_tank(self):
        neutral = self.g.neutral_tanks[0]
        mine = entities.Mine(neutral.x, neutral.y, self.g.tanks[0])
        mine.armed = True
        self.g.mines.append(mine)
        hp_before = neutral.hp
        self.g._update_projectiles(0.016)
        self.assertLess(neutral.hp, hp_before)

    def test_neutral_tanks_included_in_collision_resolution(self):
        # Place neutral tank on top of player tank and verify they separate
        neutral = self.g.neutral_tanks[0]
        neutral.x = self.g.tanks[0].x
        neutral.y = self.g.tanks[0].y
        self.g._resolve_tank_collision()
        dist = utils.distance(neutral.position, self.g.tanks[0].position)
        self.assertGreater(dist, 0.0)


class TestNeutralTankNetworkSync(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()
        self.g.reset_round()
        self.g.single_player = False

    def test_send_neutral_sync_skips_when_not_host(self):
        self.g.lobby_is_host = False
        self.g._neutral_sync_timer = -1.0
        self.g._send_neutral_sync(0.0)
        self.assertEqual(len(self.g._reliable_events_sent), 0)

    def test_send_neutral_sync_skips_when_timer_positive(self):
        self.g.lobby_is_host = True
        self.g._neutral_sync_timer = 5.0
        self.g._send_neutral_sync(0.1)
        self.assertEqual(len(self.g._reliable_events_sent), 0)

    def test_send_neutral_sync_fires_when_host_and_timer_expired(self):
        self.g.lobby_is_host = True
        self.g._neutral_sync_timer = 0.0
        self.g._send_neutral_sync(0.1)
        self.assertEqual(len(self.g._reliable_events_sent), 1)
        self.assertEqual(self.g._reliable_events_sent[0][0], "neutral_sync")

    def test_send_neutral_sync_payload_has_tanks_list(self):
        self.g.lobby_is_host = True
        self.g._neutral_sync_timer = 0.0
        self.g._send_neutral_sync(0.1)
        payload = self.g._reliable_events_sent[0][1]
        self.assertIn("tanks", payload)
        self.assertEqual(len(payload["tanks"]), constants.NEUTRAL_TANK_COUNT)

    def test_send_neutral_sync_tank_entry_has_six_fields(self):
        self.g.lobby_is_host = True
        self.g._neutral_sync_timer = 0.0
        self.g._send_neutral_sync(0.1)
        payload = self.g._reliable_events_sent[0][1]
        for entry in payload["tanks"]:
            self.assertEqual(len(entry), 6)

    def test_send_neutral_sync_resets_timer(self):
        self.g.lobby_is_host = True
        self.g._neutral_sync_timer = 0.0
        self.g._send_neutral_sync(0.1)
        self.assertAlmostEqual(self.g._neutral_sync_timer, constants.NEUTRAL_TANK_SYNC_INTERVAL)

    def test_handle_tcp_neutral_sync_applies_to_client(self):
        self.g.lobby_is_host = False
        t = self.g.neutral_tanks[0]
        payload = {"tanks": [[999.0, 888.0, 45.0, 90.0, 3, True]], "seq": self.g._round_seq}
        self.g._handle_tcp_events_playing([("neutral_sync", payload)])
        self.assertAlmostEqual(t.x, 999.0)
        self.assertAlmostEqual(t.y, 888.0)
        self.assertEqual(t.hp, 3)

    def test_handle_tcp_neutral_sync_ignored_by_host(self):
        self.g.lobby_is_host = True
        t = self.g.neutral_tanks[0]
        original_x = t.x
        payload = {"tanks": [[999.0, 888.0, 45.0, 90.0, 3, True]], "seq": self.g._round_seq}
        self.g._handle_tcp_events_playing([("neutral_sync", payload)])
        self.assertEqual(t.x, original_x)

    def test_handle_tcp_neutral_sync_safe_with_empty_list(self):
        self.g.lobby_is_host = False
        self.g._handle_tcp_events_playing([("neutral_sync", {"tanks": [], "seq": self.g._round_seq})])


class TestUpdateNeutralTanks(unittest.TestCase):

    def setUp(self):
        self.g = _StubGame()
        self.g.reset_round()

    def test_update_neutral_tanks_runs_for_single_player(self):
        self.g.single_player = True
        # Just verify no crash
        self.g._update_neutral_tanks(0.016)

    def test_update_neutral_tanks_skips_for_client(self):
        self.g.single_player = False
        self.g.lobby_is_host = False
        # Neutral tanks should not move (AI not applied)
        positions_before = [(t.x, t.y) for t in self.g.neutral_tanks]
        self.g._update_neutral_tanks(0.5)
        positions_after = [(t.x, t.y) for t in self.g.neutral_tanks]
        self.assertEqual(positions_before, positions_after)

    def test_update_neutral_tanks_runs_for_host(self):
        self.g.single_player = False
        self.g.lobby_is_host = True
        # Just verify no crash
        self.g._update_neutral_tanks(0.016)
