<h1>Maxbloks Game Development Quick Reference</h1><p>When creating a new game for the maxbloks collection, follow these guidelines:</p><h2>Project Structure</h2><pre><code>maxbloks/yourgame/
├── __init__.py           # Package marker
├── main.py               # Entry point
├── game.py               # Main game class
├── constants.py          # All configuration constants
├── entities.py           # Player, enemies, and game objects
├── utils.py              # Helper functions
├── compat_sdl.py         # Symlink to ../common/compat_sdl.py
├── tests/                # Unit tests
├── BUILD                 # Bazel build config
├── README.md             # Documentation
├── CLAUDE.md             # AI assistant docs
├── game.json             # Metadata
└── version.json          # Version info
</code></pre><h2>Architecture Patterns</h2><h3>Option A: GameFramework (Simple Games)</h3><ul> <li>Extend <code>GameFramework</code> base class</li> <li>Override: <code>handle_input()</code>, <code>update()</code>, <code>draw()</code></li> <li>Use <code>self.movement_x/y</code> for input, <code>self.draw_text()</code> for UI</li> </ul><h3>Option B: State Machine (Complex Games)</h3><ul> <li>States: MENU → PLAYING ↔ PAUSED → GAME_OVER</li> <li>Separate update/draw methods per state</li> <li>Use <code>enum.Enum</code> for state definitions</li> </ul><h2>Python Style Guidelines</h2><ul> <li><strong>Imports</strong>: <code>import module</code> then <code>module.Class</code> (not <code>from module import Class</code>)</li> <li><strong>Paths</strong>: Use <code>pathlib</code>, not <code>os.path</code></li> <li><strong>Classes</strong>: Prefer custom classes over dictionaries; keep under 400 lines</li> <li><strong>Methods</strong>: Keep minimal; factor out logical sections</li> <li><strong>Naming</strong>: PascalCase for classes, snake_case for functions, UPPER_SNAKE_CASE for constants</li> </ul><h2>Key Requirements</h2><ol> <li><strong>Dual Input Support</strong>: Must work with both keyboard AND gamepad</li> <li><strong>Display</strong>: Use <code>compat_sdl.init_display()</code> for SDL bootstrap; support fullscreen/windowed</li> <li><strong>Resolution</strong>: Design for 640×480 or 800×600 logical resolution with scaling</li> <li><strong>Performance</strong>: Target 60 FPS; pre-render static surfaces; avoid object creation in game loop</li> <li><strong>Testing</strong>: Use <code>unittest</code>; one TestCase per module; maintain &gt;80% coverage for core modules</li> </ol><h2>Common Patterns</h2><h3>Display Initialization</h3><pre><code class="language-python">from maxbloks.yourgame.compat_sdl import init_display
screen, info = init_display(size=(640, 480), fullscreen=True, vsync=True)
</code></pre><h3>Game Loop</h3><pre><code class="language-python">def run(self):
    while self.running:
        self.handle_input()
        self.update()
        self.draw()
        self.clock.tick(60)
</code></pre><h3>Input Handling</h3><ul> <li>Keyboard: Arrow keys + WASD for movement, Space for action</li> <li>Gamepad: D-pad/Left stick for movement, A/B buttons for action</li> <li>Normalize diagonal movement (multiply by 0.707)</li> <li>Implement joystick deadzone (0.2 typical)</li> </ul><h2>Documentation Requirements</h2><ul> <li>README.md: Installation, controls, features</li> <li>CLAUDE.md: Architecture, dependencies, configuration, development notes</li> <li>All files need GPL-3.0-or-later license headers</li> </ul><h2>Pre-Submit Checklist</h2><ul> <li><input disabled="" type="checkbox"> Runs via <code>python -m maxbloks.yourgame.main</code></li> <li><input disabled="" type="checkbox"> Both keyboard and gamepad work</li> <li><input disabled="" type="checkbox"> Tests pass: <code>python -m unittest discover</code></li> <li><input disabled="" type="checkbox"> Documentation complete (README.md, CLAUDE.md)</li> <li><input disabled="" type="checkbox"> game.json and version.json present</li> <li><input disabled="" type="checkbox"> Symlink to compat_sdl.py created</li> <li><input disabled="" type="checkbox"> License headers on all source files</li> </ul>