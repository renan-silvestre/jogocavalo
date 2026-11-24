import math
import random
import threading
import time

import pygame

WIDTH, HEIGHT = 480, 270   # mockup size
SCALE = 3                  # 1440x810 on screen

NUM_HORSES = 5
NAMES = ["CAVALO 1", "CAVALO 2", "CAVALO 3", "CAVALO 4", "CAVALO 5"]   # put your funny names here
COLORS = [(230, 57, 70), (40, 110, 200), (250, 200, 40), (140, 70, 170), (255, 255, 255)]
LANE_FEET_Y = [97, 137, 177, 217, 242]   # y where the hooves touch the ground, one per lane

START_X = 184              # body x at the start (same as the mockup)
NOSE = 83                  # distance from the body x to the tip of the nose
FINISH_LINE = 2600         # world x of the finish line
BOTTLENECK_START = 1200    # world x where the narrow part begins
BOTTLENECK_END = 1500      # world x where it ends
BOTTLENECK_SIZE = 2        # how many horses fit in the narrow part at the same time
STUMBLE_CHANCE = 0.002     # chance of stumbling on each step

BET = 10
PRIZE = 40

pygame.init()
window = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
pygame.display.set_caption("Jogo do Cavalo")
screen = pygame.Surface((WIDTH, HEIGHT))   # draw here, at the small size
clock = pygame.time.Clock()

font_tiny = pygame.font.Font(None, 15)
font_small = pygame.font.Font(None, 16)
font_big = pygame.font.Font(None, 48)

background = pygame.image.load("sprites/fundo.png").convert()
body_img = pygame.image.load("sprites/corpo.png").convert_alpha()
head_img = pygame.image.load("sprites/cabeca.png").convert_alpha()
leg_img = pygame.image.load("sprites/perna.png").convert_alpha()
neck_img = pygame.image.load("sprites/pescoco.png").convert_alpha()
tail_img = pygame.image.load("sprites/rabo.png").convert_alpha()

# darker copy of the leg, for the two legs on the far side of the horse
leg_dark = leg_img.copy()
leg_dark.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_MULT)

# the part of the track after the white line, repeated forever to the right.
# it starts at x 291 and is 189 wide (3 x 63, the space between fence posts),
# so the fence posts line up where two pieces meet.
TILE_W = 189
track_tile = background.subsurface((291, 0, TILE_W, HEIGHT))

# each horse is drawn on its own small surface first, then that surface is put on the screen
HORSE_SURF_SIZE = (150, 110)
BODY_POS = (35, 35)        # where the body goes inside that surface


def blit_rotated(surf, img, pivot, origin, angle):
    # pivot: point on the screen where the piece is attached
    # origin: that same point inside the image
    rect = img.get_rect(topleft=(pivot[0] - origin[0], pivot[1] - origin[1]))
    offset = pygame.math.Vector2(pivot) - rect.center
    rotated = pygame.transform.rotate(img, angle)
    new_center = pygame.math.Vector2(pivot) - offset.rotate(-angle)
    surf.blit(rotated, rotated.get_rect(center=new_center))


def draw_text(text, font, color, center):
    shadow = font.render(text, False, (0, 0, 0))
    image = font.render(text, False, color)
    rect = image.get_rect(center=center)
    screen.blit(shadow, rect.move(1, 1))
    screen.blit(image, rect)


class Horse:
    def __init__(self, number):
        self.number = number
        self.name = NAMES[number - 1]
        self.color = COLORS[number - 1]
        self.feet_y = LANE_FEET_Y[number - 1]
        self.x = START_X
        self.speed = random.uniform(1.2, 1.6)
        self.zone = "before"       # "before", "inside" or "after" the bottleneck
        self.waiting = False       # True while waiting in line for the bottleneck
        self.stumbling = False

    def run(self):
        # this runs in the horse's own thread. it only changes the horse's data,
        # the main thread is the one that draws.
        start_gate.acquire()       # wait here until "VAI!"

        while self.x + NOSE < FINISH_LINE:
            nose = self.x + NOSE

            if self.zone == "before" and nose >= BOTTLENECK_START:
                self.waiting = True
                bottleneck.acquire()       # blocks if 2 horses are already inside
                self.waiting = False
                self.zone = "inside"
            elif self.zone == "inside" and nose >= BOTTLENECK_END:
                bottleneck.release()       # free a spot for the next horse in line
                self.zone = "after"

            if random.random() < STUMBLE_CHANCE:
                self.stumbling = True
                time.sleep(random.uniform(0.5, 1.0))
                self.stumbling = False

            self.x += self.speed * random.uniform(0.6, 1.4)
            time.sleep(1 / 60)

        podium_lock.acquire()      # only one horse at a time touches the podium list
        podium.append(self)
        podium_lock.release()


def new_race():
    global horses, podium, start_gate, podium_lock, bottleneck
    horses = [Horse(number) for number in range(1, NUM_HORSES + 1)]
    podium = []
    start_gate = threading.Semaphore(0)                  # starts closed
    podium_lock = threading.Semaphore(1)                 # one at a time
    bottleneck = threading.Semaphore(BOTTLENECK_SIZE)    # two at a time


def draw_horse(horse):
    surf = pygame.Surface(HORSE_SURF_SIZE, pygame.SRCALPHA)
    bx, by = BODY_POS

    # the animation uses the distance run, not the time,
    # so the legs stop when the horse stops (waiting in line or stumbling)
    run = horse.x / 6
    swing = math.sin(run) * 25

    # far side legs, behind everything
    blit_rotated(surf, leg_dark, (bx + 8, by + 22), (4, 0), -swing)
    blit_rotated(surf, leg_dark, (bx + 40, by + 22), (4, 0), swing)

    blit_rotated(surf, tail_img, (bx - 2, by + 2), (23, 2), math.sin(run / 2) * 10)

    # near side legs
    blit_rotated(surf, leg_img, (bx + 4, by + 22), (4, 0), swing)
    blit_rotated(surf, leg_img, (bx + 43, by + 22), (4, 0), -swing)

    # body, with a colored cloth and the horse's number
    surf.blit(body_img, (bx, by))
    pygame.draw.rect(surf, horse.color, (bx + 14, by + 3, 16, 12))
    number = font_tiny.render(str(horse.number), False, (0, 0, 0))
    surf.blit(number, number.get_rect(center=(bx + 22, by + 9)))

    # neck and head (same idea as main.py)
    neck_angle = -30 + math.sin(run / 2) * 10
    neck_pivot = pygame.math.Vector2(bx + 47, by + 3)
    neck_tip = neck_pivot + pygame.math.Vector2(0, -15).rotate(-neck_angle)
    blit_rotated(surf, neck_img, neck_pivot, (4, 15), neck_angle)
    blit_rotated(surf, head_img, neck_tip, (4, 11), neck_angle)

    return surf


def draw_horse_on_screen(horse, camera_x):
    surf = draw_horse(horse)
    # the front hooves are the pivot, so a stumble tips the horse forward
    hooves = (horse.x - camera_x + 43, horse.feet_y)
    hooves_in_surf = (BODY_POS[0] + 43, BODY_POS[1] + 47)
    tilt = -25 if horse.stumbling else 0
    blit_rotated(screen, surf, hooves, hooves_in_surf, tilt)


def draw_track(camera_x):
    screen.blit(background, (-camera_x, 0))
    x = WIDTH - camera_x
    while x < WIDTH:
        screen.blit(track_tile, (x, 0))
        x += TILE_W


def draw_bottleneck(camera_x):
    left = BOTTLENECK_START - camera_x
    width = BOTTLENECK_END - BOTTLENECK_START

    shade = pygame.Surface((width, 183), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 60))
    screen.blit(shade, (left, 62))
    pygame.draw.rect(screen, (220, 40, 40), (left, 62, 3, 183))
    pygame.draw.rect(screen, (220, 40, 40), (left + width - 3, 62, 3, 183))

    inside = sum(1 for horse in horses if horse.zone == "inside")
    in_line = sum(1 for horse in horses if horse.waiting)
    color = (255, 80, 80) if inside == BOTTLENECK_SIZE else (255, 255, 255)
    # keep the sign over the part of the zone that is on the screen
    sign_x = (max(left, 0) + min(left + width, WIDTH)) // 2
    sign_x = max(50, min(sign_x, WIDTH - 50))
    if left + width > 0 and left < WIDTH:
        draw_text(f"GARGALO {inside}/{BOTTLENECK_SIZE}", font_small, color, (sign_x, 30))
        if in_line > 0:
            draw_text(f"FILA: {in_line}", font_small, (255, 255, 255), (sign_x, 46))


def draw_finish_line(camera_x):
    x = FINISH_LINE - camera_x
    for y in range(62, 245, 4):
        for column in range(2):
            color = (0, 0, 0) if (y // 4 + column) % 2 == 0 else (255, 255, 255)
            pygame.draw.rect(screen, color, (x + column * 4, y, 4, 4))


def draw_progress_bar():
    # a small map of the race at the top: one dot per horse
    left, right, y = 10, WIDTH - 10, 6
    total = FINISH_LINE - (START_X + NOSE)

    def to_bar(world_x):
        return left + (right - left) * (world_x - (START_X + NOSE)) / total

    pygame.draw.line(screen, (255, 255, 255), (left, y), (right, y))
    pygame.draw.line(screen, (220, 40, 40), (to_bar(BOTTLENECK_START), y), (to_bar(BOTTLENECK_END), y), 3)
    for horse in horses:
        dot_x = min(to_bar(horse.x + NOSE), right)
        pygame.draw.circle(screen, horse.color, (dot_x, y), 3)


new_race()
money = 100
chosen = 1
state = "bet"              # "bet", "countdown", "race" or "podium"
countdown_start = 0
go_time = 0
camera_x = 0
result_text = ""

running = True
while running:
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if state == "bet":
                if pygame.K_1 <= event.key <= pygame.K_5:
                    chosen = event.key - pygame.K_0
                elif event.key == pygame.K_RETURN:
                    money -= BET
                    # the threads start now, but they all stop at start_gate.acquire()
                    for horse in horses:
                        threading.Thread(target=horse.run, daemon=True).start()
                    countdown_start = now
                    state = "countdown"
            elif state == "podium" and event.key == pygame.K_RETURN:
                new_race()
                camera_x = 0
                state = "bet"

    # update
    if state == "countdown":
        seconds_left = 3 - (now - countdown_start) // 700
        if seconds_left <= 0:
            start_gate.release(NUM_HORSES)    # "VAI!": opens the gate for every horse at once
            go_time = now
            state = "race"
    elif state == "race":
        # the camera follows the horse you bet on
        followed_x = horses[chosen - 1].x
        camera_x = min(max(0, followed_x - 200), FINISH_LINE + 60 - WIDTH)

        podium_lock.acquire()
        finished = len(podium)
        podium_lock.release()

        if finished == NUM_HORSES:
            if podium[0].number == chosen:
                money += BET + PRIZE
                result_text = f"VOCÊ GANHOU ${PRIZE}!"
            else:
                result_text = f"VOCÊ PERDEU ${BET}"
            state = "podium"

    # draw
    cam = int(camera_x)
    draw_track(cam)
    draw_bottleneck(cam)
    draw_finish_line(cam)
    for horse in horses:           # top lane first, so lower horses stay in front
        draw_horse_on_screen(horse, cam)

    if state == "bet":
        draw_text("FAÇA SUA APOSTA", font_small, (255, 255, 255), (365, 14))
        draw_text("TECLAS 1-5 E ENTER", font_small, (255, 255, 255), (365, 30))
        draw_text(f"DINHEIRO: ${money}   APOSTA: ${BET}", font_small, (255, 255, 0), (365, 46))
        for horse in horses:
            draw_text(f"{horse.number} {horse.name}", font_small, horse.color, (60, horse.feet_y - 20))
        chosen_horse = horses[chosen - 1]
        draw_text(">", font_big, (255, 255, 0), (145, chosen_horse.feet_y - 25))

    elif state == "countdown":
        seconds_left = 3 - (now - countdown_start) // 700
        draw_text(str(seconds_left), font_big, (255, 255, 255), (WIDTH // 2, HEIGHT // 2))

    elif state == "race":
        draw_progress_bar()
        draw_text(f"SUA APOSTA: {NAMES[chosen - 1]}", font_small, (255, 255, 0), (WIDTH - 75, 16))
        if now - go_time < 700:
            draw_text("VAI!", font_big, (255, 255, 0), (WIDTH // 2, HEIGHT // 2))

    elif state == "podium":
        dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 150))
        screen.blit(dark, (0, 0))
        draw_text("PÓDIO", font_big, (255, 255, 0), (WIDTH // 2, 50))
        for place in range(3):
            horse = podium[place]
            draw_text(f"{place + 1}º  {horse.name}", font_small, horse.color, (WIDTH // 2, 95 + place * 22))
        draw_text(result_text, font_small, (255, 255, 255), (WIDTH // 2, 180))
        draw_text(f"DINHEIRO: ${money}", font_small, (255, 255, 0), (WIDTH // 2, 200))
        draw_text("ENTER: NOVA CORRIDA", font_small, (255, 255, 255), (WIDTH // 2, 230))

    # scale the small screen up to the window size, without blurring
    window.blit(pygame.transform.scale(screen, window.get_size()), (0, 0))
    pygame.display.flip()
    clock.tick(60)   # 60 frames per second

pygame.quit()
