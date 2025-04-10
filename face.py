import tkinter as tk
from PIL import Image, ImageTk
import os
import numpy as np
from scipy.ndimage import binary_erosion
import random
import tkinter.ttk as ttk
import time
import importlib

CLIP_DIR = 'faces'  # put your expression folders in this folder
FRAME_RATE = 60

class FaceApp:
    def __init__(self, root):
        self.animation_progress = 0.0
        self.animation_duration = 180  # total frames for walk animation (~3 seconds at 60 FPS)
        self.bounce_timer = 0
        self.root = root
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-transparentcolor', 'green')
        self.root.wm_attributes("-disabled", True)
        self.root.wm_attributes("-topmost", True)

        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()

        self.original_width = 1000
        self.original_height = 1000
        self.scale_factor = 0.80
        self.win_width = int(self.original_width * self.scale_factor)
        self.win_height = int(self.original_height * self.scale_factor)

        self.label = tk.Label(self.root, bg='green')
        self.label.pack()

        self.expressions = {}
        # self.loaded_expression = None  # no longer needed with full preload
        self.load_all_expressions_with_progress()  # re-enabled full preload
        self.current_expression = 'normal'
        self.frame_index = 0
        self.last_update_time = time.time()
        self.speaking = False
        self.phoneme_queue = []
        self.original_expression = 'normal'

        self.visible = False
        self.animating = False
        self.x = self.screen_width
        self.animation_start_x = self.x

        self.root.geometry(f"{self.win_width}x{self.win_height}+{self.x}+{self.screen_height - self.win_height}")
        self.update_frame()
        self.watch_api_variables()

    def load_expression(self, expression):
        path = os.path.join(CLIP_DIR, expression)
        if not os.path.isdir(path):
            print(f"[WARNING] Expression folder '{expression}' not found.")
            return []
        frame_files = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')], key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))))
        frames = []
        for f in frame_files:
            try:
                print(f"[DEBUG] Loading image: {f}")
                img = Image.open(f).convert('RGBA').resize((self.win_width, self.win_height), Image.Resampling.LANCZOS)
                img = self.key_out_green(img)
                frames.append(img)
            except Exception as e:
                print(f"[ERROR] Failed to load image {f}: {e}")
        return frames

    def update_frame(self):
        now = time.time()
        elapsed = now - self.last_update_time

        if elapsed > 1.0 / FRAME_RATE:
            # Handle phoneme switching
            if self.speaking and self.phoneme_queue:
                phoneme = self.phoneme_queue.pop(0)
                if phoneme in self.expressions:
                    self.current_expression = phoneme
            elif self.speaking:
                self.speaking = False
                self.current_expression = self.original_expression

            frames = self.expressions.get(self.current_expression, [])
            if frames:
                frame = frames[self.frame_index % len(frames)]
                self.frame_index += 1

                display_frame = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                display_frame.paste(frame, (0, 0), frame)
                imgtk = ImageTk.PhotoImage(display_frame)
                self.label.imgtk = imgtk
                self.label.config(image=imgtk)

            self.last_update_time = now

        self.update_position()
        self.root.after(1, self.update_frame)

    def set_expression(self, name):
        # Expression already preloaded; skip dynamic loading
        if name in self.expressions and not self.animating and not self.speaking:
            self.current_expression = name
            self.frame_index = 0

    def walk_in(self):
        self.animation_start_x = self.screen_width
        self.animation_progress = 0.0
        self.visible = True
        self.animating = True
        self.bounce_timer = 60  # frames of bounce after starting animation

    def walk_out(self):
        self.animation_start_x = self.x
        self.animation_progress = 0.0
        self.visible = False
        self.animating = True
      
    def key_out_green(self, img):
        data = np.array(img)
        red, green, blue, alpha = data.T
        green_mask = (red < 140) & (green > 180) & (blue < 140)
        data[..., 3][green_mask.T] = 0

        # Contract the non-transparent area inward by 3 pixels
        from scipy.ndimage import binary_erosion
        alpha_channel = data[..., 3] > 0
        eroded = binary_erosion(alpha_channel, iterations=3)
        data[..., 3] = np.where(eroded, data[..., 3], 0)

        return Image.fromarray(data)

    def load_all_expressions_with_progress(self):
        loading_window = tk.Toplevel(self.root)
        loading_window.overrideredirect(True)
        loading_window.geometry("300x30+{}+{}".format(self.screen_width // 2 - 150, self.screen_height // 2 - 15))
        progress = tk.DoubleVar()
        bar = tk.ttk.Progressbar(loading_window, variable=progress, maximum=100)
        bar.pack(fill='both', expand=True)

        expression_folders = [exp for exp in os.listdir(CLIP_DIR) if os.path.isdir(os.path.join(CLIP_DIR, exp))]
        total_files = sum(len([f for f in os.listdir(os.path.join(CLIP_DIR, exp)) if f.endswith('.jpg')]) for exp in expression_folders)
        loaded_files = 0

        for expression in expression_folders:
            path = os.path.join(CLIP_DIR, expression)
            frame_files = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')], key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x)))))
            frames = []
            for f in frame_files:
                try:
                    img = Image.open(f).convert('RGBA').resize((self.win_width, self.win_height), Image.Resampling.LANCZOS)
                    img = self.key_out_green(img)
                    frames.append(img)
                    loaded_files += 1
                    progress.set((loaded_files / total_files) * 100)
                    self.root.update()
                except Exception as e:
                    print(f"[ERROR] Failed to load image {f}: {e}")
            self.expressions[expression] = frames

        loading_window.destroy()


    def watch_api_variables(self):
        import api
        self.last_emotion = getattr(api, 'emotion', None)
        self.last_looking = getattr(api, 'Looking', None)
        self.last_waiting = getattr(api, 'waiting', None)
        self.last_talking = getattr(api, 'talking', None)
        self.last_output = getattr(api, 'output', '')
        self.last_length = getattr(api, 'length', 0.0)

        def check():
            importlib.reload(api)
            emotion = getattr(api, 'emotion', None)
            looking = getattr(api, 'Looking', None)
            waiting = getattr(api, 'waiting', None)
            talking = getattr(api, 'talking', None)
            output = getattr(api, 'output', None)
            length = getattr(api, 'length', None)
    
            if talking != self.last_talking:
                self.last_talking = talking
    
            if emotion != self.last_emotion:
                self.set_expression("normal")
                self.last_emotion = emotion

            if looking != self.last_looking:
                if looking:
                    self.previous_emotion = self.current_expression
                    self.set_expression('lookingatscreen')
                else:
                    self.set_expression(self.previous_emotion)
                self.last_looking = looking

            if waiting != self.last_waiting:
                if waiting:
                    self.walk_out()
                else:
                    self.walk_in()
                self.last_waiting = waiting

            if talking != self.last_talking and talking:
                self.speak(length, output)
            self.last_talking = talking

            self.root.after(100, check)

        check()

    def update_position(self):
        if self.animating:
            self.animation_progress += 1
            progress = min(self.animation_progress / self.animation_duration, 1)
            eased = 1 - (1 - progress) ** 3  # cubic ease out

            target_x = self.screen_width - int(self.win_width * 0.7) if self.visible else self.screen_width
            self.x = round(self.animation_start_x + (target_x - self.animation_start_x) * eased)

            y = self.screen_height - self.win_height + 40  # move window down by 40 pixels
            if self.bounce_timer > 0:
                bounce = int(12 * np.sin(progress * 12 * np.pi))
                y += bounce

            if progress >= 1:
                self.animating = False
                self.x = target_x

            self.root.geometry(f"{self.win_width}x{self.win_height}+{self.x}+{y}")
            if self.bounce_timer > 0:
                self.bounce_timer -= 10
        else:
            y = self.screen_height - self.win_height + 40
            self.root.geometry(f"{self.win_width}x{self.win_height}+{self.x}+{y}")
            
if __name__ == '__main__':
    root = tk.Tk()
    app = FaceApp(root)
    app.set_expression('normal')  # Replace 'a' with your default expression name if different
    root.mainloop()
