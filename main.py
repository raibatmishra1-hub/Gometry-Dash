import random
import sys
import time
import pygame

# ================================================================
# INITIALIZE PYGAME
# ================================================================

pygame.init()
pygame.mixer.init()

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
FPS = 60
# ================================================================
# BACKGROUND MUSIC & SOUND EFFECTS
# ================================================================

pygame.mixer.music.load("./audio/level1.ogg")
pygame.mixer.music.set_volume(100)

explode_sound = pygame.mixer.Sound("./audio/explode.ogg")
explode_sound.set_volume(0.9)

# ================================================================
# GAMEPLAY CONSTANTS
# ================================================================

GROUND_Y = int(SCREEN_HEIGHT * 0.8)

GRAVITY = 1
JUMP_STRENGTH = -20
PAD_JUMP_STRENGTH = -30

PLAYER_SIZE = 60

# ================================================================
# COLORS
# ================================================================

BACKGROUND_COLOR = (10, 12, 26)
GROUND_COLOR = (16, 20, 42)
GRID_LINE_COLOR = (30, 40, 55)

NEON_LINE_COLOR = (0, 180, 255)
NEON_GLOW_COLOR = (0, 90, 180)

CUBE_COLOR = (0, 255, 200)
CUBE_BORDER = (0, 180, 150)

SPIKE_COLOR = (255, 40, 80)

BLOCK_COLOR = (0, 120, 255)
BLOCK_BORDER = (100, 200, 255)

PAD_COLOR = (255, 220, 0)
PAD_BORDER = (255, 150, 0)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ================================================================
# DISPLAY
# ================================================================

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption("Geometry Dash")

clock = pygame.time.Clock()

font = pygame.font.SysFont(
    "serif",
    int(SCREEN_HEIGHT * 0.04),
    bold=True
)

# ================================================================
# SOUND FUNCTIONS
# ================================================================

def start_music():

    pygame.mixer.music.play(-1)


def player_died():

    # Stop background music immediately
    pygame.mixer.music.stop()

    # Play explosion once
    explode_sound.play()


# ================================================================
# EXIT
# ================================================================

def clean_exit():

    pygame.mixer.music.stop()

    screen.fill(BLACK)

    pygame.display.flip()

    time.sleep(0.2)

    pygame.mixer.stop()

    pygame.quit()

    sys.exit()


# ================================================================
# PARTICLES
# ================================================================

class Particle:

    def __init__(self, x, y, color, is_burst=False):

        self.x = x
        self.y = y
        self.color = color

        if is_burst:

            self.vx = random.uniform(-4, 4)
            self.vy = random.uniform(-8, -2)

            self.size = random.uniform(4, 8)

            self.alpha = 255

            self.fade_speed = random.uniform(
                5,
                10
            )

        else:

            self.vx = random.uniform(-3, -1)
            self.vy = random.uniform(-1, 1)

            self.size = random.uniform(3, 6)

            self.alpha = 150

            self.fade_speed = random.uniform(
                8,
                12
            )

    def update(self):

        self.x += self.vx
        self.y += self.vy

        self.alpha -= self.fade_speed

        if self.alpha < 0:

            self.alpha = 0

    def draw(self, surface):

        if self.alpha <= 0:

            return

        size = max(
            1,
            int(self.size)
        )

        particle_surface = pygame.Surface(
            (
                size * 2,
                size * 2
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            particle_surface,
            (
                *self.color,
                int(self.alpha)
            ),
            (
                size,
                size
            ),
            size
        )

        surface.blit(
            particle_surface,
            (
                int(self.x - size),
                int(self.y - size)
            )
        )


# ================================================================
# PLAYER
# ================================================================

class CubePlayer:

    def __init__(self):

        self.size = PLAYER_SIZE

        self.x = 200

        self.y = (
            GROUND_Y
            - self.size
        )

        self.velocity_y = 0

        self.is_grounded = True

        self.angle = 0

        self.base_image = pygame.Surface(
            (
                self.size,
                self.size
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            self.base_image,
            CUBE_COLOR,
            (
                0,
                0,
                self.size,
                self.size
            )
        )

        pygame.draw.rect(
            self.base_image,
            CUBE_BORDER,
            (
                0,
                0,
                self.size,
                self.size
            ),
            4
        )

    def jump(self, particles_list):

        if self.is_grounded:

            self.velocity_y = JUMP_STRENGTH

            self.is_grounded = False

            for _ in range(15):

                particles_list.append(
                    Particle(
                        self.x + self.size // 2,
                        self.y + self.size,
                        CUBE_COLOR,
                        is_burst=True
                    )
                )

    def pad_jump(self, particles_list):

        self.velocity_y = PAD_JUMP_STRENGTH

        self.is_grounded = False

        for _ in range(25):

            particles_list.append(
                Particle(
                    self.x + self.size // 2,
                    self.y + self.size,
                    PAD_COLOR,
                    is_burst=True
                )
            )

    def update(
        self,
        obstacles,
        particles_list
    ):

        previous_y = self.y

        # ========================================================
        # GRAVITY
        # ========================================================

        self.velocity_y += GRAVITY

        self.y += self.velocity_y

        self.is_grounded = False

        player_rect = self.get_hitbox()

        # ========================================================
        # BLOCK / PAD LANDING
        # ========================================================

        for obs in obstacles:

            # ----------------------------------------------------
            # JUMP PAD
            # ----------------------------------------------------

            if isinstance(
                obs,
                JumpPad
            ):

                pad_rect = obs.get_rect()

                previous_bottom = (
                    previous_y
                    + self.size
                    - 6
                )

                if (
                    self.velocity_y >= 0
                    and
                    previous_bottom
                    <= pad_rect.top + 10
                    and
                    player_rect.bottom
                    >= pad_rect.top
                    and
                    player_rect.right
                    > pad_rect.left + 4
                    and
                    player_rect.left
                    < pad_rect.right - 4
                ):

                    self.y = (
                        pad_rect.top
                        - self.size
                        + 6
                    )

                    self.pad_jump(
                        particles_list
                    )

                    obs.activate()

                    break

            # ----------------------------------------------------
            # NORMAL BLOCK
            # ----------------------------------------------------

            elif isinstance(
                obs,
                ObstacleBlock
            ):

                block_rect = obs.get_rect()

                previous_bottom = (
                    previous_y
                    + self.size
                    - 6
                )

                if (
                    self.velocity_y >= 0
                    and
                    previous_bottom
                    <= block_rect.top + 12
                    and
                    player_rect.bottom
                    >= block_rect.top
                    and
                    player_rect.right
                    > block_rect.left + 4
                    and
                    player_rect.left
                    < block_rect.right - 4
                ):

                    self.y = (
                        block_rect.top
                        - self.size
                    )

                    self.velocity_y = 0

                    self.is_grounded = True

                    break

        # ========================================================
        # GROUND
        # ========================================================

        if self.y >= (
            GROUND_Y
            - self.size
        ):

            self.y = (
                GROUND_Y
                - self.size
            )

            self.velocity_y = 0

            self.is_grounded = True

        # ========================================================
        # GROUND PARTICLES
        # ========================================================

        if (
            self.is_grounded
            and random.random() < 0.4
        ):

            particles_list.append(
                Particle(
                    self.x + 4,
                    self.y + self.size - 2,
                    CUBE_COLOR
                )
            )

        # ========================================================
        # ROTATION
        # ========================================================

        if not self.is_grounded:

            self.angle -= 8.0

        else:

            remainder = self.angle % -90

            if remainder != 0:

                if remainder <= -45:

                    self.angle += (
                        -90
                        - remainder
                    )

                else:

                    self.angle -= remainder

            self.angle = (
                self.angle % -360
            )

    def draw(self, surface):

        rotated_image = pygame.transform.rotate(
            self.base_image,
            self.angle
        )

        rotated_rect = (
            rotated_image.get_rect()
        )

        rotated_rect.center = (
            self.x
            + self.size // 2,
            self.y
            + self.size // 2
        )

        surface.blit(
            rotated_image,
            rotated_rect.topleft
        )

    def get_hitbox(self):

        return pygame.Rect(
            self.x + 6,
            self.y + 6,
            self.size - 12,
            self.size - 12
        )


# ================================================================
# SPIKE
# ================================================================

class ObstacleSpike:

    def __init__(
        self,
        x_pos,
        y_pos,
        speed
    ):

        self.width = 50
        self.height = 55

        self.x = x_pos
        self.y = y_pos

        self.speed = speed

    def update(self):

        self.x -= self.speed

    def draw(self, surface):

        points = [

            (
                int(self.x),
                int(self.y)
            ),

            (
                int(self.x + self.width),
                int(self.y)
            ),

            (
                int(
                    self.x
                    + self.width // 2
                ),
                int(
                    self.y
                    - self.height
                )
            )
        ]

        pygame.draw.polygon(
            surface,
            SPIKE_COLOR,
            points
        )

    def get_mask_rect(self):

        return pygame.Rect(
            int(self.x + 6),
            int(
                self.y
                - self.height
                + 6
            ),
            self.width - 12,
            self.height - 6
        )


# ================================================================
# BLOCK
# ================================================================

class ObstacleBlock:

    def __init__(
        self,
        x_pos,
        speed
    ):

        self.width = 50
        self.height = 55

        self.x = x_pos

        self.y = (
            GROUND_Y
            - self.height
        )

        self.speed = speed

    def update(self):

        self.x -= self.speed

    def draw(self, surface):

        pygame.draw.rect(
            surface,
            BLOCK_COLOR,
            (
                int(self.x),
                int(self.y),
                self.width,
                self.height
            )
        )

        pygame.draw.rect(
            surface,
            BLOCK_BORDER,
            (
                int(self.x),
                int(self.y),
                self.width,
                self.height
            ),
            3
        )

    def get_rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )


# ================================================================
# JUMP PAD
# ================================================================

class JumpPad:

    def __init__(
        self,
        x_pos,
        y_pos,
        speed
    ):

        self.width = 50
        self.height = 14

        self.x = x_pos
        self.y = y_pos

        self.speed = speed

        self.active_timer = 0

    def update(self):

        self.x -= self.speed

        if self.active_timer > 0:

            self.active_timer -= 1

    def activate(self):

        self.active_timer = 8

    def draw(self, surface):

        extra = (
            5
            if self.active_timer > 0
            else 0
        )

        pad_y = int(
            self.y + extra
        )

        # Glow
        glow = pygame.Surface(
            (
                self.width + 20,
                self.height + 20
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            glow,
            (
                255,
                220,
                0,
                50
            ),
            (
                10,
                10,
                self.width,
                self.height
            )
        )

        surface.blit(
            glow,
            (
                int(self.x - 10),
                int(self.y - 10)
            )
        )

        # Main pad
        pygame.draw.rect(
            surface,
            PAD_COLOR,
            (
                int(self.x),
                pad_y,
                self.width,
                self.height
            )
        )

        # Border
        pygame.draw.rect(
            surface,
            PAD_BORDER,
            (
                int(self.x),
                pad_y,
                self.width,
                self.height
            ),
            3
        )

        # Up arrow
        center_x = int(
            self.x
            + self.width // 2
        )

        arrow_points = [

            (
                center_x,
                pad_y - 12
            ),

            (
                center_x - 10,
                pad_y
            ),

            (
                center_x + 10,
                pad_y
            )
        ]

        pygame.draw.polygon(
            surface,
            WHITE,
            arrow_points
        )

    def get_rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )


# ================================================================
# FLOOR
# ================================================================

def draw_scrolling_floor(
    surface,
    scroll_offset
):

    pygame.draw.rect(
        surface,
        GROUND_COLOR,
        (
            0,
            GROUND_Y,
            SCREEN_WIDTH,
            SCREEN_HEIGHT - GROUND_Y
        )
    )

    grid_spacing = 60

    start_x = -int(
        scroll_offset
        % grid_spacing
    )

    for x in range(
        start_x,
        SCREEN_WIDTH + grid_spacing,
        grid_spacing
    ):

        pygame.draw.line(
            surface,
            GRID_LINE_COLOR,
            (x, GROUND_Y),
            (
                int(x - 40),
                int(SCREEN_HEIGHT)
            ),
            2
        )

    pygame.draw.line(
        surface,
        GRID_LINE_COLOR,
        (
            0,
            GROUND_Y + 40
        ),
        (
            SCREEN_WIDTH,
            GROUND_Y + 40
        ),
        2
    )

    pygame.draw.line(
        surface,
        GRID_LINE_COLOR,
        (
            0,
            GROUND_Y + 100
        ),
        (
            SCREEN_WIDTH,
            GROUND_Y + 100
        ),
        1
    )

    glow_surface = pygame.Surface(
        (
            SCREEN_WIDTH,
            12
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        glow_surface,
        (
            *NEON_GLOW_COLOR,
            80
        ),
        (
            0,
            0,
            SCREEN_WIDTH,
            12
        )
    )

    surface.blit(
        glow_surface,
        (
            0,
            GROUND_Y - 4
        )
    )

    pygame.draw.line(
        surface,
        NEON_LINE_COLOR,
        (
            0,
            GROUND_Y
        ),
        (
            SCREEN_WIDTH,
            GROUND_Y
        ),
        4
    )


# ================================================================
# GAME
# ================================================================

def run_game(attempt_count):

    # Start/restart background music
    start_music()

    player = CubePlayer()

    obstacles = []
    particles = []

    score = 0

    game_speed = 10.0

    last_spawn_distance = 999

    floor_scroll = 0

    game_over = False

    running = True

    while running:

        clock.tick(FPS)

        # ========================================================
        # EVENTS
        # ========================================================

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                clean_exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    clean_exit()

                if (
                    event.key in [
                        pygame.K_SPACE,
                        pygame.K_UP,
                        pygame.K_w
                    ]
                    and not game_over
                ):

                    player.jump(
                        particles
                    )

                if (
                    event.key == pygame.K_r
                    and game_over
                ):

                    return True

        # ========================================================
        # UPDATE
        # ========================================================

        if not game_over:

            player.update(
                obstacles,
                particles
            )

            floor_scroll += game_speed

            last_spawn_distance += (
                game_speed
            )

            game_speed = (
                9.0
                + score * 0.12
            )

            # ====================================================
            # SPAWNING
            # ====================================================

            MIN_SAFE_GAP = 600
            MAX_SAFE_GAP = 850

            if (
                last_spawn_distance
                > MIN_SAFE_GAP
            ):

                if (
                    random.random() < 0.035
                    or
                    last_spawn_distance
                    > MAX_SAFE_GAP
                ):

                    choice = random.choice(
                        [
                            "spike",
                            "block_run",
                            "spike_on_block",
                            "jump_pad"
                        ]
                    )

                    base_x = (
                        SCREEN_WIDTH + 50
                    )

                    # --------------------------------------------
                    # SPIKE
                    # --------------------------------------------

                    if choice == "spike":

                        obstacles.append(
                            ObstacleSpike(
                                base_x,
                                GROUND_Y,
                                game_speed
                            )
                        )

                    # --------------------------------------------
                    # BLOCK RUN
                    # --------------------------------------------

                    elif choice == "block_run":

                        num_blocks = random.randint(
                            1,
                            3
                        )

                        for i in range(
                            num_blocks
                        ):

                            obstacles.append(
                                ObstacleBlock(
                                    base_x
                                    + i * 50,
                                    game_speed
                                )
                            )

                    # --------------------------------------------
                    # SPIKE ON BLOCK
                    # --------------------------------------------

                    elif choice == "spike_on_block":

                        num_blocks = random.randint(
                            2,
                            3
                        )

                        spike_index = random.randint(
                            0,
                            num_blocks - 1
                        )

                        for i in range(
                            num_blocks
                        ):

                            block_x = (
                                base_x
                                + i * 50
                            )

                            obstacles.append(
                                ObstacleBlock(
                                    block_x,
                                    game_speed
                                )
                            )

                            if i == spike_index:

                                obstacles.append(
                                    ObstacleSpike(
                                        block_x,
                                        GROUND_Y - 55,
                                        game_speed
                                    )
                                )

                    # --------------------------------------------
                    # JUMP PAD
                    # --------------------------------------------

                    elif choice == "jump_pad":

                        obstacles.append(
                            JumpPad(
                                base_x,
                                GROUND_Y - 14,
                                game_speed
                            )
                        )

                    last_spawn_distance = 0

            # ====================================================
            # PARTICLES
            # ====================================================

            for p in particles[:]:

                p.update()

                if p.alpha <= 0:

                    particles.remove(p)

            # ====================================================
            # COLLISION
            # ====================================================

            player_rect = (
                player.get_hitbox()
            )

            for obs in obstacles[:]:

                obs.update()

                # -----------------------------------------------
                # SPIKE
                # -----------------------------------------------

                if isinstance(
                    obs,
                    ObstacleSpike
                ):

                    if player_rect.colliderect(
                        obs.get_mask_rect()
                    ):

                        game_over = True

                        player_died()

                        break

                # -----------------------------------------------
                # JUMP PAD
                # -----------------------------------------------

                elif isinstance(
                    obs,
                    JumpPad
                ):

                    pad_rect = (
                        obs.get_rect()
                    )

                    if (
                        player_rect.colliderect(
                            pad_rect
                        )
                        and
                        player.velocity_y >= 0
                    ):

                        previous_bottom = (
                            player.y
                            + player.size
                            - 6
                            - player.velocity_y
                        )

                        if (
                            previous_bottom
                            <= pad_rect.top + 10
                        ):

                            player.y = (
                                pad_rect.top
                                - player.size
                                + 6
                            )

                            player.pad_jump(
                                particles
                            )

                            obs.activate()

                # -----------------------------------------------
                # BLOCK
                # -----------------------------------------------

                elif isinstance(
                    obs,
                    ObstacleBlock
                ):

                    block_rect = (
                        obs.get_rect()
                    )

                    if player_rect.colliderect(
                        block_rect
                    ):

                        # ----------------------------------------
                        # HEAD-ON LEFT-SIDE CRASH
                        # ----------------------------------------

                        if (
                            not player.is_grounded
                            and
                            player_rect.bottom
                            > block_rect.top + 12
                        ):

                            if (
                                player_rect.right
                                > block_rect.left
                                and
                                player_rect.left
                                < block_rect.left
                            ):

                                game_over = True

                                player_died()

                                break

                        # ----------------------------------------
                        # SIDE / BOTTOM CRASH
                        # ----------------------------------------

                        if not player.is_grounded:

                            if (
                                player_rect.bottom
                                > block_rect.top + 12
                            ):

                                if (
                                    player_rect.right
                                    > block_rect.left + 4
                                    and
                                    player_rect.left
                                    < block_rect.right - 4
                                ):

                                    game_over = True

                                    player_died()

                                    break

            # ====================================================
            # REMOVE OFFSCREEN OBJECTS
            # ====================================================

            for obs in obstacles[:]:

                if (
                    obs.x + obs.width
                    < 0
                ):

                    # Do not count spikes sitting
                    # on blocks as separate points.
                    if not (
                        isinstance(
                            obs,
                            ObstacleSpike
                        )
                        and
                        obs.y < GROUND_Y
                    ):

                        score += 1

                    obstacles.remove(obs)

        # ========================================================
        # DRAW
        # ========================================================

        screen.fill(
            BACKGROUND_COLOR
        )

        draw_scrolling_floor(
            screen,
            floor_scroll
        )

        # Particles
        for p in particles:

            p.draw(screen)

        # Player
        player.draw(screen)

        # Obstacles
        for obs in obstacles:

            obs.draw(screen)

        # ========================================================
        # SCORE
        # ========================================================

        score_text = font.render(
            f"SCORE: {score}",
            True,
            WHITE
        )

        screen.blit(
            score_text,
            (40, 40)
        )

        # ========================================================
        # ATTEMPT
        # ========================================================

        attempt_text = font.render(
            f"ATTEMPT: {attempt_count}",
            True,
            WHITE
        )

        screen.blit(
            attempt_text,
            (
                40,
                40 + int(
                    SCREEN_HEIGHT * 0.05
                )
            )
        )

        # ========================================================
        # GAME OVER
        # ========================================================

        if game_over:

            go_text = font.render(
                "CRASHED! Press 'R' to Restart",
                True,
                WHITE
            )

            esc_font = pygame.font.SysFont(
                "serif",
                int(
                    SCREEN_HEIGHT * 0.025
                )
            )

            esc_text = esc_font.render(
                "Press 'ESC' to Quit",
                True,
                WHITE
            )

            go_rect = go_text.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT // 2
                )
            )

            esc_rect = esc_text.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    SCREEN_HEIGHT // 2 + 50
                )
            )

            screen.blit(
                go_text,
                go_rect
            )

            screen.blit(
                esc_text,
                esc_rect
            )

        pygame.display.flip()

    return False


# ================================================================
# MAIN LOOP
# ================================================================

current_attempt = 1

while True:

    if run_game(current_attempt):

        current_attempt += 1