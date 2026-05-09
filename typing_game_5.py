import pygame
import random
import time
import os
import csv
from collections import defaultdict
from datetime import datetime
import motor_utils


class TypingGame:
    def __init__(self):
        pygame.init()

        # Screen + font — start at 800x400 but allow resizing
        self.screen = pygame.display.set_mode((800, 400), pygame.RESIZABLE)
        pygame.display.set_caption("Typing Game")
        self.font = pygame.font.SysFont("Courier", 90)

        # Convenience properties (updated whenever the window resizes)
        self.W, self.H = self.screen.get_size()

        # -------------------------
        # Game states
        # -------------------------
        self.state = "title"   # title, game, results

        # -------------------------
        # Title State
        # -------------------------
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
        self.motors_active = False

        self.clock = pygame.time.Clock()
        self.running = True

        # Book metadata
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
        self.failed_keys = defaultdict(int)

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
        # Graphics
        # -------------------------
        self.bg_raw = pygame.image.load("Images/sunset.jpg").convert()
        self.bg = pygame.transform.scale(self.bg_raw, (self.W, self.H))

        self.sheeple_img = pygame.image.load("Images/sheeple.png").convert_alpha()

        # Sheeple state
        self.sheeple_x = self.W // 2
        self.sheeple_y = self.H // 2
        self.sheeple_vy = 0
        self.sheeple_angle = 0
        self.sheeple_spin_speed = 0

        # Pre-build char-width cache for the current font
        self._char_width_cache = {}

    # -------------------------
    # Helper: width of a single char
    # -------------------------
    def _cw(self, ch):
        if ch not in self._char_width_cache:
            self._char_width_cache[ch] = self.font.size(ch)[0]
        return self._char_width_cache[ch]

    # -------------------------
    # Hardware hook (placeholder)
    # -------------------------
    def vibrate_key(self, key_pressed):
        if self.motors_active:
            motor_utils.run_motor(key_pressed)
        else:
            print(key_pressed)

    

    # -------------------------
    # Text loading
    # -------------------------
    def load_excerpt(self):
        directory = "EasyBooks"
        # directory = "HardBooks"

        files = [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]

        if not files:
            return "No files found."

        random_file = random.choice(files)
        self.current_book = random_file
        full_path = os.path.join(directory, random_file)

        with open(full_path, 'r', encoding='utf-8') as file:
            data = (
                file.read()
                .replace('\r', '')
                .replace("\t", " ")
                .replace("\n", " ")
                .replace("\u201c", "\"")
                .replace("\u201d", "\"")
                .replace("\u2018", "'")
                .replace("\u2019", "'")
                .replace("  ", " ")
                .replace("\u2014", "-")
                .replace("_", "")
            )

        space_indices = [i for i, char in enumerate(data) if char == ' ']

        space_index = random.choice(range(len(space_indices) - 101))

        start = space_indices[space_index]
        self.excerpt_start = start
        end = space_indices[space_index + 25]
        self.excerpt_end = end

        return data[start:end]

    # -------------------------
    # Layout function (paragraph mode)
    # -------------------------
    def layout_text(self, text, max_width, start_x, start_y, line_spacing=5):
        """Return list of (char, x, y) for every character in *text*."""
        positions = []
        x = start_x
        y = start_y
        words = text.split(" ")

        for word in words:
            word_w = sum(self._cw(c) for c in word)
            space_w = self._cw(" ")

            if x + word_w > max_width and x != start_x:
                x = start_x
                y += self.font.get_height() + line_spacing

            for char in word:
                positions.append((char, x, y))
                x += self._cw(char)

            # trailing space
            positions.append((" ", x, y))
            x += space_w

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
            # Sheeple bounce
            self.sheeple_vy = -3
            self.sheeple_spin_speed = 0

            # Statistics
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
            self.sheeple_spin_speed = 20
            self.failed_keys[expected] += 1
            self.feedback = "wrong"
            self.vibrate_key(expected)

        self.feedback_time = time.time()

        if self.current_index >= len(self.excerpt):
            self.finish_game()

    # -------------------------
    # Finish game + calculate stats
    # -------------------------
    def finish_game(self):

        if motors_active:
            motor_utils.motor_cleanup()

        self.end_time = time.time()
        elapsed_minutes = (self.end_time - self.start_time) / 60

        self.wpm = (self.total_correct / 5) / elapsed_minutes if elapsed_minutes > 0 else 0

        self.accuracy = (self.total_correct / self.total_pressed * 100) if self.total_pressed > 0 else 0

        self.avg_reaction = (sum(self.reaction_times) / len(self.reaction_times)) if self.reaction_times else 0

        self.most_failed = max(self.failed_keys, key=self.failed_keys.get) if self.failed_keys else "None"

        self.save_results()
        self.state = "results"

    # -------------------------
    # Save results to CSV
    # -------------------------
    def save_results(self):
        file_exists = os.path.isfile("typing_results.csv")

        with open("typing_results.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow([
                    "Name", "Date", "Title", "Start Index", "End Index",
                    "WPM", "Accuracy", "Average Reaction", "Most Failed Key",
                    "Number Correct", "Number Pressed", "Seconds Elapsed"
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
                round(self.end_time - self.start_time, 2)
            ])

    # -------------------------
    # Drawing — SCROLLING mode
    # Keeps the current character horizontally centred.
    # -------------------------
    def draw_scrolling_text(self):
        cx = self.W // 2   # horizontal centre of the window
        y  = self.H // 2   # vertical centre

        # Build cumulative x-offsets from position 0
        # x_offsets[i] = pixel distance from the first char to char i
        x_offsets = []
        acc = 0
        for ch in self.excerpt:
            x_offsets.append(acc)
            acc += self._cw(ch)

        # We want excerpt[current_index] to appear at cx.
        # So char i is drawn at:  cx + (x_offsets[i] - x_offsets[current_index])
        origin = x_offsets[self.current_index]

        current_pos = None

        for i, char in enumerate(self.excerpt):
            draw_x = cx + (x_offsets[i] - origin)

            # Simple culling — skip chars well off-screen
            if draw_x < -200 or draw_x > self.W + 200:
                continue

            if i < self.current_index:
                color = (100, 100, 100)
            elif i == self.current_index:
                current_pos = (draw_x, y)
                if self.feedback == "correct":
                    color = (0, 255, 0)
                elif self.feedback == "wrong":
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)
            else:
                color = (200, 200, 200)

            surface = self.font.render(char, True, color)
            self.screen.blit(surface, (draw_x, y))

        # -------------------------
        # Update & draw sheeple
        # -------------------------
        if current_pos:
            target_x, target_y = current_pos
            target_y -= 20  # hover above the letter

            self.sheeple_x += (target_x - self.sheeple_x) * 0.2

            self.sheeple_vy += 0.5
            self.sheeple_y += self.sheeple_vy

            if self.sheeple_y > target_y:
                self.sheeple_y = target_y
                self.sheeple_vy = -abs(self.sheeple_vy) * 0.6

    # -------------------------
    # Drawing — PARAGRAPH (wrapped) mode
    # -------------------------
    def draw_wrapped_text(self):
        margin = 20
        top    = int(self.H * 0.25)   # start text at 25 % of window height

        positions = self.layout_text(
            self.excerpt,
            max_width=self.W - margin,
            start_x=margin,
            start_y=top
        )

        current_pos = None

        for i, (char, x, y) in enumerate(positions):
            if i < self.current_index:
                color = (100, 100, 100)
            elif i == self.current_index:
                current_pos = (x, y)
                if self.feedback == "correct":
                    color = (0, 255, 0)
                elif self.feedback == "wrong":
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)
            else:
                color = (200, 200, 200)

            surface = self.font.render(char, True, color)
            self.screen.blit(surface, (x, y))

        # -------------------------
        # Update & draw sheeple (paragraph mode)
        # -------------------------
        if current_pos:
            target_x, target_y = current_pos
            target_y -= 20

            self.sheeple_x += (target_x - self.sheeple_x) * 0.2

            self.sheeple_vy += 0.5
            self.sheeple_y += self.sheeple_vy

            if self.sheeple_y > target_y:
                self.sheeple_y = target_y
                self.sheeple_vy = -abs(self.sheeple_vy) * 0.6

    def draw_remaining_chars(self):
        small_font = pygame.font.SysFont("Courier", 30)
        remaining = len(self.excerpt) - self.current_index
        surface = small_font.render(f"Remaining: {remaining}", True, (255, 255, 255))
        self.screen.blit(surface, (10, 10))

    def draw_book_name(self):
        small_font = pygame.font.SysFont("Courier", 30)
        surface = small_font.render(f"{self.current_book}", True, (255, 255, 255))
        self.screen.blit(surface, (10, 30))

    # -------------------------
    # Title screen
    # -------------------------
    def draw_title_screen(self):
        title_font = pygame.font.SysFont("Courier", 72)
        input_font = pygame.font.SysFont("Courier", 48)

        cx = self.W // 2

        title_surface = title_font.render("Typing Game", True, (255, 255, 255))
        self.screen.blit(title_surface, (cx - title_surface.get_width() // 2, int(self.H * 0.20)))

        instruction = input_font.render("Enter Name:", True, (200, 200, 200))
        self.screen.blit(instruction, (cx - instruction.get_width() // 2, int(self.H * 0.45)))

        box_w, box_h = 440, 60
        box_x = cx - box_w // 2
        box_y = int(self.H * 0.58)
        pygame.draw.rect(self.screen, (100, 100, 100), (box_x, box_y, box_w, box_h), 2)

        name_surface = input_font.render(self.player_name, True, (0, 255, 0))
        self.screen.blit(name_surface, (box_x + 20, box_y + 8))

        start_surface = input_font.render("Press ENTER to Start", True, (255, 255, 0))
        self.screen.blit(start_surface, (cx - start_surface.get_width() // 2, int(self.H * 0.80)))

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

        total_h = len(lines) * 55
        y = (self.H - total_h) // 2

        for line in lines:
            surface = font.render(line, True, (255, 255, 255))
            self.screen.blit(surface, ((self.W - surface.get_width()) // 2, y))
            y += 55

    # -------------------------
    # Main loop
    # -------------------------
    def run(self):
        while self.running:
            # ------------------------------------------
            # Handle window resize + rescale background
            # ------------------------------------------
            new_w, new_h = self.screen.get_size()
            if (new_w, new_h) != (self.W, self.H):
                self.W, self.H = new_w, new_h
                self.bg = pygame.transform.scale(self.bg_raw, (self.W, self.H))

            self.screen.blit(self.bg, (0, 0))

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

                # Update & draw sheeple (rotation / size)
                self.sheeple_angle += self.sheeple_spin_speed
                self.sheeple_spin_speed *= 0.92

                if abs(self.sheeple_spin_speed) < 0.1:
                    self.sheeple_spin_speed = 0

                self.sheeple_angle %= 360

                transformed = pygame.transform.smoothscale(self.sheeple_img, (120, 120))
                rotated = pygame.transform.rotate(transformed, self.sheeple_angle)
                rect = rotated.get_rect(center=(int(self.sheeple_x), int(self.sheeple_y)))
                self.screen.blit(rotated, rect)

            elif self.state == "results":
                self.draw_results_screen()

            # Reset feedback after short window
            if self.feedback and time.time() - self.feedback_time > 0.2:
                self.feedback = None

            # -------------------------
            # Events
            # -------------------------
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    # pygame.RESIZABLE handles this automatically in pygame 2,
                    # but we update W/H at the top of the loop anyway.
                    pass

                elif event.type == pygame.KEYDOWN:

                    # TITLE
                    if self.state == "title":

                        if event.key == pygame.K_RETURN:
                            if self.player_name.strip() != "":
                                self.state = "game"
                                self.start_time = time.time()
                                self.last_time = time.time()
                                self.vibrate_key(self.excerpt[self.current_index])

                        elif event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]

                        else:
                            if event.unicode.isprintable() and len(self.player_name) < 15:
                                self.player_name += event.unicode

                    # GAME
                    elif self.state == "game":
                        self.handle_key(event.unicode)

                    # RESULTS
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