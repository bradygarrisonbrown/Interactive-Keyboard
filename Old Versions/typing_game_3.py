import pygame
import random
import time
import os
import csv
from collections import defaultdict
from datetime import datetime


class TypingGame:
    def __init__(self):
        pygame.init()

        # Screen + font
        self.screen = pygame.display.set_mode((800, 400))
        pygame.display.set_caption("Typing Game")
        self.font = pygame.font.SysFont("Courier", 90)

        # -------------------------
        # Game states
        # -------------------------
        self.state = "title"   # title, game, results

        # -------------------------
        # Title State
        # -------------------------
        # Player name
        self.player_name = ""
        self.name_active = True

        # -------------------------
        # Main State
        # -------------------------
        self.current_index = 0
        self.feedback = None
        self.feedback_time = 0

        self.scroll_x = 0
        self.scrolling = True

        self.clock = pygame.time.Clock()
        self.running = True

        #Book metadata
        self.current_book = ""
        self.excerpt_start = 0
        self.excerpt_end = 0

        # Load text
        self.excerpt = self.load_excerpt()

        # Initial vibration
        self.vibrate_key(self.excerpt[self.current_index])


        # -------------------------
        # Results State
        # -------------------------
        #User data collected

        # Metrics
        self.failed_keys = defaultdict(int)

        # Results
        self.accuracy = 0
        self.avg_reaction = 0
        self.most_failed = "None"
        self.start_time = time.time()
        self.last_time = time.time()
        self.end_time = time.time()
        self.wpm = 0
        self.reaction_times = []
        self.total_correct = 0
        self.total_pressed = 0

        

    # -------------------------
    # Hardware hook (placeholder)
    # -------------------------
    def vibrate_key(self, key_pressed):
        print(key_pressed)

    # -------------------------
    # Text loading
    # -------------------------
    def load_excerpt(self):
        directory = "EasyBooks"
        #directory = "HardBooks"

        files = [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]

        if not files:
            return "No files found."

        random_file = random.choice(files)
        self.current_book = random_file
        #print(self.current_book)
        full_path = os.path.join(directory, random_file)

        with open(full_path, 'r', encoding='utf-8') as file:
            data = file.read().replace('\r', '').replace("\t", " ").replace("\n", " ").replace("”", "\"").replace("“", "\"").replace("’", "\'").replace("  ", " ").replace("—", "-").replace("_", "")

        space_indices = [i for i, char in enumerate(data) if char == ' ']

        # Pick ~50-word excerpt
        space_index = random.choice(range(len(space_indices) - 101))

        start = space_indices[space_index]
        self.excerpt_start = start
        end = space_indices[space_index + 25]
        self.excerpt_end = end

        return data[start:end]

    # -------------------------
    # Layout function
    # -------------------------
    def layout_text(self, text, max_width, start_x, start_y, line_spacing=5):
        positions = []

        x = start_x
        y = start_y

        words = text.split(" ")

        for word in words:
            word_surface = self.font.render(word, True, (255, 255, 255))
            space_surface = self.font.render(" ", True, (255, 255, 255))

            if x + word_surface.get_width() > max_width:
                x = start_x
                y += self.font.get_height() + line_spacing

            for char in word:
                char_surface = self.font.render(char, True, (255, 255, 255))
                positions.append((char, x, y))
                x += char_surface.get_width()

            positions.append((" ", x, y))
            x += space_surface.get_width()

        return positions

    # -------------------------
    # Input handling
    # -------------------------
    def handle_key(self, key):
        if key == "space":
            key = " "

        if key == "":
            return

        expected = self.excerpt[self.current_index]

        print(f"Pressed: '{key}' | Expected: '{expected}'")

        self.total_pressed += 1

        if key == expected:

            #Statistics Tracking
            self.total_correct += 1
            current_time = time.time()
            reaction = current_time - self.last_time
            self.reaction_times.append(reaction)
            self.last_time = current_time

            self.feedback = "correct"
            self.current_index += 1

            if self.current_index < len(self.excerpt):
                self.vibrate_key(self.excerpt[self.current_index])
        else:
            #Add one to failed keys
            self.failed_keys[expected] += 1


            #Output for user
            self.feedback = "wrong"
            self.vibrate_key(expected)


        self.feedback_time = time.time()

        # End game
        if self.current_index >= len(self.excerpt):
            self.finish_game()


    # -------------------------
    # Finish game + calculate stats
    # -------------------------
    def finish_game(self):
        self.end_time = time.time()

        elapsed_minutes = (self.end_time - self.start_time) / 60

        # WPM
        if elapsed_minutes > 0:
            self.wpm = (self.total_correct / 5) / elapsed_minutes
        else:
            self.wpm = 0

        # Accuracy
        if self.total_pressed > 0:
            self.accuracy = (
                self.total_correct / self.total_pressed
            ) * 100
        else:
            self.accuracy = 0

        # Average reaction time
        if self.reaction_times:
            self.avg_reaction = (
                sum(self.reaction_times)
                / len(self.reaction_times)
            )
        else:
            self.avg_reaction = 0

        # Most failed key
        if self.failed_keys:
            self.most_failed = max(
                self.failed_keys,
                key=self.failed_keys.get
            )
        else:
            self.most_failed = "None"

        # Save results
        self.save_results()

        # Switch screen
        self.state = "results"

    # -------------------------
    # Save results to CSV
    # -------------------------
    def save_results(self):
        file_exists = os.path.isfile("typing_results.csv")

        with open(
            "typing_results.csv",
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            # Header
            if not file_exists:
                writer.writerow([
                    "Name",
                    "Date",
                    "Title",
                    "Start Index",
                    "End Index",
                    "WPM",
                    "Accuracy",
                    "Average Reaction",
                    "Most Failed Key",
                    "Number Correct",
                    "Number Pressed",
                    "Seconds Elapsed"

                ])

            writer.writerow([
                self.player_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.current_book,
                self.excerpt_start,
                self.excerpt_end,
                round(self.wpm, 2),
                round(self.accuracy, 2),
                round(self.avg_reaction, 3),
                self.most_failed,
                self.total_correct,
                self.total_pressed,
                round(self.end_time - self.start_time,2)
            ])


    # -------------------------
    # Drawing
    # -------------------------
    def draw_scrolling_text(self):
        
        x = 400 - self.scroll_x
        y = 200

        for i, char in enumerate(self.excerpt):
            color = (200, 200, 200)

            if i < self.current_index:
                color = (100, 100, 100)
            elif i == self.current_index:
                if self.feedback == "correct":
                    color = (0, 255, 0)
                    self.scroll_x += 5.5
                elif self.feedback == "wrong":
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)

            surface = self.font.render(char, True, color)
            self.screen.blit(surface, (x, y))
            x += surface.get_width()

    def draw_wrapped_text(self):
        positions = self.layout_text(self.excerpt, 950, 20, 100)

        for i, (char, x, y) in enumerate(positions):
            color = (200, 200, 200)

            if i < self.current_index:
                color = (100, 100, 100)
            elif i == self.current_index:
                if self.feedback == "correct":
                    color = (0, 255, 0)
                elif self.feedback == "wrong":
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)

            surface = self.font.render(char, True, color)
            self.screen.blit(surface, (x, y))

    def draw_remaining_chars(self):
        small_font = pygame.font.SysFont("Courier", 30)
        remaining = len(self.excerpt) - self.current_index
        remaining_surface = small_font.render(
            f"Remaining: {remaining}",
            True,
            (255, 255, 255)
        )

        self.screen.blit(remaining_surface, (10, 10))

    def draw_book_name(self):
        small_font = pygame.font.SysFont("Courier", 30)
        book_surface = small_font.render(
            f"{self.current_book}",
            True,
            (255, 255, 255)
        )

        self.screen.blit(book_surface, (10, 30))

    # -------------------------
    # Title screen
    # -------------------------
    def draw_title_screen(self):
        title_font = pygame.font.SysFont("Courier", 72)
        input_font = pygame.font.SysFont("Courier", 48)

        # Title
        title_surface = title_font.render(
            "Typing Game",
            True,
            (255, 255, 255)
        )

        self.screen.blit(title_surface, (180, 80))

        # Instructions
        instruction = input_font.render(
            "Enter Name:",
            True,
            (200, 200, 200)
        )

        self.screen.blit(instruction, (220, 180))

        # Name box
        name_surface = input_font.render(
            self.player_name,
            True,
            (0, 255, 0)
        )

        pygame.draw.rect(
            self.screen,
            (100, 100, 100),
            (180, 250, 440, 60),
            2
        )

        self.screen.blit(name_surface, (200, 260))

        # Start text
        start_surface = input_font.render(
            "Press ENTER to Start",
            True,
            (255, 255, 0)
        )

        self.screen.blit(start_surface, (120, 330))


    # -------------------------
    # Results screen
    # -------------------------
    def draw_results_screen(self):
        font = pygame.font.SysFont("Courier", 42)

        lines = [
            f"Player: {self.player_name}",
            f"WPM: {self.wpm:.2f}",
            f"Accuracy: {self.accuracy:.2f}%",
            f"Avg Reaction: {self.avg_reaction:.3f}s",
            f"Most Failed Key: {self.most_failed}",
            "",
            "Press ESC to Quit"
        ]

        y = 60

        for line in lines:
            surface = font.render(
                line,
                True,
                (255, 255, 255)
            )

            self.screen.blit(surface, (80, y))
            y += 55

    # -------------------------
    # Main loop
    # -------------------------
    def run(self):
        while self.running:
            self.screen.fill((20, 20, 20))

            # -------------------------
            # Draw current state
            # -------------------------
            if self.state == "title":
                self.draw_title_screen()

            elif self.state == "game":

                if self.scrolling:
                    self.draw_scrolling_text()
                else:
                    self.draw_wrapped_text()

                self.draw_remaining_chars()
                self.draw_book_name()

            elif self.state == "results":
                self.draw_results_screen()

            # Reset feedback after short time
            if self.feedback and time.time() - self.feedback_time > 0.2:
                self.feedback = None

            # Events
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:

                    # -------------------------
                    # TITLE SCREEN
                    # -------------------------
                    if self.state == "title":

                        # Start game
                        if event.key == pygame.K_RETURN:

                            if self.player_name.strip() != "":
                                self.state = "game"

                                # Reset timers at actual game start
                                self.start_time = time.time()
                                self.last_time = time.time()

                                #Vibrate First Key in Excerpt
                                self.vibrate_key(
                                    self.excerpt[self.current_index]
                                )

                        # Delete character
                        elif event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]

                        # Add typed character
                        else:

                            # Ignore weird control keys
                            if event.unicode.isprintable():

                                if len(self.player_name) < 15:
                                    self.player_name += event.unicode

                    # -------------------------
                    # GAMEPLAY
                    # -------------------------
                    elif self.state == "game":

                        self.handle_key(event.unicode)

                    # -------------------------
                    # RESULTS SCREEN
                    # -------------------------
                    elif self.state == "results":

                        if event.key == pygame.K_ESCAPE:
                            self.running = False



            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


# -------------------------
# Run game
# -------------------------
if __name__ == "__main__":
    TypingGame().run()