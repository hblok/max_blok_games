# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Main renderer for TankBattle: world, menus, and state overlays."""

import math
import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import utils
from maxbloks.tankbattle.rendering import particle_system as _particle_system
from maxbloks.tankbattle.rendering import sprite_cache as _sprite_cache


class Renderer:
    """Draw world, tanks, menus, and state overlays with polished graphics."""

    # Lobby colour palette (matches networktest style)
    _LOB_COLOR_BG = (15, 15, 25)
    _LOB_COLOR_PANEL = (30, 40, 45)
    _LOB_COLOR_TEXT = (220, 220, 220)
    _LOB_COLOR_DIM = (120, 120, 140)
    _LOB_COLOR_HIGHLIGHT = (40, 100, 50)
    _LOB_COLOR_SUCCESS = (80, 200, 120)
    _LOB_COLOR_WARNING = (200, 180, 80)
    _LOB_COLOR_BORDER = (40, 100, 50)

    def __init__(self, pygame_module, screen):
        self.pygame = pygame_module
        self.screen = screen
        self.font_menu = pygame_module.font.Font(None, constants.MENU_FONT_SIZE)
        self.font_big = pygame_module.font.Font(None, constants.BIG_FONT_SIZE)
        self.font_small = pygame_module.font.Font(None, constants.SMALL_FONT_SIZE)
        self.font_lobby = pygame_module.font.Font(None, constants.HUD_FONT_SIZE)
        self.sprite_cache = _sprite_cache.SpriteCache(pygame_module)
        self.particles = _particle_system.ParticleSystem(pygame_module)
        self.terrain_surface = pygame_module.Surface(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        self.terrain_surface.fill(constants.COLOR_BG)
        self._build_terrain_pattern()
        self.flash_timer = 0.0
        self.destroy_timers = {}
        self._powerup_frame_index = 0.0

    def _build_terrain_pattern(self):
        tile = self.sprite_cache.get("terrain_tile")
        if tile:
            for y in range(0, constants.SCREEN_HEIGHT, constants.TILE_SIZE):
                for x in range(0, constants.SCREEN_WIDTH, constants.TILE_SIZE):
                    self.terrain_surface.blit(tile, (x, y))

    def draw_world(self, game):
        self.screen.blit(self.terrain_surface, (0, 0))
        camera = game.arena.clamp_camera(game.local_tank.position)
        self._draw_obstacles(game, camera)
        self._draw_powerups(game, camera)
        self._draw_mines(game, camera)
        self._draw_bullets(game, camera)
        self._draw_tanks(game, camera)
        self.particles.draw(self.screen, camera)

    def _draw_obstacles(self, game, camera):
        for obstacle in game.arena.obstacles:
            if obstacle.is_destroyed:
                continue
            wx = obstacle.tile_x * constants.TILE_SIZE
            wy = obstacle.tile_y * constants.TILE_SIZE
            sx, sy = game.arena.world_to_screen((wx, wy), camera)
            if sx + constants.TILE_SIZE < 0 or sx > constants.SCREEN_WIDTH:
                continue
            if sy + constants.TILE_SIZE < 0 or sy > constants.SCREEN_HEIGHT:
                continue
            if obstacle.type == entities.ObstacleType.HARD_ROCK:
                tile = self.sprite_cache.get("hard_rock_tile")
            else:
                tile = self.sprite_cache.get("soft_obstacle_tile")
            if tile:
                self.screen.blit(tile, (int(sx), int(sy)))
            else:
                color = constants.COLOR_HARD
                if obstacle.type == entities.ObstacleType.SOFT:
                    color = constants.COLOR_SOFT
                self.pygame.draw.rect(self.screen, color,
                                      (int(sx), int(sy), constants.TILE_SIZE, constants.TILE_SIZE))

    def _draw_powerups(self, game, camera):
        """Draw powerups using pre-computed pulse frames."""
        for powerup in game.powerups:
            sx, sy = game.arena.world_to_screen(powerup.position, camera)
            isx, isy = int(sx), int(sy)
            if isx < -20 or isx > constants.SCREEN_WIDTH + 20:
                continue
            if isy < -20 or isy > constants.SCREEN_HEIGHT + 20:
                continue
            # Look up pre-computed frames
            frames_key = f"powerup_frames_{powerup.type.value}"
            frames = self.sprite_cache.get(frames_key)
            if frames:
                # Map pulse_timer to a frame index
                phase_index = int((powerup.pulse_timer * 2.0 / (2.0 * math.pi)) * len(frames)) % len(frames)
                scaled, glow_surf = frames[phase_index]
                self.screen.blit(glow_surf,
                                 (isx - glow_surf.get_width() // 2,
                                  isy - glow_surf.get_height() // 2))
                self.screen.blit(scaled,
                                 (isx - scaled.get_width() // 2,
                                  isy - scaled.get_height() // 2))
            else:
                # Fallback to base surface without pulse
                key = f"powerup_{powerup.type.value}"
                surface = self.sprite_cache.get(key)
                if surface:
                    self.screen.blit(surface,
                                     (isx - surface.get_width() // 2,
                                      isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_YELLOW, (isx, isy), 8)

    def _draw_mines(self, game, camera):
        for mine in game.mines:
            sx, sy = game.arena.world_to_screen(mine.position, camera)
            isx, isy = int(sx), int(sy)
            key = "mine_armed" if mine.armed else "mine_unarmed"
            surface = self.sprite_cache.get(key)
            if surface:
                blink = mine.armed and (int(mine.arm_timer * 10) % 2 == 0 if mine.arm_timer > 0 else True)
                if mine.armed and blink:
                    glow = self.pygame.Surface((28, 28), self.pygame.SRCALPHA)
                    self.pygame.draw.circle(glow, (255, 0, 0, 50), (14, 14), 12)
                    self.screen.blit(glow, (isx - 14, isy - 14))
                self.screen.blit(surface, (isx - surface.get_width() // 2,
                                           isy - surface.get_height() // 2))
            else:
                color = constants.COLOR_ORANGE if mine.armed else constants.COLOR_GREY
                self.pygame.draw.circle(self.screen, color, (isx, isy), 6)

    def _draw_bullets(self, game, camera):
        ricochet_glow = self.sprite_cache.get("ricochet_glow")
        for bullet in game.bullets:
            sx, sy = game.arena.world_to_screen(bullet.position, camera)
            isx, isy = int(sx), int(sy)
            if isx < -10 or isx > constants.SCREEN_WIDTH + 10:
                continue
            if isy < -10 or isy > constants.SCREEN_HEIGHT + 10:
                continue
            if bullet.weapon_type == entities.WeaponType.ROCKET:
                surface = self.sprite_cache.get("rocket")
                if surface:
                    self.screen.blit(surface, (isx - surface.get_width() // 2,
                                               isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_ORANGE, (isx, isy), 4)
            elif bullet.weapon_type == entities.WeaponType.RICOCHET:
                # Use pre-cached glow surface
                if ricochet_glow:
                    self.screen.blit(ricochet_glow, (isx - 8, isy - 8))
                else:
                    self.pygame.draw.circle(self.screen, (220, 150, 255), (isx, isy), 3)
            else:
                surface = self.sprite_cache.get("bullet")
                if surface:
                    self.screen.blit(surface, (isx - surface.get_width() // 2,
                                               isy - surface.get_height() // 2))
                else:
                    self.pygame.draw.circle(self.screen, constants.COLOR_WHITE, (isx, isy), 3)

    def _draw_tanks(self, game, camera):
        for idx, tank in enumerate(game.tanks):
            if not tank.is_alive:
                self._draw_destroyed_tank(game, tank, camera)
                continue
            color_key = "green" if idx == game.local_player_index else "red"
            self._draw_alive_tank(game, tank, camera, color_key)

    def _draw_alive_tank(self, game, tank, camera, color_key):
        sx, sy = game.arena.world_to_screen(tank.position, camera)
        isx, isy = int(sx), int(sy)
        cached = self.sprite_cache.get(f"tank_{color_key}")
        total_size = self.sprite_cache.get(f"tank_{color_key}_size")
        if cached is None or total_size is None:
            self._draw_tank_fallback(game, tank, camera,
                                     constants.COLOR_GREEN if color_key == "green" else constants.COLOR_RED)
            return
        # Draw body (pre-cached surface, rotated)
        body_angle = tank.body_angle
        body_rotated = self.pygame.transform.rotate(cached, -body_angle)
        body_rect = body_rotated.get_rect(center=(isx, isy))
        self.screen.blit(body_rotated, body_rect)
        # Draw turret (pre-cached surface, rotated)
        turret_surface = self.sprite_cache.get(f"turret_{color_key}")
        if turret_surface:
            turret_angle = tank.turret_angle
            turret_rotated = self.pygame.transform.rotate(turret_surface, -turret_angle)
            turret_rect = turret_rotated.get_rect(center=(isx, isy))
            self.screen.blit(turret_rotated, turret_rect)
        # Draw hit flash (pre-cached surface with alpha modulation)
        if tank.hit_flash_timer > 0:
            flash_surface = self.sprite_cache.get("hit_flash")
            flash_radius = self.sprite_cache.get("hit_flash_radius")
            if flash_surface and flash_radius:
                flash_intensity = tank.hit_flash_timer / constants.TANK_HIT_FLASH_TIME
                # Scale alpha by modulating a copy — this is cheaper than
                # creating a new surface from scratch every frame.
                alpha = int(120 * flash_intensity)
                temp = flash_surface.copy()
                temp.set_alpha(alpha)
                self.screen.blit(temp,
                                 (isx - flash_radius, isy - flash_radius))

    def _draw_tank_fallback(self, game, tank, camera, color):
        screen_pos = game.arena.world_to_screen(tank.position, camera)
        draw_color = constants.COLOR_WHITE if tank.hit_flash_timer > 0.0 else color
        center = (int(screen_pos[0]), int(screen_pos[1]))
        self.pygame.draw.circle(self.screen, draw_color, center,
                                int(constants.TANK_HITBOX_RADIUS))
        dx_value, dy_value = utils.angle_to_vector(tank.turret_angle)
        end = (
            int(screen_pos[0] + dx_value * constants.TANK_BODY_HEIGHT),
            int(screen_pos[1] + dy_value * constants.TANK_BODY_HEIGHT),
        )
        self.pygame.draw.line(self.screen, constants.COLOR_BLACK, center, end,
                              constants.TANK_TURRET_WIDTH)

    def _draw_destroyed_tank(self, game, tank, camera):
        sx, sy = game.arena.world_to_screen(tank.position, camera)
        isx, isy = int(sx), int(sy)
        hull = self.sprite_cache.get("destroyed_hull")
        if hull:
            self.screen.blit(hull, (isx - 16, isy - 16))
        else:
            self.pygame.draw.circle(self.screen, (60, 60, 60), (isx, isy), 12)
        if random.random() < 0.1:
            self.particles.emit_smoke(tank.x, tank.y, 1)

    def register_destroy(self, tank):
        """Register tank destruction. Returns True on the first call, False if already registered."""
        key = id(tank)
        if key not in self.destroy_timers:
            self.destroy_timers[key] = constants.TANK_DESTROY_ANIMATION_TIME
            self.particles.emit_explosion(tank.x, tank.y, constants.COLOR_ORANGE,
                                          count=20, speed=120.0, lifetime=0.8)
            self.particles.emit_explosion(tank.x, tank.y, (255, 255, 200),
                                          count=8, speed=60.0, lifetime=0.4)
            return True
        return False

    def register_hit(self, bullet):
        self.particles.emit_explosion(bullet.x, bullet.y, (255, 255, 150),
                                      count=5, speed=40.0, lifetime=0.2)

    def register_mine_explosion(self, mine):
        self.particles.emit_explosion(mine.x, mine.y, constants.COLOR_ORANGE,
                                      count=15, speed=100.0, lifetime=0.6)
        self.particles.emit_explosion(mine.x, mine.y, (100, 100, 100),
                                      count=8, speed=50.0, lifetime=0.8)

    def register_muzzle_flash(self, tank):
        dx, dy = utils.angle_to_vector(tank.turret_angle)
        x = tank.x + dx * constants.TANK_BODY_HEIGHT
        y = tank.y + dy * constants.TANK_BODY_HEIGHT
        self.particles.emit_muzzle_flash(x, y, tank.turret_angle)

    def update(self, dt):
        self.particles.update(dt)
        expired = []
        for key, timer in self.destroy_timers.items():
            self.destroy_timers[key] -= dt
            if self.destroy_timers[key] <= 0:
                expired.append(key)
        for key in expired:
            del self.destroy_timers[key]

    # ------------------------------------------------------------------
    # Menu drawing
    # ------------------------------------------------------------------

    def draw_menu(self, menu_index):
        self.screen.fill((15, 15, 25))
        border_size = 4
        border_color = (40, 100, 50)
        self.pygame.draw.rect(self.screen, border_color,
                              (0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), border_size)
        title = self.font_big.render("TANK BATTLE", True, constants.COLOR_GREEN)
        title_shadow = self.font_big.render("TANK BATTLE", True, (20, 80, 30))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title, title_rect)
        separator_y = 155
        self.pygame.draw.line(self.screen, (60, 130, 70),
                              (constants.SCREEN_WIDTH // 4, separator_y),
                              (3 * constants.SCREEN_WIDTH // 4, separator_y), 2)
        for index, item in enumerate(constants.MENU_ITEMS):
            y_pos = 210 + index * 48
            if index == menu_index:
                indicator_x = constants.SCREEN_WIDTH // 2 - 90
                self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                         [(indicator_x, y_pos - 6),
                                          (indicator_x + 10, y_pos),
                                          (indicator_x, y_pos + 6)])
                self.pygame.draw.rect(self.screen, (40, 60, 45),
                                      (constants.SCREEN_WIDTH // 2 - 100, y_pos - 16, 200, 36),
                                      border_radius=6)
                self.pygame.draw.rect(self.screen, constants.COLOR_GREEN,
                                      (constants.SCREEN_WIDTH // 2 - 100, y_pos - 16, 200, 36),
                                      2, border_radius=6)
                color = constants.COLOR_YELLOW
            else:
                color = constants.COLOR_LIGHT_GREY
            surface = self.font_menu.render(item, True, color)
            self.screen.blit(surface, surface.get_rect(center=(constants.SCREEN_WIDTH // 2, y_pos)))
        controls_text = self.font_small.render("Arrows/WASD: Move  |  Space: Fire  |  Ctrl: Mine  |  IJKL: Turret",
                                                True, constants.COLOR_GREY)
        self.screen.blit(controls_text,
                         controls_text.get_rect(center=(constants.SCREEN_WIDTH // 2,
                                                        constants.SCREEN_HEIGHT - 20)))

    # ------------------------------------------------------------------
    # Lobby drawing — enhanced with network info, symmetric visibility,
    # and bidirectional handshake indicators
    # ------------------------------------------------------------------

    def draw_lobby(self, game):
        """Draw the enhanced lobby screen with network information."""
        sw = constants.SCREEN_WIDTH
        sh = constants.SCREEN_HEIGHT
        margin = 16
        row_h = 28

        # Background
        self.screen.fill(self._LOB_COLOR_BG)
        self.pygame.draw.rect(self.screen, self._LOB_COLOR_BORDER,
                              (0, 0, sw, sh), 4)

        y = margin

        # Title
        role_label = "HOST LOBBY" if game.lobby_is_host else "JOIN LOBBY"
        title_surf = self.font_big.render(role_label, True, constants.COLOR_GREEN)
        title_shadow = self.font_big.render(role_label, True, (20, 80, 30))
        title_rect = title_surf.get_rect(center=(sw // 2, y + 22))
        self.screen.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title_surf, title_rect)
        y += 58

        # Separator
        self.pygame.draw.line(self.screen, self._LOB_COLOR_HIGHLIGHT,
                              (margin, y), (sw - margin, y), 2)
        y += 10

        # Network information section
        ip_text = f"My IP: {game.lobby_local_ip}"
        ip_surf = self.font_lobby.render(ip_text, True, self._LOB_COLOR_SUCCESS)
        self.screen.blit(ip_surf, (margin + 8, y))
        y += row_h

        if game.lobby_wifi_ssid:
            wifi_text = f"WiFi: {game.lobby_wifi_ssid}"
            wifi_surf = self.font_lobby.render(wifi_text, True, self._LOB_COLOR_SUCCESS)
            self.screen.blit(wifi_surf, (margin + 8, y))
        else:
            wifi_text = "WiFi: (not detected)"
            wifi_surf = self.font_lobby.render(wifi_text, True, self._LOB_COLOR_DIM)
            self.screen.blit(wifi_surf, (margin + 8, y))
        y += row_h

        if game.lobby_is_host:
            port_text = f"Listening on port: {constants.HOST_PORT}"
            port_surf = self.font_lobby.render(port_text, True, self._LOB_COLOR_TEXT)
            self.screen.blit(port_surf, (margin + 8, y))
        y += row_h + 4

        # Separator
        self.pygame.draw.line(self.screen, self._LOB_COLOR_HIGHLIGHT,
                              (margin, y), (sw - margin, y), 1)
        y += 8

        # Discovered clients / hosts section
        header_label = "Discovered Clients:" if game.lobby_is_host else "Available Hosts:"
        header_surf = self.font_lobby.render(header_label, True, self._LOB_COLOR_TEXT)
        self.screen.blit(header_surf, (margin + 8, y))
        y += row_h

        discovered = game.lobby_discovered_clients
        connected = game.lobby_connected_clients
        handshake_confirmed = game.lobby_handshake_confirmed

        # Filter peers based on role for display
        if game.lobby_is_host:
            display_peers = discovered
        else:
            display_peers = [h for h in discovered if h.get("hosting")]

        if not display_peers:
            searching_text = "Searching for devices..." if game.lobby_is_host else "Searching for hosts..."
            search_surf = self.font_small.render(searching_text, True, self._LOB_COLOR_DIM)
            self.screen.blit(search_surf, (margin + 24, y))
            y += row_h
        else:
            for peer_idx, host_info in enumerate(display_peers):
                ip = host_info.get("address", "???")
                is_connected = ip in connected
                is_handshake = handshake_confirmed.get(ip, False)

                dot_x = margin + 24
                dot_y_c = y + row_h // 2
                if is_handshake:
                    dot_color = self._LOB_COLOR_SUCCESS
                    self.pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y_c), 5)
                    self.pygame.draw.line(self.screen, constants.COLOR_BLACK,
                                          (dot_x - 2, dot_y_c), (dot_x - 1, dot_y_c + 2), 2)
                    self.pygame.draw.line(self.screen, constants.COLOR_BLACK,
                                          (dot_x - 1, dot_y_c + 2), (dot_x + 3, dot_y_c - 3), 2)
                elif is_connected:
                    dot_color = self._LOB_COLOR_WARNING
                    self.pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y_c), 5)
                else:
                    dot_color = self._LOB_COLOR_DIM
                    self.pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y_c), 5)

                ip_surf = self.font_small.render(ip, True, self._LOB_COLOR_TEXT)
                self.screen.blit(ip_surf, (margin + 40, y))

                if is_handshake:
                    status = "Connected ✓"
                    status_color = self._LOB_COLOR_SUCCESS
                elif is_connected:
                    status = "Handshaking..."
                    status_color = self._LOB_COLOR_WARNING
                else:
                    status = "available"
                    status_color = self._LOB_COLOR_DIM
                status_surf = self.font_small.render(status, True, status_color)
                self.screen.blit(status_surf, (sw - margin - status_surf.get_width() - 8, y))

                if not game.lobby_is_host and peer_idx == game.lobby_index:
                    highlight_rect = (margin + 4, y - 2, sw - 2 * margin - 8, row_h)
                    self.pygame.draw.rect(self.screen, (40, 80, 50), highlight_rect, border_radius=3)
                    self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, highlight_rect, 2, border_radius=3)
                    arrow_x = margin + 8
                    arrow_y_c = y + row_h // 2
                    self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                             [(arrow_x, arrow_y_c - 4),
                                              (arrow_x + 6, arrow_y_c),
                                              (arrow_x, arrow_y_c + 4)])

                y += row_h

        # Separator
        y += 4
        self.pygame.draw.line(self.screen, self._LOB_COLOR_HIGHLIGHT,
                              (margin, y), (sw - margin, y), 1)
        y += 10

        # Lobby action menu
        if game.lobby_is_host:
            for idx, item in enumerate(constants.LOBBY_ITEMS):
                item_y = y + idx * 38
                if idx == game.lobby_index:
                    highlight_rect = (margin + 4, item_y - 6, sw - 2 * margin - 8, 32)
                    self.pygame.draw.rect(self.screen, (40, 60, 45), highlight_rect, border_radius=5)
                    self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, highlight_rect, 2, border_radius=5)
                    arrow_x = margin + 12
                    self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                             [(arrow_x, item_y - 4),
                                              (arrow_x + 8, item_y + 8),
                                              (arrow_x, item_y + 20)])
                    color = constants.COLOR_YELLOW
                else:
                    color = self._LOB_COLOR_DIM
                item_surf = self.font_lobby.render(item, True, color)
                self.screen.blit(item_surf, item_surf.get_rect(center=(sw // 2, item_y + 10)))
        else:
            hosts = [h for h in discovered if h.get("hosting")]
            num_hosts = len(hosts)
            for idx, item in enumerate(constants.LOBBY_ITEMS):
                item_index = num_hosts + idx
                item_y = y + idx * 38
                if item_index == game.lobby_index:
                    highlight_rect = (margin + 4, item_y - 6, sw - 2 * margin - 8, 32)
                    self.pygame.draw.rect(self.screen, (40, 60, 45), highlight_rect, border_radius=5)
                    self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, highlight_rect, 2, border_radius=5)
                    arrow_x = margin + 12
                    self.pygame.draw.polygon(self.screen, constants.COLOR_YELLOW,
                                             [(arrow_x, item_y - 4),
                                              (arrow_x + 8, item_y + 8),
                                              (arrow_x, item_y + 20)])
                    color = constants.COLOR_YELLOW
                else:
                    color = self._LOB_COLOR_DIM
                item_surf = self.font_lobby.render(item, True, color)
                self.screen.blit(item_surf, item_surf.get_rect(center=(sw // 2, item_y + 10)))

        # Bottom instructions
        if game.lobby_is_host:
            instructions = "D-pad/Arrows: Navigate  |  A/Enter: Select  |  B/ESC: Back"
        else:
            instructions = "D-pad: Select Host  |  A/Enter: Join  |  B/ESC: Back"
        inst_surf = self.font_small.render(instructions, True, self._LOB_COLOR_DIM)
        self.screen.blit(inst_surf, inst_surf.get_rect(center=(sw // 2, sh - 16)))

    # ------------------------------------------------------------------
    # Other screen drawing
    # ------------------------------------------------------------------

    def draw_center_text(self, message, color=constants.COLOR_WHITE):
        self.screen.fill((15, 15, 25))
        self.pygame.draw.rect(self.screen, (40, 100, 50),
                              (0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), 4)
        text = self.font_menu.render(message, True, color)
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        bg_rect = text_rect.inflate(40, 20)
        self.pygame.draw.rect(self.screen, (20, 30, 25), bg_rect, border_radius=8)
        self.pygame.draw.rect(self.screen, constants.COLOR_GREEN, bg_rect, 2, border_radius=8)
        self.screen.blit(text, text_rect)

    def draw_countdown(self, game):
        self.draw_world(game)
        overlay = self.pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                       self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))
        value = max(0, int(game.state_timer) + 1)
        label = "GO!" if value == 0 else str(value)
        text = self.font_big.render(label, True, constants.COLOR_YELLOW)
        shadow = self.font_big.render(label, True, (80, 80, 0))
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        self.screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        self.screen.blit(text, text_rect)

    def draw_paused(self, game):
        game.draw_playing()
        overlay = self.pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                       self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        text = self.font_menu.render("PAUSED", True, constants.COLOR_YELLOW)
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 - 10))
        bg_rect = text_rect.inflate(60, 30)
        self.pygame.draw.rect(self.screen, (20, 30, 25), bg_rect, border_radius=8)
        self.pygame.draw.rect(self.screen, constants.COLOR_YELLOW, bg_rect, 2, border_radius=8)
        self.screen.blit(text, text_rect)
        hint = self.font_small.render("Press ESC or ENTER to resume", True, constants.COLOR_LIGHT_GREY)
        self.screen.blit(hint, hint.get_rect(center=(constants.SCREEN_WIDTH // 2,
                                                       constants.SCREEN_HEIGHT // 2 + 25)))

    def draw_round_over(self, game):
        import time as _time
        self.draw_world(game)
        overlay = self.pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                       self.pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        text = self.font_menu.render("ROUND OVER", True, constants.COLOR_YELLOW)
        shadow = self.font_menu.render("ROUND OVER", True, (80, 80, 0))
        text_rect = text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
        self.screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        self.screen.blit(text, text_rect)
        # Countdown hint (single-player only; multiplayer advances on timer)
        if game.single_player:
            grace_remaining = constants.ROUND_END_INPUT_GRACE - (
                _time.monotonic() - game._state_entry_time)
            if grace_remaining > 0:
                hint_color = constants.COLOR_GREY
                hint_text = f"Please wait…"
            else:
                hint_color = constants.COLOR_LIGHT_GREY
                hint_text = "Press [Start] to continue"
            hint = self.font_small.render(hint_text, True, hint_color)
            self.screen.blit(hint, hint.get_rect(
                center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 + 50)))
        else:
            secs_left = max(0, int(game.state_timer) + 1)
            hint = self.font_small.render(
                f"Next round in {secs_left}…", True, constants.COLOR_GREY)
            self.screen.blit(hint, hint.get_rect(
                center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 + 50)))

    def draw_match_over(self, game):
        import time as _time
        wins = game.round_wins
        self.screen.fill((15, 15, 25))
        self.pygame.draw.rect(self.screen, (40, 100, 50),
                              (0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), 4)
        winner = 1 if wins[0] > wins[1] else 2
        winner_color = constants.COLOR_GREEN if winner == 1 else constants.COLOR_RED
        title = self.font_big.render("VICTORY!", True, winner_color)
        title_shadow = self.font_big.render("VICTORY!", True, (40, 40, 40))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 110))
        self.screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)
        message = f"Player {winner} wins the match!"
        text = self.font_menu.render(message, True, constants.COLOR_YELLOW)
        self.screen.blit(text, text.get_rect(
            center=(constants.SCREEN_WIDTH // 2, 185)))
        score_text = self.font_menu.render(f"{wins[0]}  —  {wins[1]}", True, constants.COLOR_WHITE)
        self.screen.blit(score_text, score_text.get_rect(
            center=(constants.SCREEN_WIDTH // 2, 225)))
        # Option menu
        grace_remaining = constants.ROUND_END_INPUT_GRACE - (
            _time.monotonic() - game._state_entry_time)
        options = ("Play Again", "Return to Menu")
        option_y_start = 290
        option_gap = 38
        for i, label in enumerate(options):
            selected = (i == game._match_over_option)
            if grace_remaining > 0:
                color = constants.COLOR_GREY
            elif selected:
                color = constants.COLOR_GREEN
            else:
                color = constants.COLOR_LIGHT_GREY
            prefix = "► " if selected else "  "
            opt_surf = self.font_menu.render(prefix + label, True, color)
            self.screen.blit(opt_surf, opt_surf.get_rect(
                center=(constants.SCREEN_WIDTH // 2, option_y_start + i * option_gap)))
        # Hint row
        if grace_remaining > 0:
            hint_text = f"Please wait…"
            hint_color = constants.COLOR_GREY
        else:
            hint_text = "↑↓ select   [Start] confirm"
            hint_color = constants.COLOR_GREY
        hint = self.font_small.render(hint_text, True, hint_color)
        self.screen.blit(hint, hint.get_rect(
            center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT - 30)))
