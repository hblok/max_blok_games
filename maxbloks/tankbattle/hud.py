# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Heads-up display drawing for TankBattle with polished visuals."""

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import hazards


class Hud:
    """Draw screen-space HUD elements with visual polish."""

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self.font = pygame_module.font.Font(None, constants.HUD_FONT_SIZE)
        self.small_font = pygame_module.font.Font(None, constants.SMALL_FONT_SIZE)
        self.minimap_surface = pygame_module.Surface(
            (constants.HUD_MINIMAP_WIDTH, constants.HUD_MINIMAP_HEIGHT),
            pygame_module.SRCALPHA,
        )

    def draw(self, screen, game):
        """Draw all HUD elements."""
        self._draw_hp(screen, game.local_tank)
        self._draw_weapon(screen, game.local_tank)
        self._draw_round_pips(screen, game.round_wins, game.local_player_index)
        self._draw_timer(screen, game)
        self._draw_minimap(screen, game)
        # Issue 3: In-game connection status widget
        if not game.single_player:
            self._draw_connection_status(screen, game)

    def _draw_hp(self, screen, tank):
        bg_width = constants.TANK_MAX_HP * (constants.HUD_HP_SEGMENT_WIDTH + constants.HUD_HP_SEGMENT_GAP) + 8
        bg_height = constants.HUD_HP_SEGMENT_HEIGHT + 10
        bg_surf = self.pygame.Surface((bg_width, bg_height), self.pygame.SRCALPHA)
        self.pygame.draw.rect(bg_surf, (0, 0, 0, 120), (0, 0, bg_width, bg_height), border_radius=4)
        self.pygame.draw.rect(bg_surf, (255, 255, 255, 40), (0, 0, bg_width, bg_height), 1, border_radius=4)
        screen.blit(bg_surf, (constants.HUD_HP_X - 4, constants.HUD_HP_Y - 5))
        for index in range(constants.TANK_MAX_HP):
            x_value = constants.HUD_HP_X + index * (
                constants.HUD_HP_SEGMENT_WIDTH + constants.HUD_HP_SEGMENT_GAP
            )
            rect = (
                x_value,
                constants.HUD_HP_Y,
                constants.HUD_HP_SEGMENT_WIDTH,
                constants.HUD_HP_SEGMENT_HEIGHT,
            )
            if index < tank.hp:
                if tank.hp > constants.TANK_MAX_HP * 0.6:
                    color = constants.COLOR_GREEN
                elif tank.hp > constants.TANK_MAX_HP * 0.3:
                    color = constants.COLOR_YELLOW
                else:
                    color = constants.COLOR_RED
                self.pygame.draw.rect(screen, color, rect, border_radius=2)
                highlight = tuple(min(255, c + 60) for c in color)
                self.pygame.draw.line(screen, highlight,
                                      (x_value + 2, constants.HUD_HP_Y + 1),
                                      (x_value + constants.HUD_HP_SEGMENT_WIDTH - 2, constants.HUD_HP_Y + 1), 1)
            else:
                self.pygame.draw.rect(screen, constants.COLOR_DARK_GREY, rect, border_radius=2)
            self.pygame.draw.rect(screen, (200, 200, 200), rect, 1, border_radius=2)

    def _draw_weapon(self, screen, tank):
        weapon_width = 160
        weapon_height = 28
        bg_surf = self.pygame.Surface((weapon_width, weapon_height), self.pygame.SRCALPHA)
        self.pygame.draw.rect(bg_surf, (0, 0, 0, 120), (0, 0, weapon_width, weapon_height), border_radius=4)
        self.pygame.draw.rect(bg_surf, (255, 255, 255, 40), (0, 0, weapon_width, weapon_height), 1, border_radius=4)
        screen.blit(bg_surf, (constants.HUD_WEAPON_X - weapon_width // 2, constants.HUD_WEAPON_Y - 8))
        text = tank.active_weapon.value.replace("_", " ").upper()
        if tank.active_weapon == entities.WeaponType.PRIMARY:
            text_color = constants.COLOR_LIGHT_GREY
        else:
            if tank.active_weapon == entities.WeaponType.ROCKET:
                text_color = constants.COLOR_ORANGE
            elif tank.active_weapon == entities.WeaponType.RICOCHET:
                text_color = (180, 80, 220)
            elif tank.active_weapon == entities.WeaponType.SPREAD_SHOT:
                text_color = (80, 180, 220)
            elif tank.active_weapon == entities.WeaponType.RAPID_FIRE:
                text_color = constants.COLOR_YELLOW
            elif tank.active_weapon == entities.WeaponType.MINE_LAYER:
                text_color = constants.COLOR_LIGHT_GREY
            else:
                text_color = constants.COLOR_WHITE
        surface = self.small_font.render(text, True, text_color)
        rect = surface.get_rect(center=(constants.HUD_WEAPON_X, constants.HUD_WEAPON_Y))
        screen.blit(surface, rect)
        if tank.active_weapon != entities.WeaponType.PRIMARY:
            bar_width = 120
            bar_height = 5
            bar_x = constants.HUD_WEAPON_X - bar_width // 2
            bar_y = constants.HUD_WEAPON_Y + 10
            self.pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=2)
            fill_ratio = tank.weapon_timer / constants.WEAPON_DURATION
            fill_width = int(bar_width * fill_ratio)
            if fill_width > 0:
                bar_color = constants.COLOR_YELLOW
                if fill_ratio < 0.3:
                    bar_color = constants.COLOR_RED
                elif fill_ratio < 0.6:
                    bar_color = constants.COLOR_YELLOW
                self.pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_width, bar_height), border_radius=2)
            self.pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1, border_radius=2)
            if tank.weapon_shots > 0:
                shots = self.small_font.render(str(tank.weapon_shots), True, constants.COLOR_WHITE)
                screen.blit(shots, (bar_x + bar_width + 4, bar_y - 3))

    def _draw_round_pips(self, screen, wins, local_player_index):
        r = constants.HUD_PIP_RADIUS
        spacing = r * 3
        bg_width = (constants.ROUNDS_TO_WIN - 1) * spacing + 2 * r + 10
        bg_height = spacing + 2 * r + 10
        bg_surf = self.pygame.Surface((bg_width, bg_height), self.pygame.SRCALPHA)
        self.pygame.draw.rect(bg_surf, (0, 0, 0, 120), (0, 0, bg_width, bg_height), border_radius=4)
        self.pygame.draw.rect(bg_surf, (255, 255, 255, 40), (0, 0, bg_width, bg_height), 1, border_radius=4)
        screen.blit(bg_surf, (constants.HUD_ROUND_X - r - 5, constants.HUD_ROUND_Y - r - 5))
        for player in range(2):
            base_color = constants.COLOR_GREEN if player == local_player_index else constants.COLOR_RED
            for pip in range(constants.ROUNDS_TO_WIN):
                x_value = constants.HUD_ROUND_X + pip * constants.HUD_PIP_RADIUS * 3
                y_value = constants.HUD_ROUND_Y + player * constants.HUD_PIP_RADIUS * 3
                if pip < wins[player]:
                    self.pygame.draw.circle(screen, base_color, (x_value, y_value), constants.HUD_PIP_RADIUS)
                    highlight = tuple(min(255, c + 50) for c in base_color)
                    self.pygame.draw.circle(screen, highlight,
                                            (x_value - 1, y_value - 1), constants.HUD_PIP_RADIUS - 2, 1)
                else:
                    self.pygame.draw.circle(screen, constants.COLOR_DARK_GREY,
                                            (x_value, y_value), constants.HUD_PIP_RADIUS)
                    self.pygame.draw.circle(screen, (80, 80, 80),
                                            (x_value, y_value), constants.HUD_PIP_RADIUS, 1)

    def _draw_timer(self, screen, game):
        timer_text = str(int(max(0.0, game.round_time_remaining)))
        timer_color = constants.COLOR_WHITE
        if game.sudden_death:
            timer_text = "SUDDEN DEATH"
            timer_color = constants.COLOR_RED
        elif game.round_time_remaining < 15:
            timer_color = constants.COLOR_YELLOW
        elif game.round_time_remaining < 30:
            timer_color = constants.COLOR_LIGHT_GREY
        surface = self.small_font.render(timer_text, True, timer_color)
        rect = surface.get_rect(center=(constants.HUD_WEAPON_X, constants.HUD_TIMER_Y))
        bg_surf = self.pygame.Surface((rect.width + 12, rect.height + 6), self.pygame.SRCALPHA)
        self.pygame.draw.rect(bg_surf, (0, 0, 0, 120),
                              (0, 0, bg_surf.get_width(), bg_surf.get_height()), border_radius=4)
        screen.blit(bg_surf, (rect.x - 6, rect.y - 3))
        screen.blit(surface, rect)

    def _draw_minimap(self, screen, game):
        self.minimap_surface.fill((0, 0, 0, 140))
        self.pygame.draw.rect(
            self.minimap_surface,
            (80, 80, 80),
            (0, 0, constants.HUD_MINIMAP_WIDTH - 1, constants.HUD_MINIMAP_HEIGHT - 1),
            1,
        )
        for tile_x, tile_y in game.arena.hard_tiles:
            x_value = int(tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
            y_value = int(tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
            size_x = max(1, int(constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X))
            size_y = max(1, int(constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y))
            x_value = min(x_value, constants.HUD_MINIMAP_WIDTH - size_x)
            y_value = min(y_value, constants.HUD_MINIMAP_HEIGHT - size_y)
            self.pygame.draw.rect(self.minimap_surface, (60, 60, 65),
                                  (x_value, y_value, size_x, size_y))
        for tile_x, tile_y in game.arena.soft_tiles:
            obstacle = game.arena.obstacle_map.get((tile_x, tile_y))
            if obstacle is not None and not obstacle.is_destroyed:
                x_value = int(tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
                y_value = int(tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
                size_x = max(1, int(constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X))
                size_y = max(1, int(constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y))
                x_value = min(x_value, constants.HUD_MINIMAP_WIDTH - size_x)
                y_value = min(y_value, constants.HUD_MINIMAP_HEIGHT - size_y)
                self.pygame.draw.rect(self.minimap_surface, (100, 75, 50),
                                      (x_value, y_value, size_x, size_y))
        # Draw ice patches on minimap
        for ice in game.arena.ice_patches:
            x_value = int(ice.tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
            y_value = int(ice.tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
            self.minimap_surface.set_at(
                (max(0, min(x_value, constants.HUD_MINIMAP_WIDTH - 1)),
                 max(0, min(y_value, constants.HUD_MINIMAP_HEIGHT - 1))),
                (180, 220, 255),
            )
        # Draw mud swamps on minimap
        for mud in game.arena.mud_swamps:
            x_value = int(mud.tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
            y_value = int(mud.tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
            self.minimap_surface.set_at(
                (max(0, min(x_value, constants.HUD_MINIMAP_WIDTH - 1)),
                 max(0, min(y_value, constants.HUD_MINIMAP_HEIGHT - 1))),
                (100, 70, 30),
            )
        # Draw teleporters on minimap
        for tp in game.arena.teleporters:
            x_value = int(tp.tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
            y_value = int(tp.tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
            x_value = max(0, min(x_value, constants.HUD_MINIMAP_WIDTH - 3))
            y_value = max(0, min(y_value, constants.HUD_MINIMAP_HEIGHT - 3))
            self.pygame.draw.circle(self.minimap_surface, (180, 100, 255), (x_value, y_value), 2)
        # Draw turrets on minimap
        for turret in game.arena.turrets:
            if not turret.is_alive:
                continue
            x_value = int(turret.tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
            y_value = int(turret.tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
            x_value = max(0, min(x_value, constants.HUD_MINIMAP_WIDTH - 3))
            y_value = max(0, min(y_value, constants.HUD_MINIMAP_HEIGHT - 3))
            self.pygame.draw.circle(self.minimap_surface, (200, 80, 80), (x_value, y_value), 2)
        for powerup in game.powerups:
            px = int(powerup.x * constants.HUD_MINIMAP_SCALE_X)
            py = int(powerup.y * constants.HUD_MINIMAP_SCALE_Y)
            px = min(px, constants.HUD_MINIMAP_WIDTH - 2)
            py = min(py, constants.HUD_MINIMAP_HEIGHT - 2)
            self.minimap_surface.set_at((max(0, px), max(0, py)), constants.COLOR_YELLOW)
        for idx, tank in enumerate(game.tanks):
            dot_color = constants.COLOR_GREEN if idx == game.local_player_index else constants.COLOR_RED
            self._draw_tank_dot(tank, dot_color)
        camera = game.arena.clamp_camera(game.local_tank.position)
        cam_x = int(camera[0] * constants.HUD_MINIMAP_SCALE_X)
        cam_y = int(camera[1] * constants.HUD_MINIMAP_SCALE_Y)
        cam_w = int(constants.SCREEN_WIDTH * constants.HUD_MINIMAP_SCALE_X)
        cam_h = int(constants.SCREEN_HEIGHT * constants.HUD_MINIMAP_SCALE_Y)
        self.pygame.draw.rect(self.minimap_surface, (255, 255, 255, 80),
                              (cam_x, cam_y, cam_w, cam_h), 1)
        screen.blit(self.minimap_surface, (constants.HUD_MINIMAP_X, constants.HUD_MINIMAP_Y))

    def _draw_tank_dot(self, tank, color):
        if not tank.is_alive:
            return
        x_value = int(tank.x * constants.HUD_MINIMAP_SCALE_X)
        y_value = int(tank.y * constants.HUD_MINIMAP_SCALE_Y)
        x_value = max(2, min(x_value, constants.HUD_MINIMAP_WIDTH - 3))
        y_value = max(2, min(y_value, constants.HUD_MINIMAP_HEIGHT - 3))
        self.pygame.draw.circle(self.minimap_surface, color, (x_value, y_value), 3)
        outline_color = tuple(min(255, c + 80) for c in color)
        self.pygame.draw.circle(self.minimap_surface, outline_color, (x_value, y_value), 3, 1)

    # ------------------------------------------------------------------
    # Issue 3: In-Game Connection Status Widget
    # ------------------------------------------------------------------

    def _draw_connection_status(self, screen, game):
        """Draw a signal-strength bar indicator in the top-right corner.

        Shows connection quality as 1–4 filled bars:
          - 4 bars (green):  quality >= 0.8 (Good)
          - 3 bars (yellow): quality >= 0.6 (OK)
          - 2 bars (orange): quality >= 0.4 (Poor)
          - 1 bar  (red):    quality >  0.0 (Weak)
          - 0 bars (grey):   quality == 0.0 or not connected

        A small label beneath the bars shows the status text.
        The widget is only drawn during multiplayer games.
        """
        monitor = game.net.monitor
        quality = monitor.quality
        is_connected = monitor.is_connected

        x = constants.HUD_CONN_X
        y = constants.HUD_CONN_Y
        bar_w = constants.HUD_CONN_BAR_WIDTH
        bar_h_max = constants.HUD_CONN_BAR_HEIGHT
        gap = constants.HUD_CONN_BAR_GAP
        num_bars = constants.HUD_CONN_NUM_BARS

        # Background panel
        panel_w = num_bars * (bar_w + gap) + 12
        panel_h = bar_h_max + 24
        bg_surf = self.pygame.Surface((panel_w, panel_h), self.pygame.SRCALPHA)
        self.pygame.draw.rect(bg_surf, (0, 0, 0, 120),
                              (0, 0, panel_w, panel_h), border_radius=4)
        self.pygame.draw.rect(bg_surf, (255, 255, 255, 40),
                              (0, 0, panel_w, panel_h), 1, border_radius=4)
        screen.blit(bg_surf, (x - 6, y - 4))

        # Determine how many bars to fill and the color
        if not is_connected:
            filled_bars = 0
            bar_color = constants.COLOR_GREY
            status_text = "DC"
        elif quality >= constants.CONNECTION_QUALITY_GOOD:
            filled_bars = 4
            bar_color = constants.COLOR_GREEN
            status_text = "OK"
        elif quality >= 0.6:
            filled_bars = 3
            bar_color = constants.COLOR_YELLOW
            status_text = "OK"
        elif quality >= constants.CONNECTION_QUALITY_POOR:
            filled_bars = 2
            bar_color = constants.COLOR_ORANGE
            status_text = "LOW"
        elif quality > 0.0:
            filled_bars = 1
            bar_color = constants.COLOR_RED
            status_text = "LOW"
        else:
            filled_bars = 0
            bar_color = constants.COLOR_GREY
            status_text = "DC"

        # Draw the signal bars (shortest on left, tallest on right)
        for i in range(num_bars):
            bar_index = i + 1  # 1-based
            # Each bar has a height proportional to its index
            h = int(bar_h_max * bar_index / num_bars)
            bar_x = x + i * (bar_w + gap)
            bar_y = y + bar_h_max - h  # bottom-aligned

            if bar_index <= filled_bars:
                # Filled bar
                self.pygame.draw.rect(screen, bar_color,
                                      (bar_x, bar_y, bar_w, h), border_radius=1)
                # Subtle highlight on top edge
                highlight = tuple(min(255, c + 60) for c in bar_color)
                self.pygame.draw.line(screen, highlight,
                                      (bar_x + 1, bar_y + 1),
                                      (bar_x + bar_w - 2, bar_y + 1), 1)
            else:
                # Empty bar outline
                self.pygame.draw.rect(screen, (60, 60, 60),
                                      (bar_x, bar_y, bar_w, h), border_radius=1)
                self.pygame.draw.rect(screen, (80, 80, 80),
                                      (bar_x, bar_y, bar_w, h), 1, border_radius=1)

        # Status label below the bars
        label_color = bar_color
        label_surf = self.small_font.render(status_text, True, label_color)
        label_rect = label_surf.get_rect(
            center=(x + (num_bars * (bar_w + gap) - gap) // 2, y + bar_h_max + 10)
        )
        screen.blit(label_surf, label_rect)
