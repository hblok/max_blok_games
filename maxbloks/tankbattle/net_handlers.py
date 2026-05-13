# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Network send/receive handlers for TankBattleGame."""

import logging
import random
import time

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import network
from maxbloks.tankbattle import utils

logger = logging.getLogger(__name__)


class NetworkHandlersMixin:
    """UDP/TCP send-receive, dead reckoning, and HP sync methods."""

    def _send_network_update(self):
        """Send local player state to peer via UDP at 20 Hz."""
        if self.single_player:
            return
        now = time.monotonic()
        if not self.net.should_send_update(now):
            return
        packet = network.PlayerUpdatePacket(
            self.local_player_index + 1,
            self.local_tank.x,
            self.local_tank.y,
            self.local_tank.body_angle,
            self.local_tank.turret_angle,
            self.local_tank.hp,
            self.local_tank.active_weapon.value,
            self.local_tank.weapon_timer,
            fired=self._net_fired,
            fire_angle=self._net_fire_angle,
            mine_dropped=self._net_mine_dropped,
            mine_x=self._net_mine_x,
            mine_y=self._net_mine_y,
            powerup_collected_id=self._net_powerup_collected_id,
        )
        self.net.send_player_update(packet)
        # Clear action tracking flags after sending
        self._net_fired = False
        self._net_fire_angle = 0.0
        self._net_mine_dropped = False
        self._net_mine_x = 0.0
        self._net_mine_y = 0.0
        self._net_powerup_collected_id = -1

    def _receive_network_updates(self):
        """Receive and apply remote player updates from UDP packets.

        Uses the unified ``receive_udp()`` which handles player updates,
        pings, and pongs in a single socket read pass.
        """
        if self.single_player:
            return
        updates = self.net.receive_udp()
        for packet in updates:
            # Find the remote tank (player_id is 1-indexed)
            remote_idx = packet.player_id - 1
            if 0 <= remote_idx < len(self.tanks):
                remote_tank = self.tanks[remote_idx]
                remote_tank.x = packet.x
                remote_tank.y = packet.y
                remote_tank.body_angle = packet.body_angle
                remote_tank.turret_angle = packet.turret_angle
                remote_tank.hp = packet.hp
                remote_tank.active_weapon = entities.WeaponType(packet.weapon)
                remote_tank.weapon_timer = packet.weapon_timer
                if packet.fired:
                    self._add_bullet(
                        remote_tank,
                        packet.fire_angle,
                        constants.BULLET_SPEED,
                        constants.BULLET_DAMAGE,
                        entities.WeaponType.PRIMARY,
                    )
                if packet.mine_dropped:
                    self.mines.append(entities.Mine(packet.mine_x, packet.mine_y, remote_tank))
                if packet.powerup_collected_id >= 0:
                    for powerup in self.powerups:
                        if powerup.identifier == packet.powerup_collected_id:
                            powerup.is_alive = False
                            break
                logger.debug(
                    "Applied remote update: player=%d, pos=(%.1f,%.1f), hp=%d",
                    packet.player_id, packet.x, packet.y, packet.hp,
                )

    def _apply_dead_reckoning(self):
        """Smooth remote tank position using dead-reckoned prediction."""
        if self.net.dead_reckoner.target_packet is None:
            return
        rx, ry = self.net.dead_reckoner.predicted_position()
        rx = utils.clamp(rx, constants.TANK_HITBOX_RADIUS, constants.WORLD_WIDTH - constants.TANK_HITBOX_RADIUS)
        ry = utils.clamp(ry, constants.TANK_HITBOX_RADIUS, constants.WORLD_HEIGHT - constants.TANK_HITBOX_RADIUS)
        self.remote_tank.x = rx
        self.remote_tank.y = ry

    def _send_neutral_sync(self, dt):
        """Host sends authoritative neutral tank positions to client every sync interval."""
        if not self.lobby_is_host:
            return
        self._neutral_sync_timer -= dt
        if self._neutral_sync_timer > 0.0:
            return
        self._neutral_sync_timer = constants.NEUTRAL_TANK_SYNC_INTERVAL
        tanks_data = [
            [t.x, t.y, t.body_angle, t.turret_angle, t.hp, t.is_alive]
            for t in self.neutral_tanks
        ]
        self.net.send_reliable_event("neutral_sync", {"tanks": tanks_data})

    def _send_hp_sync(self, dt):
        """Periodically send authoritative HP snapshot to peer (host only)."""
        if not self.lobby_is_host:
            return
        self._hp_sync_timer -= dt
        if self._hp_sync_timer > 0.0:
            return
        self._hp_sync_timer = constants.HP_SYNC_INTERVAL
        self.net.send_reliable_event("hp_sync", {
            "hp": [self.tanks[0].hp, self.tanks[1].hp],
        })
        logger.debug("Sent HP sync: [%d, %d]", self.tanks[0].hp, self.tanks[1].hp)

    def _handle_tcp_events_playing(self, events):
        """Process reliable TCP events received during PLAYING state."""
        for event_name, payload in events:
            if event_name == "neutral_sync" and not self.lobby_is_host:
                tanks_data = payload.get("tanks", [])
                for i, data in enumerate(tanks_data):
                    if i < len(self.neutral_tanks) and len(data) >= 6:
                        t = self.neutral_tanks[i]
                        t.x = float(data[0])
                        t.y = float(data[1])
                        t.body_angle = float(data[2])
                        t.turret_angle = float(data[3])
                        t.hp = int(data[4])
                        t.is_alive = bool(data[5])
            if event_name == "hp_sync" and not self.lobby_is_host:
                hp_values = payload.get("hp", [])
                if len(hp_values) != len(self.tanks):
                    continue
                for i, tank in enumerate(self.tanks):
                    auth_hp = int(hp_values[i])
                    if i == self.local_player_index:
                        # For our own tank: only apply lower HP to avoid undoing recent damage
                        if auth_hp < tank.hp:
                            logger.info(
                                "HP reconciliation (local tank %d): %d -> %d",
                                i + 1, tank.hp, auth_hp,
                            )
                            tank.hp = max(0, auth_hp)
                    else:
                        # For remote tank: trust host's authoritative value
                        if tank.hp != auth_hp:
                            logger.info(
                                "HP reconciliation (remote tank %d): %d -> %d",
                                i + 1, tank.hp, auth_hp,
                            )
                            tank.hp = max(0, auth_hp)

    def _handle_tcp_events_match_over(self, events):
        """Process reliable TCP events received during MATCH_OVER state."""
        for event_name, payload in events:
            if event_name == "rematch":
                seed = payload.get("seed")
                if seed is not None:
                    self.match_seed = seed
                    self.arena = arena.Arena(self.match_seed)
                    logger.info("Received rematch event (seed=%s)", seed)
                else:
                    logger.info("Received rematch request — starting rematch")
                    if self.lobby_is_host:
                        self.match_seed = random.randrange(constants.WORLD_WIDTH * constants.WORLD_HEIGHT)
                        self.arena = arena.Arena(self.match_seed)
                        self.net.send_reliable_event("rematch", {"seed": self.match_seed})
                self._do_rematch()
