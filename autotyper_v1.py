import customtkinter as ctk
import tkinter as tk  # For specific constants or file dialogs
from tkinter import filedialog
import pyautogui
import time
import threading
import random

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
pyautogui.PAUSE = 0

# --- DATA ---
KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}
COMMON_SWAPS = ['th', 'he', 'an', 'in', 'er', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed']

class ModernAutoTyper(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Humanized AutoTyper Pro")
        self.geometry("700x950")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Text area expands
        
        self.is_typing = False
        self.settings_vars = {} # Store refs to slider variables

        self.build_ui()
        self.apply_profile("Lazy Student")

    def build_ui(self):
        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title_lbl = ctk.CTkLabel(self.header_frame, text="Humanized AutoTyper", font=ctk.CTkFont(size=24, weight="bold"))
        title_lbl.pack(side="left")

        self.topmost_switch = ctk.CTkSwitch(self.header_frame, text="Always on Top", command=self.toggle_topmost)
        self.topmost_switch.pack(side="right")

        # --- TOOLBAR ---
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        ctk.CTkButton(self.toolbar_frame, text="📂 Load File", width=100, command=self.load_file).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.toolbar_frame, text="📋 Paste", width=100, fg_color="gray", hover_color="#555", command=self.paste_clipboard).pack(side="left")

        # Profile Dropdown
        self.profile_var = ctk.StringVar(value="Lazy Student")
        self.profile_cb = ctk.CTkOptionMenu(self.toolbar_frame, variable=self.profile_var, 
                                            values=["Pro Typist", "Lazy Student", "Tired Human", "Just Type"],
                                            command=self.apply_profile, width=150)
        self.profile_cb.pack(side="right")
        ctk.CTkLabel(self.toolbar_frame, text="Profile:").pack(side="right", padx=10)

        # --- INPUT AREA ---
        self.textbox = ctk.CTkTextbox(self, font=("Consolas", 14), height=150, corner_radius=10)
        self.textbox.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.textbox.bind("<KeyRelease>", self.update_stats)

        # --- STATS BAR ---
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=0)
        
        self.lbl_word_count = ctk.CTkLabel(self.stats_frame, text="0 Words", text_color="gray")
        self.lbl_word_count.pack(side="left")
        
        self.lbl_est_time = ctk.CTkLabel(self.stats_frame, text="~ 0m 0s", text_color="gray")
        self.lbl_est_time.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=4, column=0, sticky="ew", padx=20, pady=(5, 20))
        self.progress_bar.set(0)

        # --- SETTINGS CONTAINER ---
        # We use a scrollable frame in case the window height is small
        self.settings_frame = ctk.CTkScrollableFrame(self, label_text="Parameters", height=300)
        self.settings_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=0)
        self.settings_frame.grid_columnconfigure(1, weight=1) # Sliders expand

        # 1. Speed
        self.add_section_header(self.settings_frame, "Speed & Fatigue", row=0)
        self.add_slider(self.settings_frame, "Base Speed (WPM)", "wpm", 10, 150, 70, row=1)
        self.add_slider(self.settings_frame, "Start Delay (sec)", "start_delay", 0, 15, 5, row=2)
        self.add_slider(self.settings_frame, "Fatigue Impact (%)", "fatigue", 0, 50, 10, row=3)

        # 2. Imperfections
        self.add_section_header(self.settings_frame, "Human Imperfections", row=4)
        self.add_slider(self.settings_frame, "Corrected Typos (%)", "correct", 0, 20, 4, row=5)
        self.add_slider(self.settings_frame, "Ignored Typos (%)", "persist", 0, 10, 1, row=6)
        self.add_slider(self.settings_frame, "Swap Errors (teh/the) (%)", "swap", 0, 10, 1.5, row=7)
        self.add_slider(self.settings_frame, "Double Space (%)", "double", 0, 10, 1, row=8)

        # 3. Behavioral
        self.add_section_header(self.settings_frame, "Behavioral Logic", row=9)
        self.add_slider(self.settings_frame, "Rethink Rate (%)", "rethink", 0, 10, 2, row=10)
        self.add_slider(self.settings_frame, "Paragraph Pause (sec)", "para_pause", 0, 5, 1.5, row=11)

        # --- FOOTER ACTIONS ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=20)
        
        self.status_label = ctk.CTkLabel(self.action_frame, text="Ready", font=("Segoe UI", 12, "bold"))
        self.status_label.pack(side="top", pady=(0, 10))

        self.btn_start = ctk.CTkButton(self.action_frame, text="START TYPING", height=50, 
                                       fg_color="#28a745", hover_color="#218838",
                                       font=("Segoe UI", 14, "bold"), command=self.initiate_start)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_stop = ctk.CTkButton(self.action_frame, text="STOP", height=50, 
                                      fg_color="#dc3545", hover_color="#c82333",
                                      state="disabled", font=("Segoe UI", 14, "bold"), command=self.stop_typing)
        self.btn_stop.pack(side="left", fill="x", expand=True, padx=(10, 0))

    # --- UI HELPERS ---
    def add_section_header(self, parent, text, row):
        lbl = ctk.CTkLabel(parent, text=text, text_color="#3b8ed0", font=("Segoe UI", 12, "bold"))
        lbl.grid(row=row, column=0, sticky="w", pady=(15, 5), padx=5)

    def add_slider(self, parent, text, key, min_val, max_val, default, row):
        # Label
        ctk.CTkLabel(parent, text=text).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        
        # Variable
        var = ctk.DoubleVar(value=default)
        self.settings_vars[key] = var
        
        # Slider
        slider = ctk.CTkSlider(parent, from_=min_val, to=max_val, variable=var, number_of_steps=100)
        slider.grid(row=row, column=1, sticky="ew", padx=10)
        slider.bind("<ButtonRelease-1>", self.update_stats) # Update stats on drag end
        
        # Value Display (Live updating)
        val_lbl = ctk.CTkLabel(parent, text=f"{default:.1f}", width=40)
        val_lbl.grid(row=row, column=2, padx=10)
        
        # Trace variable to update label
        def update_lbl(*args):
            val_lbl.configure(text=f"{var.get():.1f}")
        var.trace_add("write", update_lbl)

    # --- FUNCTIONALITY ---

    def toggle_topmost(self):
        self.attributes('-topmost', self.topmost_switch.get())

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.textbox.delete("1.0", "end")
                    self.textbox.insert("1.0", f.read())
                self.update_stats()
            except Exception as e:
                self.status_label.configure(text=f"Error: {e}", text_color="red")

    def paste_clipboard(self):
        try:
            content = self.clipboard_get()
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)
            self.update_stats()
        except:
            pass

    def apply_profile(self, choice):
        data = {
            "wpm": 70, "correct": 4.0, "persist": 1.0, "rethink": 2.0, "swap": 1.5, "double": 1.0, "fatigue": 10.0
        }
        
        if choice == "Pro Typist":
            data = {"wpm": 110, "correct": 1.5, "persist": 0.1, "rethink": 0.5, "swap": 0.5, "double": 0.1, "fatigue": 5.0}
        elif choice == "Lazy Student":
            data = {"wpm": 65, "correct": 6.0, "persist": 2.0, "rethink": 3.0, "swap": 2.5, "double": 2.0, "fatigue": 15.0}
        elif choice == "Tired Human":
            data = {"wpm": 45, "correct": 8.0, "persist": 3.0, "rethink": 5.0, "swap": 4.0, "double": 3.0, "fatigue": 30.0}
        elif choice == "Just Type":
            data = {"wpm": 90, "correct": 0.0, "persist": 0.0, "rethink": 0.0, "swap": 0.0, "double": 0.0, "fatigue": 0.0}

        # Update sliders
        for key, val in data.items():
            if key in self.settings_vars:
                self.settings_vars[key].set(val)
        
        self.update_stats()

    def update_stats(self, event=None):
        text = self.textbox.get("1.0", "end").strip()
        words = len(text.split())
        chars = len(text)
        self.lbl_word_count.configure(text=f"{words} Words")

        if chars == 0:
            self.lbl_est_time.configure(text="~ 0m 0s")
            return

        wpm = self.settings_vars['wpm'].get()
        base_delay = 60.0 / (max(wpm, 1) * 5.0)
        
        overhead = 0
        overhead += (chars * (self.settings_vars['correct'].get()/100)) * 0.6 
        overhead += (chars * (self.settings_vars['rethink'].get()/100)) * 2.0
        paragraphs = text.count('\n')
        overhead += paragraphs * self.settings_vars['para_pause'].get()

        total_seconds = (chars * base_delay) + overhead
        m, s = divmod(int(total_seconds), 60)
        self.lbl_est_time.configure(text=f"Est: {m}m {s}s")

    def initiate_start(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            self.status_label.configure(text="Please enter text first", text_color="#dc3545")
            return

        self.btn_start.configure(state="disabled", fg_color="gray")
        self.btn_stop.configure(state="normal", fg_color="#dc3545")
        
        threading.Thread(target=self.countdown_logic, args=(text,), daemon=True).start()

    def stop_typing(self):
        self.is_typing = False
        self.status_label.configure(text="Stopping...", text_color="#ffc107")

    def countdown_logic(self, text):
        delay = int(self.settings_vars['start_delay'].get())
        for i in range(delay, 0, -1):
            if self.btn_stop._state == "disabled": return
            self.status_label.configure(text=f"Starting in {i}...", text_color="#ffc107")
            time.sleep(1)
        
        self.is_typing = True
        self.status_label.configure(text="Typing in progress...", text_color="#28a745")
        self.type_text(text)

    # --- TYPING ENGINE (Core Logic) ---
    def get_neighbor(self, char):
        char_lower = char.lower()
        if char_lower in KEY_NEIGHBORS:
            neighbor = random.choice(KEY_NEIGHBORS[char_lower])
            return neighbor.upper() if char.isupper() else neighbor
        return char

    def press_key_human(self, char):
        if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?':
            pyautogui.keyDown('shift')
            time.sleep(random.uniform(0.05, 0.12))
            pyautogui.press(char.lower())
            time.sleep(random.uniform(0.05, 0.1))
            pyautogui.keyUp('shift')
        else:
            pyautogui.press(char)

    def type_text(self, text):
        try:
            # Fetch values
            wpm = self.settings_vars['wpm'].get()
            base_delay_target = 60.0 / (max(wpm, 1) * 5.0)
            
            prob_correct = self.settings_vars['correct'].get() / 100.0
            prob_persist = self.settings_vars['persist'].get() / 100.0
            prob_rethink = self.settings_vars['rethink'].get() / 100.0
            prob_swap = self.settings_vars['swap'].get() / 100.0
            prob_dbl_space = self.settings_vars['double'].get() / 100.0
            fatigue_factor = self.settings_vars['fatigue'].get() / 100.0
            para_pause = self.settings_vars['para_pause'].get()

            total_chars = len(text)
            chars_done = 0
            word_buffer = ""
            flow = 1.0 
            
            i = 0
            while i < len(text):
                if not self.is_typing: break
                
                char = text[i]
                chars_done += 1
                
                # Flow & Fatigue
                progress = chars_done / max(total_chars, 1)
                fatigue_mult = 1.0 + (progress * fatigue_factor)
                flow += random.uniform(-0.15, 0.15)
                flow = max(0.6, min(1.6, flow))

                # Update UI occasionally
                if i % 5 == 0:
                    percent = (chars_done / total_chars)
                    self.progress_bar.set(percent)

                # 1. Paragraph
                if char == '\n':
                    pyautogui.press('enter')
                    time.sleep(para_pause * random.uniform(0.8, 1.2))
                    i += 1
                    word_buffer = ""
                    continue

                # 2. Rethink
                if char in " .,?!":
                    if len(word_buffer) > 3 and random.random() < prob_rethink:
                        self.press_key_human(char)
                        time.sleep(base_delay_target * 4)
                        # Backspace logic
                        count = len(word_buffer) + 1
                        for _ in range(count):
                            pyautogui.press('backspace')
                            time.sleep(0.04)
                        time.sleep(0.8)
                        word_buffer = ""
                    else:
                        word_buffer = ""
                else:
                    word_buffer += char

                # 3. Swap (teh/the)
                if i + 1 < len(text) and char.isalnum() and random.random() < prob_swap:
                    next_char = text[i+1]
                    pair = (char + next_char).lower()
                    if pair in COMMON_SWAPS:
                        pyautogui.write(next_char)
                        time.sleep(base_delay_target * flow)
                        pyautogui.write(char)
                        time.sleep(0.25)
                        pyautogui.press('backspace')
                        pyautogui.press('backspace')
                        time.sleep(0.15)
                        # Fall through to type correctly

                # 4. Persistent Error
                if char.isalnum() and random.random() < prob_persist:
                    typo = self.get_neighbor(char)
                    pyautogui.write(typo)
                    i += 1
                    time.sleep(base_delay_target * flow)
                    continue

                # 5. Corrected Error
                if char.isalnum() and random.random() < prob_correct:
                    typo = self.get_neighbor(char)
                    pyautogui.write(typo)
                    time.sleep(0.25)
                    pyautogui.press('backspace')
                    time.sleep(0.1)

                # 6. Double Space
                if char == ' ' and random.random() < prob_dbl_space:
                    pyautogui.write("  ")
                    if random.random() < 0.5:
                        time.sleep(0.2)
                        pyautogui.press('backspace')
                    else:
                        i += 1
                        continue

                # Type
                self.press_key_human(char)
                
                # Delay
                delay = (base_delay_target * flow * fatigue_mult) * random.uniform(0.8, 1.2)
                time.sleep(delay)
                i += 1

            if self.is_typing:
                self.after(0, lambda: self.finish_typing(success=True))
        
        except pyautogui.FailSafeException:
            self.after(0, lambda: self.finish_typing(success=False, msg="FailSafe Triggered"))
        except Exception as e:
            self.after(0, lambda: self.finish_typing(success=False, msg=str(e)))

    def finish_typing(self, success, msg=""):
        self.is_typing = False
        self.btn_start.configure(state="normal", fg_color="#28a745")
        self.btn_stop.configure(state="disabled", fg_color="#dc3545")
        self.progress_bar.set(1.0 if success else 0)
        
        if success:
            self.status_label.configure(text="Typing Complete", text_color="#28a745")
        else:
            self.status_label.configure(text=msg or "Stopped", text_color="#dc3545")

if __name__ == "__main__":
    app = ModernAutoTyper()
    app.mainloop()