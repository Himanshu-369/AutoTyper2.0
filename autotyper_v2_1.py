import sys
import time
import random
import pyautogui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, 
                             QSlider, QComboBox, QCheckBox, QFileDialog, 
                             QProgressBar, QGroupBox, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette

# --- CONFIGURATION ---
pyautogui.PAUSE = 0 

# --- DATA ---
KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}
COMMON_SWAPS = ['th', 'he', 'an', 'in', 'er', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed']

# --- THEME COLORS ---
C_BG = "#121212"
C_SURFACE = "#1e1e1e"
C_ACCENT = "#3b8ed0"
C_TEXT = "#e0e0e0"
C_SUBTEXT = "#a0a0a0"
C_INPUT = "#2d2d30"
C_SUCCESS = "#28a745"
C_DANGER = "#dc3545"

# --- WORKER THREAD ---
class TypingWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str, str) # text, color_hex
    finished_signal = pyqtSignal()

    def __init__(self, text, config):
        super().__init__()
        self.text = text
        self.config = config
        self.is_running = True

    def run(self):
        try:
            self.countdown()
            if self.is_running:
                self.type_content()
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}", C_DANGER)
        finally:
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False

    def countdown(self):
        delay = self.config['start_delay']
        for i in range(delay, 0, -1):
            if not self.is_running: return
            self.status_signal.emit(f"Starting in {i}...", "#ffc107")
            time.sleep(1)
        self.status_signal.emit("Typing...", C_SUCCESS)

    def calculate_base_delay(self):
        wpm = self.config['wpm']
        # Standard: 5 chars per word. 60 sec / (WPM * 5)
        return 60.0 / (max(wpm, 1) * 5.0)

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

    def type_content(self):
        text = self.text
        base_delay_target = self.calculate_base_delay()
        
        # Unpack config (percentages converted to 0.0-1.0 range)
        prob_correct = self.config['correct_rate'] / 100.0
        prob_persist = self.config['persist_rate'] / 100.0
        prob_rethink = self.config['rethink_rate'] / 100.0
        prob_swap = self.config['swap_rate'] / 100.0
        prob_dbl_space = self.config['double_rate'] / 100.0
        fatigue_factor = self.config['fatigue_rate'] / 100.0
        
        total_chars = len(text)
        chars_done = 0
        word_buffer = ""
        flow = 1.0

        i = 0
        while i < len(text):
            if not self.is_running: break

            char = text[i]
            chars_done += 1
            
            # Update Progress
            if i % 5 == 0:
                pct = int((chars_done / total_chars) * 100)
                self.progress_signal.emit(pct)

            # Fatigue & Flow
            progress = chars_done / max(total_chars, 1)
            fatigue_mult = 1.0 + (progress * fatigue_factor)
            flow += random.uniform(-0.15, 0.15)
            flow = max(0.6, min(1.6, flow))

            # 1. Paragraph Pause
            if char == '\n':
                pyautogui.press('enter')
                time.sleep(self.config['para_pause'] * random.uniform(0.8, 1.2))
                i += 1
                word_buffer = ""
                continue

            # 2. Rethink
            if char in " .,?!":
                if len(word_buffer) > 3 and random.random() < prob_rethink:
                    self.press_key_human(char)
                    time.sleep(base_delay_target * 4)
                    
                    if random.random() < 0.7:
                        pyautogui.hotkey('ctrl', 'backspace') # Pro deletion
                        pyautogui.press('backspace') 
                    else:
                        for _ in range(len(word_buffer) + 1):
                            pyautogui.press('backspace')
                            time.sleep(0.04)
                    
                    time.sleep(random.uniform(0.5, 1.2))
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
                    time.sleep(0.2)
                    pyautogui.press('backspace')
                    pyautogui.press('backspace')
                    time.sleep(0.15)
                    # Fall through to type correctly

            # 4. Persistent Error (Ignored)
            if char.isalnum() and random.random() < prob_persist:
                typo = self.get_neighbor(char)
                pyautogui.write(typo)
                i += 1
                time.sleep(base_delay_target * flow * fatigue_mult)
                continue

            # 5. Corrected Error
            if char.isalnum() and random.random() < prob_correct:
                typo = self.get_neighbor(char)
                pyautogui.write(typo)
                time.sleep(random.uniform(0.15, 0.4))
                pyautogui.press('backspace')
                time.sleep(random.uniform(0.05, 0.1))

            # 6. Double Space
            if char == ' ' and random.random() < prob_dbl_space:
                pyautogui.write("  ")
                if random.random() < 0.5:
                    time.sleep(0.2)
                    pyautogui.press('backspace')
                else:
                    i += 1
                    continue

            # Execute
            self.press_key_human(char)
            
            # Delay
            delay = (base_delay_target * flow * fatigue_mult) * random.uniform(0.8, 1.2)
            time.sleep(delay)
            i += 1
        
        if self.is_running:
            self.status_signal.emit("Complete", C_SUCCESS)
            self.progress_signal.emit(100)

# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Humanized AutoTyper (PyQt6)")
        self.resize(700, 900)
        self.worker = None
        self.setup_ui()
        self.apply_theme()
        self.apply_profile("Lazy Student") # Default

    def apply_theme(self):
        style = f"""
            QMainWindow {{ background-color: {C_BG}; }}
            QWidget {{ color: {C_TEXT}; font-family: 'Segoe UI', sans-serif; font-size: 14px; }}
            QGroupBox {{ border: 1px solid {C_INPUT}; border-radius: 6px; margin-top: 20px; font-weight: bold; color: {C_ACCENT}; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
            QPlainTextEdit {{ background-color: {C_INPUT}; border: none; padding: 10px; font-family: Consolas; font-size: 14px; color: {C_TEXT}; }}
            QPushButton {{ background-color: {C_SURFACE}; border-radius: 4px; padding: 8px; color: {C_TEXT}; }}
            QPushButton:hover {{ background-color: {C_INPUT}; }}
            QSlider::groove:horizontal {{ height: 6px; background: {C_INPUT}; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {C_ACCENT}; width: 16px; margin: -5px 0; border-radius: 8px; }}
            QComboBox {{ background-color: {C_INPUT}; border: none; padding: 5px; }}
            QProgressBar {{ border: none; background-color: {C_INPUT}; height: 8px; border-radius: 4px; text-align: center; }}
            QProgressBar::chunk {{ background-color: {C_ACCENT}; border-radius: 4px; }}
        """
        self.setStyleSheet(style)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- HEADER ---
        header = QHBoxLayout()
        title = QLabel("Humanized AutoTyper")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {C_ACCENT};")
        header.addWidget(title)
        
        self.chk_topmost = QCheckBox("Always on Top")
        self.chk_topmost.stateChanged.connect(self.toggle_topmost)
        header.addStretch()
        header.addWidget(self.chk_topmost)
        layout.addLayout(header)

        # --- TOOLBAR ---
        toolbar = QHBoxLayout()
        
        btn_load = QPushButton("📂 Load File")
        btn_load.clicked.connect(self.load_file)
        btn_paste = QPushButton("📋 Paste Clipboard")
        btn_paste.clicked.connect(self.paste_clipboard)
        
        lbl_profile = QLabel("Profile:")
        lbl_profile.setStyleSheet(f"color: {C_SUBTEXT}; margin-left: 10px;")
        
        self.combo_profile = QComboBox()
        self.combo_profile.addItems(["Pro Typist", "Lazy Student", "Tired Human", "Just Type"])
        self.combo_profile.currentTextChanged.connect(self.apply_profile)

        toolbar.addWidget(btn_load)
        toolbar.addWidget(btn_paste)
        toolbar.addWidget(lbl_profile)
        toolbar.addWidget(self.combo_profile)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # --- INPUT AREA ---
        self.text_area = QPlainTextEdit()
        self.text_area.setPlaceholderText("Paste or type text here to be auto-typed...")
        self.text_area.textChanged.connect(self.update_stats)
        self.text_area.setMaximumHeight(150)
        layout.addWidget(self.text_area)

        # --- STATS ---
        stats_layout = QHBoxLayout()
        self.lbl_word_count = QLabel("0 Words")
        self.lbl_est_time = QLabel("~ 0m 0s")
        self.lbl_word_count.setStyleSheet(f"color: {C_SUBTEXT};")
        self.lbl_est_time.setStyleSheet(f"color: {C_SUBTEXT};")
        stats_layout.addWidget(self.lbl_word_count)
        stats_layout.addStretch()
        stats_layout.addWidget(self.lbl_est_time)
        layout.addLayout(stats_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- SETTINGS GRID ---
        self.settings_container = QWidget()
        settings_grid = QGridLayout(self.settings_container)
        settings_grid.setContentsMargins(0,0,0,0)

        # 1. Speed Group
        grp_speed = QGroupBox("SPEED & FATIGUE")
        v_speed = QVBoxLayout(grp_speed)
        self.sl_wpm = self.create_slider(v_speed, "Base Speed (WPM)", 10, 150, 70)
        self.sl_start = self.create_slider(v_speed, "Start Delay (sec)", 1, 10, 5)
        self.sl_fatigue = self.create_slider(v_speed, "Fatigue Impact (%)", 0, 50, 10)
        settings_grid.addWidget(grp_speed, 0, 0)

        # 2. Errors Group
        grp_error = QGroupBox("HUMAN ERRORS")
        v_error = QVBoxLayout(grp_error)
        self.sl_correct = self.create_slider(v_error, "Typos (Corrected) %", 0, 200, 40, scale=0.1) # 0-20.0%
        self.sl_persist = self.create_slider(v_error, "Typos (Ignored) %", 0, 100, 10, scale=0.1)
        self.sl_swap = self.create_slider(v_error, "Swap (teh/the) %", 0, 100, 15, scale=0.1)
        settings_grid.addWidget(grp_error, 0, 1)

        # 3. Behavior Group
        grp_behav = QGroupBox("BEHAVIOR")
        v_behav = QVBoxLayout(grp_behav)
        self.sl_rethink = self.create_slider(v_behav, "Word Rethink %", 0, 100, 20, scale=0.1)
        self.sl_pause = self.create_slider(v_behav, "Paragraph Pause (s)", 0, 50, 15, scale=0.1)
        self.sl_double = self.create_slider(v_behav, "Double Space %", 0, 50, 10, scale=0.1)
        settings_grid.addWidget(grp_behav, 1, 0, 1, 2)

        layout.addWidget(self.settings_container)

        # --- STATUS & BUTTONS ---
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet(f"font-weight: bold; color: {C_ACCENT}; font-size: 16px;")
        layout.addWidget(self.lbl_status)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Typing")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet(f"background-color: {C_SUCCESS}; color: white; font-weight: bold; font-size: 16px;")
        self.btn_start.clicked.connect(self.start_typing)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setFixedHeight(50)
        self.btn_stop.setStyleSheet(f"background-color: {C_INPUT}; color: #888; font-weight: bold; font-size: 16px;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_typing)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

    # --- UI HELPERS ---
    def create_slider(self, layout, label_text, min_val, max_val, default_val, scale=1):
        """Creates a slider with a dynamic label value"""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        
        lbl_name = QLabel(label_text)
        lbl_name.setStyleSheet("font-size: 12px;")
        
        # Determine initial display value
        initial_display = default_val * scale
        if scale < 1:
            lbl_value = QLabel(f"{initial_display:.1f}")
        else:
            lbl_value = QLabel(f"{int(initial_display)}")
        
        lbl_value.setFixedWidth(40)
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)

        # Logic to update label
        def update_lbl(val):
            real_val = val * scale
            if scale < 1:
                lbl_value.setText(f"{real_val:.1f}")
            else:
                lbl_value.setText(f"{int(real_val)}")
            self.update_stats()

        slider.valueChanged.connect(update_lbl)

        row.addWidget(lbl_name)
        row.addWidget(slider)
        row.addWidget(lbl_value)
        layout.addWidget(container)
        
        # Attach a custom property to easier retrieval later if needed, 
        # though we will read .value() directly
        slider.scale_factor = scale 
        return slider

    def toggle_topmost(self):
        if self.chk_topmost.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.text_area.setPlainText(f.read())

    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        self.text_area.setPlainText(clipboard.text())

    # --- LOGIC ---
    def apply_profile(self, name):
        # Block stats update temporarily to prevent lag
        self.blockSignals(True)
        if name == "Pro Typist":
            self.sl_wpm.setValue(110)
            self.sl_correct.setValue(15) # 1.5%
            self.sl_persist.setValue(1)  # 0.1%
            self.sl_rethink.setValue(5)
            self.sl_swap.setValue(5)
            self.sl_fatigue.setValue(5)
        elif name == "Lazy Student":
            self.sl_wpm.setValue(65)
            self.sl_correct.setValue(60) # 6.0%
            self.sl_persist.setValue(20) # 2.0%
            self.sl_rethink.setValue(30)
            self.sl_swap.setValue(25)
            self.sl_fatigue.setValue(15)
        elif name == "Tired Human":
            self.sl_wpm.setValue(45)
            self.sl_correct.setValue(80)
            self.sl_persist.setValue(30)
            self.sl_rethink.setValue(50)
            self.sl_swap.setValue(40)
            self.sl_fatigue.setValue(30)
        elif name == "Just Type":
            self.sl_wpm.setValue(90)
            self.sl_correct.setValue(0)
            self.sl_persist.setValue(0)
            self.sl_rethink.setValue(0)
            self.sl_swap.setValue(0)
            self.sl_fatigue.setValue(0)
        self.blockSignals(False)
        self.update_stats()

    def update_stats(self):
        text = self.text_area.toPlainText()
        words = len(text.split())
        self.lbl_word_count.setText(f"{words} Words")
        
        if not text:
            self.lbl_est_time.setText("~ 0m 0s")
            return

        wpm = self.sl_wpm.value()
        base_delay = 60.0 / (max(wpm, 1) * 5.0)
        chars = len(text)
        
        # Rough estimation of overhead
        overhead = 0
        overhead += (chars * (self.sl_correct.value() * 0.1 / 100)) * 0.6
        overhead += (chars * (self.sl_rethink.value() * 0.1 / 100)) * 2.0
        paragraphs = text.count('\n')
        overhead += paragraphs * (self.sl_pause.value() * 0.1)

        total_seconds = (chars * base_delay) + overhead
        m, s = divmod(int(total_seconds), 60)
        self.lbl_est_time.setText(f"Est: {m}m {s}s")

    def get_config_dict(self):
        return {
            'wpm': self.sl_wpm.value(),
            'start_delay': self.sl_start.value(),
            'fatigue_rate': self.sl_fatigue.value(),
            'correct_rate': self.sl_correct.value() * 0.1,
            'persist_rate': self.sl_persist.value() * 0.1,
            'swap_rate': self.sl_swap.value() * 0.1,
            'rethink_rate': self.sl_rethink.value() * 0.1,
            'double_rate': self.sl_double.value() * 0.1,
            'para_pause': self.sl_pause.value() * 0.1
        }

    def start_typing(self):
        text = self.text_area.toPlainText()
        if not text.strip():
            self.lbl_status.setText("Text area is empty!")
            self.lbl_status.setStyleSheet(f"color: {C_DANGER}; font-size: 16px; font-weight: bold;")
            return

        # Disable UI
        self.settings_container.setEnabled(False)
        self.text_area.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet(f"background-color: {C_INPUT}; color: #888;")
        self.btn_stop.setEnabled(True)
        self.btn_stop.setStyleSheet(f"background-color: {C_DANGER}; color: white;")
        
        # Start Worker
        config = self.get_config_dict()
        self.worker = TypingWorker(text, config)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.on_worker_status)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def stop_typing(self):
        if self.worker:
            self.worker.stop()
            self.lbl_status.setText("Stopping...")

    def on_worker_status(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")

    def on_worker_finished(self):
        # Reset UI
        self.settings_container.setEnabled(True)
        self.text_area.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.btn_start.setStyleSheet(f"background-color: {C_SUCCESS}; color: white; font-weight: bold; font-size: 16px;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(f"background-color: {C_INPUT}; color: #888; font-weight: bold; font-size: 16px;")
        
        if self.progress_bar.value() < 100:
            self.lbl_status.setText("Stopped")
            self.lbl_status.setStyleSheet(f"color: {C_DANGER}; font-size: 16px; font-weight: bold;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())