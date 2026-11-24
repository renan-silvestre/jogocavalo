import pygame
import math
import threading
import time
import random

WIDTH, HEIGHT = 480, 270   # mockup size
SCALE = 3                  # 1440x810 na tela
FINISH_LINE = 1500
podium = []
NOSE = 70   # distancia pra chegar no focinho do cavalo

pygame.init()
window = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
screen = pygame.Surface((WIDTH, HEIGHT))   # draw here, at the small size
clock = pygame.time.Clock()

background = pygame.image.load("sprites/fundo.png").convert()
body_img = pygame.image.load("sprites/corpo.png")
head_img = pygame.image.load("sprites/cabeca.png")
leg_img = pygame.image.load("sprites/perna.png")
neck_img = pygame.image.load("sprites/pescoco.png")
tail_img = pygame.image.load("sprites/rabo.png")

def blit_rotated(surf, img, pivot, origin, angle):  #gira a peça em torno do pivô
    # origin: that same point inside the image
    rect = img.get_rect(topleft=(pivot[0] - origin[0], pivot[1] - origin[1]))
    offset = pygame.math.Vector2(pivot) - rect.center
    rotated = pygame.transform.rotate(img, angle)
    new_center = pygame.math.Vector2(pivot) - offset.rotate(-angle)
    surf.blit(rotated, rotated.get_rect(center=new_center))
 
track_tile = background.subsurface((291, 0, 189, HEIGHT)) #pegar o fundo dps da linha inicial

start_gate = threading.Semaphore(0)   # portão fechado
podium_lock = threading.Semaphore(1)    #semáforo para só 1 cavalo alterar a lista do pódio por vez

class Horse:
    def __init__(self, number):
        self.number = number
        self.x = 184
        self.y = 7 + 40 * number
        self.speed = random.uniform(1.2, 1.6)

    def run(self):
        start_gate.acquire() # como é 0, a thread espera
        while self.x + NOSE < FINISH_LINE:
            self.x += self.speed * random.uniform(0.6, 1.4)
            time.sleep(1 / 60)
        podium_lock.acquire()   #semáforo do pódio
        podium.append(self)
        print(len(podium))
        podium_lock.release()   #se nunca liberasse seria um deadlock
        
            
horses = [Horse(1), Horse(2), Horse(3), Horse(4), Horse(5)]



for horse in horses:
    horse_thread = threading.Thread(target=horse.run, daemon=True) # threads, daemon pra thread acabar quando o programa acabar
    horse_thread.start()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                start_gate.release(5) #5 vagas para as 5 threads
            
        if event.type == pygame.QUIT:
            running = False
    
    camera_x = max(0, horses[0].x - 184)   # começa em 0 dps segue o cavalo
    finish_x = FINISH_LINE - camera_x


    screen.blit(background, (-camera_x, 0))
    x = WIDTH - camera_x    #repetir o fundo
    while x < WIDTH:
        screen.blit(track_tile, (x,0))
        x += track_tile.get_width()
    
    for y in range(62, HEIGHT, 4):  # linha de chegada xadrez (2 colunas de quadrados de 4 px)
        for column in range(2):
            if (y // 4 + column) % 2 == 0:
                color = (0, 0, 0)
            else:
                color = (255, 255, 255)
            pygame.draw.rect(screen, color, (finish_x + column * 4, y, 4, 4))
    
    pygame.draw.rect(screen, (143, 86, 59), (finish_x, 245, 8, 5))  #redesenhar a cerca


    
    for horse in horses:
        draw_x = horse.x - camera_x

        angle = math.sin(pygame.time.get_ticks() / (650/horse.speed)) * 15 * horse.speed
        
        # neck pivo
        neck_angle = angle - 30
        neck_pivot = pygame.math.Vector2(draw_x + 47, horse.y + 3)
        neck_tip = neck_pivot + pygame.math.Vector2(0, -15).rotate(-neck_angle)
        # leg pivo
        leg_angle = angle
        leg_pivot = pygame.math.Vector2(draw_x + 2, horse.y + 22)
    
        screen.blit(body_img, (draw_x, horse.y))
        screen.blit(leg_img, (draw_x, horse.y + 24))
        screen.blit(leg_img, (draw_x + 39, horse.y + 24))
        screen.blit(tail_img, (draw_x - 25, horse.y))
        blit_rotated(screen, neck_img, neck_pivot, (4, 15), neck_angle)
        blit_rotated(screen, head_img, neck_tip, (4, 11), neck_angle)
        
    
 
 
    # scale the small screen up to the window size, without blurring
    window.blit(pygame.transform.scale(screen, window.get_size()), (0, 0))
    pygame.display.flip()
    clock.tick(60)   # 60 fps

pygame.quit()