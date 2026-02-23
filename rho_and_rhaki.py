"""
Rho and Rhaki's Crazy Adventure!
A snow day game where two brothers search a house to find their parents.
When they find a parent, they twerk — and it actually hurts the parents!
Find both parents to win!
"""

import pygame
import sys
import random
import math

# ---------------------------------------------------------------------------
# Initialise
# ---------------------------------------------------------------------------
pygame.init()

WIDTH, HEIGHT = 960, 640
TILE = 32
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rho & Rhaki's Crazy Adventure!")
clock = pygame.time.Clock()
FPS = 60

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
SNOW_BG     = (220, 230, 245)
WALL_COL    = (90, 70, 55)
FLOOR_COL   = (200, 185, 160)
DOOR_COL    = (140, 100, 60)
RHO_COL     = (50, 140, 255)   # blue hoodie
RHAKI_COL   = (255, 80, 80)    # red hoodie
MOM_COL     = (180, 50, 180)
DAD_COL     = (50, 160, 80)
FURNITURE   = (120, 100, 80)
SNOW_COL    = (240, 245, 255)
WINDOW_COL  = (180, 210, 240)
HP_RED      = (220, 40, 40)
HP_GREEN    = (40, 200, 40)
YELLOW      = (255, 220, 0)
TWERK_COL   = (255, 180, 50)

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
font_big   = pygame.font.SysFont("arial", 36, bold=True)
font_med   = pygame.font.SysFont("arial", 22, bold=True)
font_small = pygame.font.SysFont("arial", 16)
font_tiny  = pygame.font.SysFont("arial", 13)

# ---------------------------------------------------------------------------
# House layout  (30 x 20 tiles)
# '#' = wall, '.' = floor, 'D' = door, 'W' = window, 'F' = furniture
# ---------------------------------------------------------------------------
HOUSE_MAP = [
    "##############################",
    "#......#......#..............#",
    "#......#......#..............#",
    "#..F...#..F...#.....F........#",
    "#......#......#..............#",
    "#......D......D..............#",
    "####D########D####..........##",
    "#..............#.............#",
    "#..............#.............#",
    "#.....F........#.....F.......#",
    "#..............#.............#",
    "#..............#.............#",
    "#..............D.............#",
    "####D#########D###############",
    "#..............#.............#",
    "#..............#.............#",
    "#.....F........#......F......#",
    "#..............#.............#",
    "#..............#.............#",
    "##############################",
]

ROWS = len(HOUSE_MAP)
COLS = len(HOUSE_MAP[0])

# Camera offset to centre the map
CAM_X = (WIDTH  - COLS * TILE) // 2
CAM_Y = (HEIGHT - ROWS * TILE) // 2

def tile_rect(c, r):
    return pygame.Rect(CAM_X + c * TILE, CAM_Y + r * TILE, TILE, TILE)

def is_wall(c, r):
    if 0 <= r < ROWS and 0 <= c < COLS:
        return HOUSE_MAP[r][c] == '#'
    return True

def is_blocked(c, r):
    if 0 <= r < ROWS and 0 <= c < COLS:
        ch = HOUSE_MAP[r][c]
        return ch == '#' or ch == 'F'
    return True

# ---------------------------------------------------------------------------
# Room names (for flavour text)
# ---------------------------------------------------------------------------
def room_name(c, r):
    if r < 6:
        if c < 7:
            return "Kitchen"
        elif c < 14:
            return "Dining Room"
        else:
            return "Living Room"
    elif r < 13:
        if c < 15:
            return "Hallway"
        else:
            return "Study"
    else:
        if c < 15:
            return "Bedroom"
        else:
            return "Playroom"

# ---------------------------------------------------------------------------
# Snow particles (visible through windows / title screen)
# ---------------------------------------------------------------------------
snowflakes = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT),
               "s": random.uniform(1, 3), "dx": random.uniform(-0.5, 0.5)}
              for _ in range(120)]

def update_snow():
    for s in snowflakes:
        s["y"] += s["s"]
        s["x"] += s["dx"]
        if s["y"] > HEIGHT:
            s["y"] = -2
            s["x"] = random.randint(0, WIDTH)

def draw_snow():
    for s in snowflakes:
        r = max(1, int(s["s"]))
        pygame.draw.circle(screen, WHITE, (int(s["x"]), int(s["y"])), r)

# ---------------------------------------------------------------------------
# Draw the house
# ---------------------------------------------------------------------------
def draw_house():
    for r in range(ROWS):
        for c in range(COLS):
            rect = tile_rect(c, r)
            ch = HOUSE_MAP[r][c]
            if ch == '#':
                pygame.draw.rect(screen, WALL_COL, rect)
                # tiny brick pattern
                if (r + c) % 2 == 0:
                    pygame.draw.rect(screen, (100, 80, 65), rect, 1)
            elif ch == 'D':
                pygame.draw.rect(screen, FLOOR_COL, rect)
                pygame.draw.rect(screen, DOOR_COL, rect.inflate(-8, -4))
            elif ch == 'W':
                pygame.draw.rect(screen, FLOOR_COL, rect)
                pygame.draw.rect(screen, WINDOW_COL, rect.inflate(-6, -6))
            elif ch == 'F':
                pygame.draw.rect(screen, FLOOR_COL, rect)
                pygame.draw.rect(screen, FURNITURE, rect.inflate(-4, -4))
                pygame.draw.rect(screen, (100, 80, 60), rect.inflate(-4, -4), 1)
            else:
                pygame.draw.rect(screen, FLOOR_COL, rect)

# ---------------------------------------------------------------------------
# Character class
# ---------------------------------------------------------------------------
class Character:
    def __init__(self, col, row, colour, name):
        self.col = col
        self.row = row
        self.colour = colour
        self.name = name
        self.move_timer = 0
        self.twerking = False
        self.twerk_frame = 0
        self.twerk_timer = 0
        self.facing = "down"

    @property
    def px(self):
        return CAM_X + self.col * TILE + TILE // 2

    @property
    def py(self):
        return CAM_Y + self.row * TILE + TILE // 2

    def try_move(self, dc, dr):
        nc, nr = self.col + dc, self.row + dr
        if not is_blocked(nc, nr):
            self.col = nc
            self.row = nr
            if dc < 0: self.facing = "left"
            elif dc > 0: self.facing = "right"
            elif dr < 0: self.facing = "up"
            else: self.facing = "down"
            return True
        return False

    def draw(self, t):
        x, y = self.px, self.py
        # Body
        body_rect = pygame.Rect(x - 10, y - 10, 20, 20)
        if self.twerking:
            # Wobble the body for twerk animation
            wobble = int(math.sin(self.twerk_frame * 1.5) * 4)
            body_rect.x += wobble
            # Draw twerk impact lines
            for i in range(3):
                angle = self.twerk_frame * 0.8 + i * 2.1
                lx = x + int(math.cos(angle) * 18)
                ly = y + int(math.sin(angle) * 18)
                pygame.draw.circle(screen, TWERK_COL, (lx, ly), 3)
        pygame.draw.rect(screen, self.colour, body_rect, border_radius=6)
        # Head
        head_y = y - 16
        pygame.draw.circle(screen, (240, 200, 160), (x, head_y), 7)
        # Eyes
        ex_off = -3 if self.facing == "left" else 3 if self.facing == "right" else 0
        ey_off = -2 if self.facing == "up" else 2 if self.facing == "down" else 0
        pygame.draw.circle(screen, BLACK, (x - 2 + ex_off, head_y - 1 + ey_off), 1)
        pygame.draw.circle(screen, BLACK, (x + 2 + ex_off, head_y - 1 + ey_off), 1)
        # Name tag
        tag = font_tiny.render(self.name, True, self.colour)
        screen.blit(tag, (x - tag.get_width() // 2, y + 12))

# ---------------------------------------------------------------------------
# Parent class  (hides in a room, has HP)
# ---------------------------------------------------------------------------
class Parent:
    def __init__(self, col, row, colour, name):
        self.col = col
        self.row = row
        self.colour = colour
        self.name = name
        self.hp = 100
        self.found = False
        self.defeated = False
        self.shake = 0
        self.speech = ""
        self.speech_timer = 0
        # Work items floating above
        self.work_text = "TAP TAP TAP..." if name == "Dad" else "TYPE TYPE TYPE..."

    @property
    def px(self):
        return CAM_X + self.col * TILE + TILE // 2

    @property
    def py(self):
        return CAM_Y + self.row * TILE + TILE // 2

    def say(self, text):
        self.speech = text
        self.speech_timer = 180  # 3 seconds

    def draw(self, t):
        if not self.found:
            return
        x, y = self.px, self.py
        # Shake if being twerked at
        sx = 0
        if self.shake > 0:
            sx = int(math.sin(self.shake * 2) * 3)
            self.shake -= 1
        # Body (sitting at desk)
        desk = pygame.Rect(x - 14 + sx, y + 2, 28, 10)
        pygame.draw.rect(screen, FURNITURE, desk)
        body_rect = pygame.Rect(x - 10 + sx, y - 12, 20, 18)
        pygame.draw.rect(screen, self.colour, body_rect, border_radius=5)
        # Head
        pygame.draw.circle(screen, (240, 200, 160), (x + sx, y - 18), 8)
        # Glasses for Dad / hair for Mom
        if self.name == "Dad":
            pygame.draw.circle(screen, BLACK, (x - 3 + sx, y - 19), 4, 1)
            pygame.draw.circle(screen, BLACK, (x + 3 + sx, y - 19), 4, 1)
        else:
            for i in range(-6, 7, 2):
                pygame.draw.line(screen, (60, 30, 20),
                                 (x + i + sx, y - 26), (x + i + sx, y - 20), 1)
        # HP bar
        bar_w = 30
        bar_rect = pygame.Rect(x - bar_w // 2, y - 32, bar_w, 5)
        pygame.draw.rect(screen, HP_RED, bar_rect)
        green_w = max(0, int(bar_w * self.hp / 100))
        pygame.draw.rect(screen, HP_GREEN, (bar_rect.x, bar_rect.y, green_w, 5))
        pygame.draw.rect(screen, BLACK, bar_rect, 1)
        # Name
        tag = font_tiny.render(self.name, True, self.colour)
        screen.blit(tag, (x - tag.get_width() // 2, y + 14))
        # Work text
        if self.hp > 0:
            work = font_tiny.render(self.work_text, True, (100, 100, 100))
            screen.blit(work, (x - work.get_width() // 2, y - 42))
        # Speech bubble
        if self.speech_timer > 0:
            self.speech_timer -= 1
            bubble = font_small.render(self.speech, True, BLACK)
            bx = x - bubble.get_width() // 2
            by = y - 58
            bg = pygame.Rect(bx - 4, by - 2, bubble.get_width() + 8, bubble.get_height() + 4)
            pygame.draw.rect(screen, WHITE, bg, border_radius=4)
            pygame.draw.rect(screen, BLACK, bg, 1, border_radius=4)
            screen.blit(bubble, (bx, by))

# ---------------------------------------------------------------------------
# Twerk damage effect
# ---------------------------------------------------------------------------
class TwerkEffect:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text
        self.life = 60
        self.start_y = y

    def update(self):
        self.life -= 1
        self.y -= 1

    def draw(self):
        alpha = max(0, min(255, self.life * 8))
        col = (255, max(0, 100 - (60 - self.life) * 3), 0)
        surf = font_med.render(self.text, True, col)
        screen.blit(surf, (self.x - surf.get_width() // 2, int(self.y)))

# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
STATE_TITLE  = 0
STATE_PLAY   = 1
STATE_WIN    = 2

state = STATE_TITLE

# Place characters
rho   = Character(2, 8, RHO_COL, "Rho")
rhaki = Character(3, 8, RHAKI_COL, "Rhaki")

# Parents hide in rooms — they appear once a kid gets close
# Dad in the Study, Mom in the Bedroom
dad = Parent(22, 9, DAD_COL, "Dad")
mom = Parent(5, 16, MOM_COL, "Mom")

effects = []

PARENT_LINES_HURT = [
    "Ow! Stop twerking!",
    "I'm on a Zoom call!",
    "Not now, kids!",
    "My back! Owww!",
    "Go play in the snow!",
    "I have a deadline!",
    "That's... my spine!",
    "Why are you like this?!",
    "HR is watching!",
    "This is NOT a dance floor!",
]

PARENT_DEFEAT = [
    "Fine! I'll play with you!",
    "Okay okay, you win!",
    "Alright, snow day it is!",
]

move_cooldown_rho = 0
move_cooldown_rhaki = 0
MOVE_DELAY = 8  # frames between moves

message = ""
message_timer = 0

parents_defeated = 0
victory_timer = 0

twerk_instructions_shown = False

def set_message(text, duration=180):
    global message, message_timer
    message = text
    message_timer = duration

def do_twerk(kid, parent):
    """Kid twerks at a parent — deals damage!"""
    kid.twerking = True
    kid.twerk_timer = 45
    kid.twerk_frame = 0
    dmg = random.randint(8, 15)
    parent.hp -= dmg
    parent.shake = 20
    parent.say(random.choice(PARENT_LINES_HURT))
    effects.append(TwerkEffect(parent.px, parent.py - 40, f"-{dmg} TWERK!"))
    if parent.hp <= 0:
        parent.hp = 0
        return True
    return False

def check_parent_nearby(kid, parent):
    """Check if kid is adjacent to parent."""
    dc = abs(kid.col - parent.col)
    dr = abs(kid.row - parent.row)
    return dc <= 1 and dr <= 1

def reveal_parents():
    """Reveal parents if any kid gets within 3 tiles."""
    for parent in [dad, mom]:
        if parent.found:
            continue
        for kid in [rho, rhaki]:
            dc = abs(kid.col - parent.col)
            dr = abs(kid.row - parent.row)
            if dc <= 3 and dr <= 3:
                parent.found = True
                set_message(f"Found {parent.name}! Get close and press TWERK!", 180)

# ---------------------------------------------------------------------------
# Title screen
# ---------------------------------------------------------------------------
title_blink = 0

def draw_title():
    global title_blink
    screen.fill((30, 30, 60))
    draw_snow()

    # Title
    t1 = font_big.render("Rho & Rhaki's", True, YELLOW)
    t2 = font_big.render("CRAZY ADVENTURE!", True, WHITE)
    screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, 120))
    screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 165))

    # Subtitle
    sub = font_med.render("~ A Snow Day Twerk-a-thon ~", True, (180, 200, 255))
    screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 220))

    # Instructions
    lines = [
        "It's a SNOW DAY! But Mom and Dad are trying to work...",
        "Find them in the house and TWERK until they give up!",
        "",
        "Rho:   WASD to move,  Q to TWERK",
        "Rhaki: Arrow keys to move,  SPACE to TWERK",
        "",
        "Get next to a parent and twerk to deal damage!",
        "Defeat both parents to win the snow day!",
    ]
    for i, line in enumerate(lines):
        col = (200, 210, 230) if i != 1 else TWERK_COL
        t = font_small.render(line, True, col)
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 290 + i * 26))

    # Blink
    title_blink += 1
    if (title_blink // 30) % 2 == 0:
        start = font_med.render("Press ENTER to start!", True, YELLOW)
        screen.blit(start, (WIDTH // 2 - start.get_width() // 2, 540))

    # Draw the two kids on title
    rho_x, rho_y = 340, 560
    rhaki_x, rhaki_y = 600, 560
    # Mini characters
    pygame.draw.rect(screen, RHO_COL, (rho_x - 8, rho_y - 8, 16, 16), border_radius=4)
    pygame.draw.circle(screen, (240, 200, 160), (rho_x, rho_y - 14), 6)
    t = font_tiny.render("Rho", True, RHO_COL)
    screen.blit(t, (rho_x - t.get_width() // 2, rho_y + 10))

    pygame.draw.rect(screen, RHAKI_COL, (rhaki_x - 8, rhaki_y - 8, 16, 16), border_radius=4)
    pygame.draw.circle(screen, (240, 200, 160), (rhaki_x, rhaki_y - 14), 6)
    t = font_tiny.render("Rhaki", True, RHAKI_COL)
    screen.blit(t, (rhaki_x - t.get_width() // 2, rhaki_y + 10))

# ---------------------------------------------------------------------------
# Victory screen
# ---------------------------------------------------------------------------
def draw_victory():
    screen.fill((30, 30, 60))
    draw_snow()

    t1 = font_big.render("SNOW DAY VICTORY!", True, YELLOW)
    screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, 150))

    lines = [
        "Rho and Rhaki's twerking was too powerful!",
        "Mom and Dad gave up on work.",
        "Everyone went outside to play in the snow!",
        "",
        "The family had hot chocolate afterwards.",
    ]
    for i, line in enumerate(lines):
        t = font_small.render(line, True, WHITE)
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 240 + i * 30))

    # Draw family together
    family_y = 430
    for i, (col, name) in enumerate([
        (RHO_COL, "Rho"), (RHAKI_COL, "Rhaki"),
        (MOM_COL, "Mom"), (DAD_COL, "Dad")
    ]):
        fx = 350 + i * 80
        pygame.draw.rect(screen, col, (fx - 10, family_y - 10, 20, 20), border_radius=5)
        pygame.draw.circle(screen, (240, 200, 160), (fx, family_y - 16), 7)
        tag = font_tiny.render(name, True, col)
        screen.blit(tag, (fx - tag.get_width() // 2, family_y + 14))

    t = font_med.render("Press ENTER to play again!", True, (180, 200, 255))
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 530))

# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
def draw_hud():
    # Room name
    rname = room_name(rho.col, rho.row)
    rt = font_small.render(f"Room: {rname}", True, WHITE)
    pygame.draw.rect(screen, (0, 0, 0, 180), (8, 8, rt.get_width() + 16, 28), border_radius=4)
    screen.blit(rt, (16, 12))

    # Parent status
    y = 44
    for p in [dad, mom]:
        status = "DEFEATED!" if p.defeated else f"HP: {p.hp}/100" if p.found else "???"
        col = HP_RED if p.defeated else HP_GREEN if p.found else (150, 150, 150)
        pt = font_small.render(f"{p.name}: {status}", True, col)
        pygame.draw.rect(screen, (0, 0, 0, 180), (8, y, pt.get_width() + 16, 24), border_radius=4)
        screen.blit(pt, (16, y + 3))
        y += 28

    # Controls reminder
    ctrl_lines = [
        "Rho: WASD + Q(twerk)",
        "Rhaki: Arrows + Space(twerk)",
    ]
    cy = HEIGHT - 56
    for line in ctrl_lines:
        ct = font_tiny.render(line, True, (180, 180, 180))
        pygame.draw.rect(screen, (0, 0, 0, 180),
                         (WIDTH - ct.get_width() - 20, cy, ct.get_width() + 12, 20),
                         border_radius=3)
        screen.blit(ct, (WIDTH - ct.get_width() - 14, cy + 2))
        cy += 22

    # Message
    if message_timer > 0:
        mt = font_med.render(message, True, YELLOW)
        mx = WIDTH // 2 - mt.get_width() // 2
        my = HEIGHT - 40
        bg = pygame.Rect(mx - 8, my - 4, mt.get_width() + 16, mt.get_height() + 8)
        pygame.draw.rect(screen, (0, 0, 0), bg, border_radius=6)
        screen.blit(mt, (mx, my))

# ---------------------------------------------------------------------------
# Reset game
# ---------------------------------------------------------------------------
def reset_game():
    global state, parents_defeated, victory_timer, message, message_timer
    global twerk_instructions_shown, effects
    rho.col, rho.row = 2, 8
    rhaki.col, rhaki.row = 3, 8
    dad.hp, dad.found, dad.defeated = 100, False, False
    mom.hp, mom.found, mom.defeated = 100, False, False
    dad.speech_timer = 0
    mom.speech_timer = 0
    parents_defeated = 0
    victory_timer = 0
    effects = []
    twerk_instructions_shown = False
    set_message("Find Mom and Dad in the house!", 180)
    state = STATE_PLAY

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if state == STATE_TITLE and event.key == pygame.K_RETURN:
                reset_game()
            elif state == STATE_WIN and event.key == pygame.K_RETURN:
                state = STATE_TITLE

    keys = pygame.key.get_pressed()

    if state == STATE_TITLE:
        update_snow()
        draw_title()

    elif state == STATE_PLAY:
        update_snow()

        # --- Movement ---
        if move_cooldown_rho > 0:
            move_cooldown_rho -= 1
        if move_cooldown_rhaki > 0:
            move_cooldown_rhaki -= 1

        # Rho: WASD
        if move_cooldown_rho == 0:
            moved = False
            if keys[pygame.K_w]:
                moved = rho.try_move(0, -1)
            elif keys[pygame.K_s]:
                moved = rho.try_move(0, 1)
            elif keys[pygame.K_a]:
                moved = rho.try_move(-1, 0)
            elif keys[pygame.K_d]:
                moved = rho.try_move(1, 0)
            if moved:
                move_cooldown_rho = MOVE_DELAY

        # Rhaki: Arrows
        if move_cooldown_rhaki == 0:
            moved = False
            if keys[pygame.K_UP]:
                moved = rhaki.try_move(0, -1)
            elif keys[pygame.K_DOWN]:
                moved = rhaki.try_move(0, 1)
            elif keys[pygame.K_LEFT]:
                moved = rhaki.try_move(-1, 0)
            elif keys[pygame.K_RIGHT]:
                moved = rhaki.try_move(1, 0)
            if moved:
                move_cooldown_rhaki = MOVE_DELAY

        # --- Twerking ---
        # Rho twerks with Q
        if keys[pygame.K_q] and not rho.twerking:
            for parent in [dad, mom]:
                if parent.found and not parent.defeated and check_parent_nearby(rho, parent):
                    defeated = do_twerk(rho, parent)
                    if defeated:
                        parent.defeated = True
                        parent.say(random.choice(PARENT_DEFEAT))
                        parents_defeated += 1
                        effects.append(TwerkEffect(parent.px, parent.py - 50, "K.O.!!"))
                        if parents_defeated >= 2:
                            set_message("BOTH PARENTS DEFEATED! SNOW DAY WINS!", 240)
                            victory_timer = 180

        # Rhaki twerks with SPACE
        if keys[pygame.K_SPACE] and not rhaki.twerking:
            for parent in [dad, mom]:
                if parent.found and not parent.defeated and check_parent_nearby(rhaki, parent):
                    defeated = do_twerk(rhaki, parent)
                    if defeated:
                        parent.defeated = True
                        parent.say(random.choice(PARENT_DEFEAT))
                        parents_defeated += 1
                        effects.append(TwerkEffect(parent.px, parent.py - 50, "K.O.!!"))
                        if parents_defeated >= 2:
                            set_message("BOTH PARENTS DEFEATED! SNOW DAY WINS!", 240)
                            victory_timer = 180

        # Update twerk animations
        for kid in [rho, rhaki]:
            if kid.twerking:
                kid.twerk_frame += 1
                kid.twerk_timer -= 1
                if kid.twerk_timer <= 0:
                    kid.twerking = False

        # Reveal parents
        reveal_parents()

        # Show twerk instructions when parent first found
        if not twerk_instructions_shown:
            if dad.found or mom.found:
                twerk_instructions_shown = True

        # Effects
        for e in effects[:]:
            e.update()
            if e.life <= 0:
                effects.remove(e)

        # Message timer
        if message_timer > 0:
            message_timer -= 1

        # Victory transition
        if victory_timer > 0:
            victory_timer -= 1
            if victory_timer == 0 and parents_defeated >= 2:
                state = STATE_WIN

        # --- Drawing ---
        screen.fill(SNOW_BG)

        # Draw snow outside the house
        draw_snow()

        # Draw house
        draw_house()

        # Draw parents
        tick = pygame.time.get_ticks()
        dad.draw(tick)
        mom.draw(tick)

        # Draw kids
        rho.draw(tick)
        rhaki.draw(tick)

        # Draw effects
        for e in effects:
            e.draw()

        # Draw HUD
        draw_hud()

    elif state == STATE_WIN:
        update_snow()
        draw_victory()

    pygame.display.flip()

pygame.quit()
sys.exit()
