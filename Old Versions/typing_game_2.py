import pygame
import random
import time
import os


def vibrate_key(key_pressed):
    print(key_pressed)

def layout_text(text, font, max_width, start_x, start_y, line_spacing=5):
    positions = []  # [(char, x, y), ...]

    x = start_x
    y = start_y

    words = text.split(" ")

    for word in words:
        word_surface = font.render(word, True, (255, 255, 255))
        space_surface = font.render(" ", True, (255, 255, 255))

        word_width = word_surface.get_width()

        # Wrap line if needed
        if x + word_width > max_width:
            x = start_x
            y += font.get_height() + line_spacing

        # Place each character in the word
        for char in word:
            char_surface = font.render(char, True, (255, 255, 255))
            positions.append((char, x, y))
            x += char_surface.get_width()

        # Add space
        positions.append((" ", x, y))
        x += space_surface.get_width()

    return positions

pygame.init()
screen = pygame.display.set_mode((800, 400))
font = pygame.font.SysFont("Arial", 20)


directory = "Books"

# Get a list of files in the directory
# Note: This list includes filenames only, not full paths
files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

if files:
    # Select a random filename from the list
    random_file = random.choice(files)

    full_path = os.path.join(directory, random_file)

with open(full_path, 'r', encoding='utf-8') as file:
        # Read the file and strip unnecessary whitespace
        data = file.read().replace('\r', '').replace("\t", " ").replace("\n", " ")
        space_indices = [i for i, char in enumerate(data) if char == ' ']
        space_index = random.choice(range(len(space_indices ) - 101))
        text_index_start = space_indices[space_index]
        text_index_end = space_indices[space_index + 100]
        excerpt = data[text_index_start:text_index_end]
        
        

# Game state
current_index = 0
feedback = None  # "correct" or "wrong"
feedback_time = 0

vibrate_key(excerpt[current_index])

running = True
clock = pygame.time.Clock()

scroll_x = 0
scrolling = False

while running:
    screen.fill((20, 20, 20))

    if scrolling:
        x = 400 - scroll_x  # keeps current letter near center
        y = 200

        for i, char in enumerate(excerpt):
            color = (200, 200, 200)

            if i < current_index:
                color = (100, 100, 100)
            elif i == current_index:
                if feedback == "correct":
                    color = (0, 255, 0)
                    scroll_x += 0.8
                elif feedback == "wrong":
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)

            text_surface = font.render(char, True, color)
            screen.blit(text_surface, (x, y))
            x += text_surface.get_width()

    else:
        x_offset = 20
        y_offset = 150

        
        positions = layout_text(excerpt, font, 950, 20, 100)
        # Draw excerpt with highlighting
        for i, (char, x, y) in enumerate(positions):
            color = (200, 200, 200)

            if i < current_index:
                color = (100, 100, 100)

            elif i == current_index:
                if feedback == "correct":
                    color = (0, 255, 0)
                elif feedback == "wrong":
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)

            text_surface = font.render(char, True, color)
            screen.blit(text_surface, (x, y))

        

    # Reset feedback color after short time
    if feedback and time.time() - feedback_time > 0.2:
        feedback = None

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            key = event.unicode

            # Handle space properly
            if key == "space":
                key = " "
                
            if key == "":
                continue

            expected = excerpt[current_index]

            print(f"Pressed: '{key}' | Expected: '{expected}'")

            if key == expected:
                feedback = "correct"
                current_index += 1

                if current_index < len(excerpt):
                    vibrate_key(excerpt[current_index])
            else:
                feedback = "wrong"
                vibrate_key(expected)  # remind correct key
            
            print(feedback)

            feedback_time = time.time()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()