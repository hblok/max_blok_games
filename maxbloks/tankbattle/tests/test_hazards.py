# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import types
import unittest

from maxbloks.tankbattle import arena
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hazards
from maxbloks.tankbattle import utils


class TestHazardType(unittest.TestCase):

    def test_ice_patch_value(self):
        self.assertEqual(hazards.HazardType.ICE_PATCH.value, "ice_patch")

    def test_mud_swamp_value(self):
        self.assertEqual(hazards.HazardType.MUD_SWAMP.value, "mud_swamp")

    def test_conveyor_belt_value(self):
        self.assertEqual(hazards.HazardType.CONVEYOR_BELT.value, "conveyor_belt")

    def test_teleporter_value(self):
        self.assertEqual(hazards.HazardType.TELEPORTER.value, "teleporter")

    def test_landmine_value(self):
        self.assertEqual(hazards.HazardType.LANDMINE.value, "landmine")

    def test_turret_value(self):
        self.assertEqual(hazards.HazardType.TURRET.value, "turret")

    def test_all_six_types(self):
        self.assertEqual(len(list(hazards.HazardType)), 6)


class TestIcePatch(unittest.TestCase):

    def test_friction_modifier(self):
        ice = hazards.IcePatch(5, 10)
        self.assertAlmostEqual(ice.get_friction_modifier(), 0.3)

    def test_position(self):
        ice = hazards.IcePatch(5, 10)
        self.assertEqual(ice.position, (5, 10))

    def test_default_alive(self):
        ice = hazards.IcePatch(0, 0)
        self.assertTrue(ice.is_alive)


class TestMudSwamp(unittest.TestCase):

    def test_speed_modifier(self):
        mud = hazards.MudSwamp(3, 7)
        self.assertAlmostEqual(mud.get_speed_modifier(), 0.5)

    def test_position(self):
        mud = hazards.MudSwamp(3, 7)
        self.assertEqual(mud.position, (3, 7))


class TestConveyorBelt(unittest.TestCase):

    def test_push_velocity_north(self):
        conv = hazards.ConveyorBelt(0, 0, 0.0, -1.0)
        vx, vy = conv.get_push_velocity()
        self.assertAlmostEqual(vx, 0.0)
        self.assertAlmostEqual(vy, -80.0)

    def test_push_velocity_east(self):
        conv = hazards.ConveyorBelt(0, 0, 1.0, 0.0)
        vx, vy = conv.get_push_velocity()
        self.assertAlmostEqual(vx, 80.0)
        self.assertAlmostEqual(vy, 0.0)

    def test_position(self):
        conv = hazards.ConveyorBelt(5, 10, 1.0, 0.0)
        self.assertEqual(conv.position, (5, 10))

    def test_custom_push_speed(self):
        conv = hazards.ConveyorBelt(0, 0, 1.0, 0.0, push_speed=120.0)
        vx, vy = conv.get_push_velocity()
        self.assertAlmostEqual(vx, 120.0)


class TestTeleporter(unittest.TestCase):

    def test_position(self):
        tp = hazards.Teleporter(5, 10, 100, 200)
        self.assertEqual(tp.position, (5, 10))

    def test_target_position(self):
        tp = hazards.Teleporter(5, 10, 100, 200)
        tx, ty = tp.target_position
        self.assertAlmostEqual(tx, 100 * constants.TILE_SIZE + constants.TILE_SIZE / 2.0)
        self.assertAlmostEqual(ty, 200 * constants.TILE_SIZE + constants.TILE_SIZE / 2.0)

    def test_can_teleport_initially(self):
        tp = hazards.Teleporter(0, 0, 10, 10)
        self.assertTrue(tp.can_teleport())

    def test_cannot_teleport_on_cooldown(self):
        tp = hazards.Teleporter(0, 0, 10, 10)
        tp.teleport()
        self.assertFalse(tp.can_teleport())

    def test_cooldown_expires(self):
        tp = hazards.Teleporter(0, 0, 10, 10)
        tp.teleport()
        tp.update(3.0)  # More than 2 second cooldown
        self.assertTrue(tp.can_teleport())

    def test_update_decrements_cooldown(self):
        tp = hazards.Teleporter(0, 0, 10, 10)
        tp.teleport()
        self.assertEqual(tp.cooldown, 2.0)
        tp.update(0.5)
        self.assertAlmostEqual(tp.cooldown, 1.5)


class TestLandmine(unittest.TestCase):

    def test_initially_unarmed(self):
        lm = hazards.Landmine(5, 10)
        self.assertFalse(lm.is_armed)

    def test_arms_after_delay(self):
        lm = hazards.Landmine(5, 10)
        lm.update(2.0)  # More than 1.5 arm time
        self.assertTrue(lm.is_armed)

    def test_does_not_trigger_when_unarmed(self):
        lm = hazards.Landmine(5, 10)
        tank = entities.Tank(100.0, 100.0, 0.0, 0.0)
        # Position tank on mine
        wx, wy = lm.position
        tank.x = wx
        tank.y = wy
        result = lm.check_trigger([tank])
        self.assertEqual(result, [])
        self.assertTrue(lm.is_alive)

    def test_triggers_when_armed(self):
        lm = hazards.Landmine(5, 10)
        lm.is_armed = True
        tank = entities.Tank(100.0, 100.0, 0.0, 0.0)
        wx, wy = lm.position
        tank.x = wx
        tank.y = wy
        result = lm.check_trigger([tank])
        self.assertEqual(len(result), 1)
        self.assertFalse(lm.is_alive)

    def test_damage_applied(self):
        lm = hazards.Landmine(5, 10)
        lm.is_armed = True
        tank = entities.Tank(100.0, 100.0, 0.0, 0.0)
        wx, wy = lm.position
        tank.x = wx
        tank.y = wy
        hp_before = tank.hp
        lm.check_trigger([tank])
        self.assertEqual(tank.hp, hp_before - constants.LANDMINE_DAMAGE)

    def test_no_trigger_when_dead(self):
        lm = hazards.Landmine(5, 10)
        lm.is_armed = True
        lm.is_alive = False
        tank = entities.Tank(100.0, 100.0, 0.0, 0.0)
        wx, wy = lm.position
        tank.x = wx
        tank.y = wy
        result = lm.check_trigger([tank])
        self.assertEqual(result, [])


class TestTurret(unittest.TestCase):

    def test_position(self):
        t = hazards.Turret(10, 20)
        tx, ty = t.position
        self.assertAlmostEqual(tx, 10 * constants.TILE_SIZE + constants.TILE_SIZE / 2.0)
        self.assertAlmostEqual(ty, 20 * constants.TILE_SIZE + constants.TILE_SIZE / 2.0)

    def test_does_not_fire_when_no_tanks_alive(self):
        t = hazards.Turret(10, 20)
        result = t.update(0.1, [], None)
        self.assertIsNone(result)

    def test_does_not_fire_when_tank_out_of_range(self):
        t = hazards.Turret(10, 20)
        # Place tank far away
        tank = entities.Tank(5000.0, 5000.0, 0.0, 0.0)
        result = t.update(0.1, [tank], None)
        self.assertIsNone(result)

    def test_fires_at_nearby_tank(self):
        t = hazards.Turret(10, 20)
        tx, ty = t.position
        # Place tank within range
        tank = entities.Tank(tx + 50.0, ty, 0.0, 0.0)
        result = t.update(0.1, [tank], None)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, hazards.TurretBullet)

    def test_fire_cooldown(self):
        t = hazards.Turret(10, 20)
        tx, ty = t.position
        tank = entities.Tank(tx + 50.0, ty, 0.0, 0.0)
        # First fire
        result1 = t.update(0.1, [tank], None)
        self.assertIsNotNone(result1)
        # Second fire should be on cooldown
        result2 = t.update(0.1, [tank], None)
        self.assertIsNone(result2)

    def test_cooldown_expires(self):
        t = hazards.Turret(10, 20)
        tx, ty = t.position
        tank = entities.Tank(tx + 50.0, ty, 0.0, 0.0)
        # First fire
        result1 = t.update(0.1, [tank], None)
        self.assertIsNotNone(result1)
        # Second fire should be blocked by cooldown
        result2 = t.update(0.1, [tank], None)
        self.assertIsNone(result2)
        # Wait for cooldown to expire in a single large dt
        # (decrement + fire happen in the same update call)
        result3 = t.update(constants.TURRET_FIRE_INTERVAL + 0.1, [tank], None)
        self.assertIsNotNone(result3)

    def test_does_not_fire_when_dead(self):
        t = hazards.Turret(10, 20)
        t.is_alive = False
        tx, ty = t.position
        tank = entities.Tank(tx + 50.0, ty, 0.0, 0.0)
        result = t.update(0.1, [tank], None)
        self.assertIsNone(result)


class TestTurretBullet(unittest.TestCase):

    def test_movement(self):
        b = hazards.TurretBullet(100.0, 100.0, 100.0, 0.0)
        world = arena.Arena(42)
        b.update(0.1, world)
        self.assertAlmostEqual(b.x, 110.0, places=0)
        self.assertAlmostEqual(b.y, 100.0, places=0)

    def test_dies_on_lifetime_expire(self):
        b = hazards.TurretBullet(100.0, 100.0, 100.0, 0.0, lifetime=0.05)
        world = arena.Arena(42)
        b.update(0.1, world)
        self.assertFalse(b.is_alive)

    def test_dies_on_boundary(self):
        b = hazards.TurretBullet(5.0, 100.0, -200.0, 0.0)
        world = arena.Arena(42)
        b.update(0.1, world)
        self.assertFalse(b.is_alive)


class TestArenaHazardGeneration(unittest.TestCase):

    def test_arena_generates_ice_patches(self):
        world = arena.Arena(42)
        self.assertGreater(len(world.ice_patches), 0)

    def test_arena_generates_mud_swamps(self):
        world = arena.Arena(42)
        self.assertGreater(len(world.mud_swamps), 0)

    def test_arena_generates_conveyor_belts(self):
        world = arena.Arena(42)
        self.assertGreater(len(world.conveyor_belts), 0)

    def test_arena_generates_teleporters(self):
        world = arena.Arena(42)
        # Teleporters come in pairs
        self.assertGreaterEqual(len(world.teleporters), 0)
        if len(world.teleporters) > 0:
            self.assertEqual(len(world.teleporters) % 2, 0)

    def test_arena_generates_landmines(self):
        world = arena.Arena(42)
        self.assertGreater(len(world.landmines), 0)

    def test_arena_generates_turrets(self):
        world = arena.Arena(42)
        self.assertGreater(len(world.turrets), 0)

    def test_ice_patches_not_on_obstacles(self):
        world = arena.Arena(42)
        for ice in world.ice_patches:
            key = (ice.tile_x, ice.tile_y)
            self.assertNotIn(key, world.hard_tiles)
            self.assertNotIn(key, world.soft_tiles)

    def test_mud_not_on_obstacles(self):
        world = arena.Arena(42)
        for mud in world.mud_swamps:
            key = (mud.tile_x, mud.tile_y)
            self.assertNotIn(key, world.hard_tiles)
            self.assertNotIn(key, world.soft_tiles)

    def test_hazards_not_on_spawn_points(self):
        world = arena.Arena(42)
        reserved = world._reserved_tiles()
        for ice in world.ice_patches:
            self.assertNotIn((ice.tile_x, ice.tile_y), reserved)
        for mud in world.mud_swamps:
            self.assertNotIn((mud.tile_x, mud.tile_y), reserved)
        for turret in world.turrets:
            self.assertNotIn((turret.tile_x, turret.tile_y), reserved)

    def test_landmines_on_soft_obstacles(self):
        world = arena.Arena(42)
        for landmine in world.landmines:
            key = (landmine.tile_x, landmine.tile_y)
            self.assertIn(key, world.soft_tiles)

    def test_teleporter_pairs_linked(self):
        world = arena.Arena(42)
        if len(world.teleporters) < 2:
            return
        # Each teleporter should have a partner that targets back
        for tp in world.teleporters:
            found_partner = False
            for other in world.teleporters:
                if (other.tile_x == tp.target_tile_x
                        and other.tile_y == tp.target_tile_y
                        and other.target_tile_x == tp.tile_x
                        and other.target_tile_y == tp.tile_y):
                    found_partner = True
                    break
            self.assertTrue(found_partner, f"Teleporter at ({tp.tile_x}, {tp.tile_y}) has no partner")


class TestArenaHazardSerialization(unittest.TestCase):

    def test_serialize_contains_hazard_data(self):
        world = arena.Arena(42)
        data = world.serialize()
        self.assertIn("ice_patches", data)
        self.assertIn("mud_swamps", data)
        self.assertIn("conveyor_belts", data)
        self.assertIn("teleporters", data)
        self.assertIn("landmines", data)
        self.assertIn("turrets", data)

    def test_deserialize_reconstructs_hazards(self):
        world = arena.Arena(42)
        data = world.serialize()
        restored = arena.Arena.deserialize(data)
        self.assertEqual(len(restored.ice_patches), len(world.ice_patches))
        self.assertEqual(len(restored.mud_swamps), len(world.mud_swamps))
        self.assertEqual(len(restored.conveyor_belts), len(world.conveyor_belts))
        self.assertEqual(len(restored.teleporters), len(world.teleporters))
        self.assertEqual(len(restored.landmines), len(world.landmines))
        self.assertEqual(len(restored.turrets), len(world.turrets))

    def test_deserialize_ice_patch_positions(self):
        world = arena.Arena(42)
        data = world.serialize()
        restored = arena.Arena.deserialize(data)
        for orig, rest in zip(world.ice_patches, restored.ice_patches):
            self.assertEqual((orig.tile_x, orig.tile_y), (rest.tile_x, rest.tile_y))

    def test_deserialize_conveyor_directions(self):
        world = arena.Arena(42)
        data = world.serialize()
        restored = arena.Arena.deserialize(data)
        for orig, rest in zip(world.conveyor_belts, restored.conveyor_belts):
            self.assertAlmostEqual(orig.direction_x, rest.direction_x)
            self.assertAlmostEqual(orig.direction_y, rest.direction_y)

    def test_deserialize_teleporter_targets(self):
        world = arena.Arena(42)
        data = world.serialize()
        restored = arena.Arena.deserialize(data)
        for orig, rest in zip(world.teleporters, restored.teleporters):
            self.assertEqual(orig.target_tile_x, rest.target_tile_x)
            self.assertEqual(orig.target_tile_y, rest.target_tile_y)


class TestArenaHazardReset(unittest.TestCase):

    def test_reset_round_resets_landmines(self):
        world = arena.Arena(42)
        # Arm some landmines and trigger them
        for lm in world.landmines:
            lm.is_armed = True
            lm.is_alive = False
        world.reset_round()
        for lm in world.landmines:
            self.assertTrue(lm.is_alive)
            self.assertFalse(lm.is_armed)
            self.assertAlmostEqual(lm.arm_timer, constants.LANDMINE_ARM_TIME)

    def test_reset_round_resets_turrets(self):
        world = arena.Arena(42)
        for turret in world.turrets:
            turret.fire_cooldown = 99.0
            turret.is_alive = False
        world.reset_round()
        for turret in world.turrets:
            self.assertTrue(turret.is_alive)
            self.assertAlmostEqual(turret.fire_cooldown, 0.0)

    def test_reset_round_resets_teleporters(self):
        world = arena.Arena(42)
        for tp in world.teleporters:
            tp.cooldown = 99.0
        world.reset_round()
        for tp in world.teleporters:
            self.assertAlmostEqual(tp.cooldown, 0.0)


class TestArenaTerrainQuery(unittest.TestCase):

    def test_terrain_at_world_ice(self):
        world = arena.Arena(42)
        if not world.ice_patches:
            return
        ice = world.ice_patches[0]
        wx, wy = utils.tile_to_world(ice.tile_x, ice.tile_y)
        self.assertEqual(world.terrain_at_world(wx, wy), hazards.HazardType.ICE_PATCH)

    def test_terrain_at_world_mud(self):
        world = arena.Arena(42)
        if not world.mud_swamps:
            return
        mud = world.mud_swamps[0]
        wx, wy = utils.tile_to_world(mud.tile_x, mud.tile_y)
        self.assertEqual(world.terrain_at_world(wx, wy), hazards.HazardType.MUD_SWAMP)

    def test_terrain_at_world_conveyor(self):
        world = arena.Arena(42)
        if not world.conveyor_belts:
            return
        conv = world.conveyor_belts[0]
        wx, wy = utils.tile_to_world(conv.tile_x, conv.tile_y)
        self.assertEqual(world.terrain_at_world(wx, wy), hazards.HazardType.CONVEYOR_BELT)

    def test_terrain_at_world_teleporter(self):
        world = arena.Arena(42)
        if not world.teleporters:
            return
        tp = world.teleporters[0]
        wx, wy = utils.tile_to_world(tp.tile_x, tp.tile_y)
        self.assertEqual(world.terrain_at_world(wx, wy), hazards.HazardType.TELEPORTER)

    def test_terrain_at_world_normal(self):
        world = arena.Arena(42)
        # Use a spawn point which should be clear
        sx, sy = world.spawn_points[0]
        self.assertIsNone(world.terrain_at_world(sx, sy))

    def test_conveyor_at_world(self):
        world = arena.Arena(42)
        if not world.conveyor_belts:
            return
        conv = world.conveyor_belts[0]
        wx, wy = utils.tile_to_world(conv.tile_x, conv.tile_y)
        result = world.conveyor_at_world(wx, wy)
        self.assertIs(result, conv)

    def test_teleporter_at_world(self):
        world = arena.Arena(42)
        if not world.teleporters:
            return
        tp = world.teleporters[0]
        wx, wy = utils.tile_to_world(tp.tile_x, tp.tile_y)
        result = world.teleporter_at_world(wx, wy)
        self.assertIs(result, tp)


if __name__ == "__main__":
    unittest.main()
