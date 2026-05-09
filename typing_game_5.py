import pygame
import random
import time
import os
import csv
from collections import defaultdict
from datetime import datetime
#import motor_utils


# ─────────────────────────────────────────────────────────────────────────────
#  TypingGame
# ─────────────────────────────────────────────────────────────────────────────
class TypingGame:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 400), pygame.RESIZABLE)
        pygame.display.set_caption("Typing Game")
        self.font = pygame.font.SysFont("Courier", 90)

        self.W, self.H = self.screen.get_size()

        # ── Menu / settings ──────────────────────────────────────────────────
        self.motors_active = False   # toggled on menu
        self.scrolling     = True    # True = scroll mode, False = paragraph

        # ── Game states ──────────────────────────────────────────────────────
        # "title" → "game" | "simple"  → "results"
        self.state = "title"

        # ── Title state ───────────────────────────────────────────────────────
        self.player_name = ""

        # ── Main (book) state ─────────────────────────────────────────────────
        self.current_index = 0
        self.feedback      = None
        self.feedback_time = 0

        self.clock   = pygame.time.Clock()
        self.running = True

        self.current_book  = ""
        self.excerpt_start = 0
        self.excerpt_end   = 0
        self.excerpt       = self.load_excerpt()

        # ── Simple mode state ─────────────────────────────────────────────────
        self.simple_keys    = list("asdfjkl;")   # default key set
        self.simple_letter  = random.choice(self.simple_keys)
        self.simple_correct = 0
        self.simple_pressed = 0
        self.simple_times   = []
        self.simple_last    = time.time()
        self.simple_failed  = defaultdict(int)

        # ── Results state ─────────────────────────────────────────────────────
        self.failed_keys    = defaultdict(int)
        self.accuracy       = 0
        self.avg_reaction   = 0
        self.most_failed    = "None"
        self.start_time     = time.time()
        self.last_time      = time.time()
        self.end_time       = time.time()
        self.wpm            = 0
        self.reaction_times = []
        self.total_correct  = 0
        self.total_pressed  = 0

        # ── Graphics ──────────────────────────────────────────────────────────
        self.bg_raw    = pygame.image.load("Images/sunset.jpg").convert()
        self.bg        = pygame.transform.scale(self.bg_raw, (self.W, self.H))
        self.sheeple_img = pygame.image.load("Images/sheeple.png").convert_alpha()

        self.sheeple_x       = self.W // 2
        self.sheeple_y       = self.H // 2
        self.sheeple_vy      = 0
        self.sheeple_angle   = 0
        self.sheeple_spin    = 0

        self._char_width_cache = {}

        # Vibrate the first key
        self.vibrate_key(self.excerpt[self.current_index])

    # ─────────────────────────────────────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _cw(self, ch):
        if ch not in self._char_width_cache:
            self._char_width_cache[ch] = self.font.size(ch)[0]
        return self._char_width_cache[ch]

    def vibrate_key(self, key_pressed):
        if self.motors_active:
            motor_utils.run_motor(key_pressed)
        else:
            print(key_pressed)

    # ─────────────────────────────────────────────────────────────────────────
    #  Text loading
    # ─────────────────────────────────────────────────────────────────────────
    def load_excerpt(self):
        directory = "EasyBooks"
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        if not files:
            return "No files found."

        random_file = random.choice(files)
        self.current_book = random_file
        full_path = os.path.join(directory, random_file)

        with open(full_path, 'r', encoding='utf-8') as file:
            data = (
                file.read()
                .replace('\r', '').replace("\t", " ").replace("\n", " ")
                .replace("\u201c", "\"").replace("\u201d", "\"")
                .replace("\u2018", "'").replace("\u2019", "'")
                .replace("  ", " ").replace("\u2014", "-").replace("_", "")
            )

        space_indices = [i for i, char in enumerate(data) if char == ' ']
        space_index = random.choice(range(len(space_indices) - 101))
        start = space_indices[space_index]
        self.excerpt_start = start
        end = space_indices[space_index + 25]
        self.excerpt_end = end
        return data[start:end]

    # ─────────────────────────────────────────────────────────────────────────
    #  Layout
    # ─────────────────────────────────────────────────────────────────────────
    def layout_text(self, text, max_width, start_x, start_y, line_spacing=5):
        positions = []
        x, y = start_x, start_y
        for word in text.split(" "):
            word_w  = sum(self._cw(c) for c in word)
            space_w = self._cw(" ")
            if x + word_w > max_width and x != start_x:
                x = start_x
                y += self.font.get_height() + line_spacing
            for char in word:
                positions.append((char, x, y))
                x += self._cw(char)
            positions.append((" ", x, y))
            x += space_w
        return positions

    # ─────────────────────────────────────────────────────────────────────────
    #  Input handling — book mode
    # ─────────────────────────────────────────────────────────────────────────
    def handle_key(self, key):
        if key == "space":
            key = " "
        if key == "":
            return

        expected = self.excerpt[self.current_index]
        self.total_pressed += 1

        if key == expected:
            self.sheeple_vy   = -3
            self.sheeple_spin = 0
            self.total_correct += 1
            now = time.time()
            self.reaction_times.append(now - self.last_time)
            self.last_time = now
            self.feedback = "correct"
            self.current_index += 1
            if self.current_index < len(self.excerpt):
                self.vibrate_key(self.excerpt[self.current_index])
        else:
            self.sheeple_spin = 20
            self.failed_keys[expected] += 1
            self.feedback = "wrong"
            self.vibrate_key(expected)

        self.feedback_time = time.time()
        if self.current_index >= len(self.excerpt):
            self.finish_game()

    # ─────────────────────────────────────────────────────────────────────────
    #  Finish + stats — book mode
    # ─────────────────────────────────────────────────────────────────────────
    def finish_game(self):
        if self.motors_active:
            motor_utils.motor_cleanup()
        self.end_time = time.time()
        elapsed = (self.end_time - self.start_time) / 60
        self.wpm          = (self.total_correct / 5) / elapsed if elapsed > 0 else 0
        self.accuracy     = (self.total_correct / self.total_pressed * 100) if self.total_pressed > 0 else 0
        self.avg_reaction = (sum(self.reaction_times) / len(self.reaction_times)) if self.reaction_times else 0
        self.most_failed  = max(self.failed_keys, key=self.failed_keys.get) if self.failed_keys else "None"
        self.save_results()
        self.state = "results"

    # ─────────────────────────────────────────────────────────────────────────
    #  CSV
    # ─────────────────────────────────────────────────────────────────────────
    def save_results(self):
        file_exists = os.path.isfile("typing_results.csv")
        with open("typing_results.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "Name","Date","Title","Start Index","End Index",
                    "WPM","Accuracy","Average Reaction","Most Failed Key",
                    "Number Correct","Number Pressed","Seconds Elapsed"
                ])
            writer.writerow([
                self.player_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.current_book,
                self.excerpt_start, self.excerpt_end,
                round(self.wpm,2), round(self.accuracy,2),
                round(self.avg_reaction,3), self.most_failed,
                self.total_correct, self.total_pressed,
                round(self.end_time - self.start_time, 2)
            ])

    # ─────────────────────────────────────────────────────────────────────────
    #  Drawing — scrolling text
    # ─────────────────────────────────────────────────────────────────────────
    def draw_scrolling_text(self):
        cx = self.W // 2
        y  = self.H // 2

        x_offsets, acc = [], 0
        for ch in self.excerpt:
            x_offsets.append(acc)
            acc += self._cw(ch)

        origin      = x_offsets[self.current_index]
        current_pos = None

        for i, char in enumerate(self.excerpt):
            draw_x = cx + (x_offsets[i] - origin)
            if draw_x < -200 or draw_x > self.W + 200:
                continue
            if i < self.current_index:
                color = (100, 100, 100)
            elif i == self.current_index:
                current_pos = (draw_x, y)
                color = (0,255,0) if self.feedback=="correct" else (255,0,0) if self.feedback=="wrong" else (255,255,0)
            else:
                color = (200, 200, 200)
            self.screen.blit(self.font.render(char, True, color), (draw_x, y))

        self._update_sheeple(current_pos)

    # ─────────────────────────────────────────────────────────────────────────
    #  Drawing — paragraph text
    # ─────────────────────────────────────────────────────────────────────────
    def draw_wrapped_text(self):
        margin = 20
        top    = int(self.H * 0.25)
        positions   = self.layout_text(self.excerpt, self.W - margin, margin, top)
        current_pos = None

        for i, (char, x, y) in enumerate(positions):
            if i < self.current_index:
                color = (100, 100, 100)
            elif i == self.current_index:
                current_pos = (x, y)
                color = (0,255,0) if self.feedback=="correct" else (255,0,0) if self.feedback=="wrong" else (255,255,0)
            else:
                color = (200, 200, 200)
            self.screen.blit(self.font.render(char, True, color), (x, y))

        self._update_sheeple(current_pos)

    def _update_sheeple(self, current_pos):
        if current_pos:
            tx, ty = current_pos[0], current_pos[1] - 20
            self.sheeple_x += (tx - self.sheeple_x) * 0.2
            self.sheeple_vy += 0.5
            self.sheeple_y  += self.sheeple_vy
            if self.sheeple_y > ty:
                self.sheeple_y  = ty
                self.sheeple_vy = -abs(self.sheeple_vy) * 0.6

    def draw_remaining_chars(self):
        sf = pygame.font.SysFont("Courier", 30)
        self.screen.blit(sf.render(f"Remaining: {len(self.excerpt)-self.current_index}", True, (255,255,255)), (10, 10))

    def draw_book_name(self):
        sf = pygame.font.SysFont("Courier", 30)
        self.screen.blit(sf.render(self.current_book, True, (255,255,255)), (10, 30))

    # ─────────────────────────────────────────────────────────────────────────
    #  Drawing — title / menu screen
    # ─────────────────────────────────────────────────────────────────────────
    def draw_title_screen(self):
        tf  = pygame.font.SysFont("Courier", 72)
        inf = pygame.font.SysFont("Courier", 40)
        sf  = pygame.font.SysFont("Courier", 32)
        cx  = self.W // 2

        # Title
        t = tf.render("Typing Game", True, (255, 255, 255))
        self.screen.blit(t, (cx - t.get_width()//2, int(self.H * 0.06)))

        # Name input
        lbl = inf.render("Enter Name:", True, (200, 200, 200))
        self.screen.blit(lbl, (cx - lbl.get_width()//2, int(self.H * 0.25)))
        bx, by, bw, bh = cx - 220, int(self.H * 0.35), 440, 50
        pygame.draw.rect(self.screen, (100, 100, 100), (bx, by, bw, bh), 2)
        self.screen.blit(inf.render(self.player_name, True, (0, 255, 0)), (bx + 12, by + 6))

        # ── Toggle buttons ────────────────────────────────────────────────────
        # Motor vibration toggle
        motor_color = (0, 220, 100) if self.motors_active else (180, 60, 60)
        motor_label = f"Motors: {'ON ' if self.motors_active else 'OFF'}"
        mbtn = sf.render(f"[M]  {motor_label}", True, motor_color)
        self.screen.blit(mbtn, (cx - mbtn.get_width()//2, int(self.H * 0.52)))

        # Scroll mode toggle
        scroll_color = (100, 180, 255)
        scroll_label = "Scroll Mode" if self.scrolling else "Paragraph Mode"
        sbtn = sf.render(f"[S]  {scroll_label}", True, scroll_color)
        self.screen.blit(sbtn, (cx - sbtn.get_width()//2, int(self.H * 0.62)))

        # ── Game mode buttons ─────────────────────────────────────────────────
        book_btn = inf.render("[ENTER]  Book Mode", True, (255, 255, 0))
        self.screen.blit(book_btn, (cx - book_btn.get_width()//2, int(self.H * 0.74)))

        simp_btn = inf.render("[TAB]    Simple Mode", True, (255, 200, 80))
        self.screen.blit(simp_btn, (cx - simp_btn.get_width()//2, int(self.H * 0.86)))

    # ─────────────────────────────────────────────────────────────────────────
    #  Drawing — simple mode
    # ─────────────────────────────────────────────────────────────────────────
    def draw_simple_mode(self):
        cx, cy = self.W // 2, self.H // 2

        # Big target letter
        big_font = pygame.font.SysFont("Courier", 180)
        color = (
            (0, 255, 0)   if self.feedback == "correct" else
            (255, 60, 60) if self.feedback == "wrong"   else
            (255, 255, 255)
        )
        letter_surf = big_font.render(self.simple_letter.upper(), True, color)
        self.screen.blit(letter_surf, (cx - letter_surf.get_width()//2, cy - letter_surf.get_height()//2))

        # Stats overlay
        sf = pygame.font.SysFont("Courier", 28)
        acc = (self.simple_correct / self.simple_pressed * 100) if self.simple_pressed > 0 else 0
        self.screen.blit(sf.render(f"Correct: {self.simple_correct}  Pressed: {self.simple_pressed}  Acc: {acc:.1f}%",
                                   True, (200,200,200)), (10, 10))
        keys_str = "Keys: " + " ".join(k if k != " " else "SPC" for k in self.simple_keys)
        self.screen.blit(sf.render(keys_str, True, (150,150,150)), (10, 40))
        self.screen.blit(sf.render("ESC = quit  |  motors toggle with M", True, (120,120,120)), (10, self.H-35))

    def handle_simple_key(self, key):
        if key == "space":
            key = " "
        if key == "":
            return

        self.simple_pressed += 1

        if key == self.simple_letter:
            self.simple_correct += 1
            now = time.time()
            self.simple_times.append(now - self.simple_last)
            self.simple_last = now
            self.feedback = "correct"
            # pick a different letter
            choices = [k for k in self.simple_keys if k != self.simple_letter]
            self.simple_letter = random.choice(choices if choices else self.simple_keys)
            self.vibrate_key(self.simple_letter)
        else:
            self.simple_failed[self.simple_letter] += 1
            self.feedback = "wrong"
            self.vibrate_key(self.simple_letter)

        self.feedback_time = time.time()

    def finish_simple(self):
        if self.motors_active:
            motor_utils.motor_cleanup()
        self.end_time    = time.time()
        elapsed          = (self.end_time - self.start_time) / 60
        self.wpm         = (self.simple_correct / 5) / elapsed if elapsed > 0 else 0
        self.accuracy    = (self.simple_correct / self.simple_pressed * 100) if self.simple_pressed > 0 else 0
        self.avg_reaction= (sum(self.simple_times) / len(self.simple_times)) if self.simple_times else 0
        self.most_failed = max(self.simple_failed, key=self.simple_failed.get) if self.simple_failed else "None"
        self.total_correct  = self.simple_correct
        self.total_pressed  = self.simple_pressed
        self.reaction_times = self.simple_times
        self.state = "results"

    # ─────────────────────────────────────────────────────────────────────────
    #  Drawing — results
    # ─────────────────────────────────────────────────────────────────────────
    def draw_results_screen(self):
        font  = pygame.font.SysFont("Courier", 42)
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
            s = font.render(line, True, (255,255,255))
            self.screen.blit(s, ((self.W - s.get_width())//2, y))
            y += 55

    # ─────────────────────────────────────────────────────────────────────────
    #  Main loop
    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            # Resize handling
            nw, nh = self.screen.get_size()
            if (nw, nh) != (self.W, self.H):
                self.W, self.H = nw, nh
                self.bg = pygame.transform.scale(self.bg_raw, (self.W, self.H))

            self.screen.blit(self.bg, (0, 0))

            # ── Draw current state ────────────────────────────────────────────
            if self.state == "title":
                self.draw_title_screen()

            elif self.state == "game":
                if self.scrolling:
                    self.draw_scrolling_text()
                else:
                    self.draw_wrapped_text()
                self.draw_remaining_chars()
                self.draw_book_name()

                # Sheeple
                self.sheeple_angle += self.sheeple_spin
                self.sheeple_spin  *= 0.92
                if abs(self.sheeple_spin) < 0.1:
                    self.sheeple_spin = 0
                self.sheeple_angle %= 360
                transformed = pygame.transform.smoothscale(self.sheeple_img, (120,120))
                rotated     = pygame.transform.rotate(transformed, self.sheeple_angle)
                rect        = rotated.get_rect(center=(int(self.sheeple_x), int(self.sheeple_y)))
                self.screen.blit(rotated, rect)

            elif self.state == "simple":
                self.draw_simple_mode()

            elif self.state == "results":
                self.draw_results_screen()

            # Feedback timeout
            if self.feedback and time.time() - self.feedback_time > 0.2:
                self.feedback = None

            # ── Events ────────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    pass

                elif event.type == pygame.KEYDOWN:

                    # ── TITLE ─────────────────────────────────────────────────
                    if self.state == "title":
                        if event.key == pygame.K_m:
                            self.motors_active = not self.motors_active

                        elif event.key == pygame.K_s:
                            self.scrolling = not self.scrolling

                        elif event.key == pygame.K_RETURN:
                            if self.player_name.strip():
                                self.state      = "game"
                                self.start_time = time.time()
                                self.last_time  = time.time()
                                self.vibrate_key(self.excerpt[self.current_index])

                        elif event.key == pygame.K_TAB:
                            if self.player_name.strip():
                                self.state       = "simple"
                                self.start_time  = time.time()
                                self.simple_last = time.time()
                                self.vibrate_key(self.simple_letter)

                        elif event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]

                        else:
                            if event.unicode.isprintable() and len(self.player_name) < 15:
                                self.player_name += event.unicode

                    # ── GAME (book) ───────────────────────────────────────────
                    elif self.state == "game":
                        self.handle_key(event.unicode)

                    # ── SIMPLE ────────────────────────────────────────────────
                    elif self.state == "simple":
                        if event.key == pygame.K_ESCAPE:
                            self.finish_simple()
                        elif event.key == pygame.K_m:
                            self.motors_active = not self.motors_active
                        else:
                            self.handle_simple_key(event.unicode)

                    # ── RESULTS ───────────────────────────────────────────────
                    elif self.state == "results":
                        if event.key == pygame.K_ESCAPE:
                            self.running = False

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TypingGame().run()