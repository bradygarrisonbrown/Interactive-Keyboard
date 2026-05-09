import pygame
import random
import time


def vibrate_key(key_pressed):
    print(key_pressed)

pygame.init()
screen = pygame.display.set_mode((800, 400))
font = pygame.font.SysFont("Arial", 60)

letters = list("asdfjkl;")
current_letter = random.choice(letters)
start_time = time.time()

running = True

while running:
    screen.fill((20, 20, 20))

    # Draw target letter
    text = font.render(current_letter.upper(), True, (255, 255, 255))
    screen.blit(text, (350, 150))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            key = pygame.key.name(event.key)

            if key == current_letter:
                print("Correct")
                current_letter = random.choice(letters)
                start_time = time.time()
                vibrate_key(current_letter)  # your hardware call
            else:
                print("Wrong")

    pygame.display.flip()

pygame.quit()