import sys
import time
import random
import pyautogui
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QPlainTextEdit, QProgressBar, QCheckBox, 
    QComboBox, QFileDialog, QSlider, QGridLayout, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon

# --- CONFIGURATION & DATA ---
pyautogui.PAUSE = 0

KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}

COMMON_SWAPS = ['th', 'he', 'an', 'in', 'er', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed']

# --- MODERN MINIMALIST STYLESHEET ---
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}

/* --- TEXT AREA --- */
QPlainTextEdit {
    background-color: #252526;
    border: none;
    border-radius: 6px;
    padding: 10px;
    color: #e0e0e0;
    font-family: 'Consolas', monospace;
    font-size: 11pt;
    selection-background-color: #264f78;
}

/* --- BUTTONS --- */
QPushButton {
    background-color: #333333;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    color: #e0e0e0;
}
QPushButton:hover { background-color: #3e3e42; }
QPushButton:pressed { background-color: #007acc; color: white; }

QPushButton#StartBtn {
    background-color: #2da44e; /* GitHub Green */
    color: white;
    font-weight: bold;
    padding: 10px;
    font-size: 11pt;
}
QPushButton#StartBtn:hover { background-color: #2c974b; }
QPushButton#StartBtn:disabled { background-color: #2b3036; color: #555; }

QPushButton#StopBtn {
    background-color: #c93c37;
    color: white;
    font-weight: bold;
}
QPushButton#StopBtn:hover { background-color: #b52a25; }

/* --- SLIDERS --- */
QSlider::groove:horizontal {
    border: 1px solid #3e3e42;
    height: 4px;
    background: #2d2d30;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #007acc;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #e0e0e0;
    border: 1px solid #e0e0e0;
    width: 12px;
    height: 12px;
    margin: -5px 0; /* center on groove */
    border-radius: 6px;
}

/* --- COMBOBOX --- */
QComboBox {
    background-color: #333333;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox::drop-down { border: none; }

/* --- PROGRESS BAR --- */
QProgressBar {
    border: none;
    background-color: #252526;
    height: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #007acc;
}

/* --- LABELS --- */
QLabel#Header { font-size: 12pt; font-weight: bold; color: #ffffff; }
QLabel#SubLabel { color: #858585; font-size: 9pt; }
QLabel#ValueLabel { color: #007acc; font-weight: bold; }
"""

# --- WORKER THREAD (UNCHANGED LOGIC) ---
class TypingWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str, str)
    finished_signal = pyqtSignal()
    
    def __init__(self, text, config):
        super().__init__()
        self.text = text
        self.config = config
        self.is_running = True

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

    def calculate_base_delay(self):
        wpm = self.config['wpm']
        return 60.0 / (max(wpm, 1) * 5.0)

    def run(self):
        delay = self.config['start_delay']
        for i in range(delay, 0, -1):
            if not self.is_running: return
            self.status.emit(f"Starting in {i}...", "#e5c07b") # Yellowish
            time.sleep(1)

        if not self.is_running: return
        self.status.emit("Typing...", "#98c379") # Greenish
        
        try:
            text = self.text
            base_delay_target = self.calculate_base_delay()
            
            # Unpack config
            prob_correct = self.config['correct_rate'] / 100.0
            prob_persist = self.config['persist_rate'] / 100.0
            prob_swap = self.config['swap_rate'] / 100.0
            prob_rethink = self.config['rethink_rate'] / 100.0
            prob_dbl_space = self.config['dbl_space_rate'] / 100.0
            fatigue_factor = self.config['fatigue_rate'] / 100.0
            para_pause = self.config['para_pause']

            total_chars = len(text)
            chars_done = 0
            word_buffer = ""
            flow = 1.0
            
            i = 0
            while i < len(text) and self.is_running:
                char = text[i]
                chars_done += 1
                
                if i % 5 == 0:
                    percent = int((chars_done / total_chars) * 100)
                    self.progress.emit(percent)

                progress_ratio = chars_done / max(total_chars, 1)
                fatigue_mult = 1.0 + (progress_ratio * fatigue_factor)
                flow += random.uniform(-0.15, 0.15)
                flow = max(0.6, min(1.6, flow))

                if char == '\n':
                    pyautogui.press('enter')
                    time.sleep(para_pause * random.uniform(0.8, 1.2))
                    i += 1
                    word_buffer = ""
                    continue

                if char in " .,?!":
                    if len(word_buffer) > 3 and random.random() < prob_rethink:
                        self.press_key_human(char)
                        time.sleep(base_delay_target * 4)
                        if random.random() < 0.7:
                            pyautogui.hotkey('ctrl', 'backspace')
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

                if char.isalnum() and random.random() < prob_persist:
                    typo = self.get_neighbor(char)
                    pyautogui.write(typo)
                    i += 1
                    time.sleep(base_delay_target * flow * fatigue_mult)
                    continue

                if char.isalnum() and random.random() < prob_correct:
                    typo = self.get_neighbor(char)
                    pyautogui.write(typo)
                    time.sleep(random.uniform(0.15, 0.4))
                    pyautogui.press('backspace')
                    time.sleep(random.uniform(0.05, 0.1))

                if char == ' ' and random.random() < prob_dbl_space:
                    pyautogui.write("  ")
                    if random.random() < 0.5:
                        time.sleep(0.2)
                        pyautogui.press('backspace')
                    else:
                        i += 1
                        continue

                self.press_key_human(char)
                delay_time = (base_delay_target * flow * fatigue_mult) * random.uniform(0.8, 1.2)
                time.sleep(delay_time)
                i += 1

            if self.is_running:
                self.status.emit("Complete", "#98c379")
                self.progress.emit(100)
                self.finished_signal.emit()

        except pyautogui.FailSafeException:
            self.status.emit("Failsafe (Corner) Triggered", "#e06c75")
            self.finished_signal.emit()
        except Exception as e:
            self.status.emit(f"Error: {str(e)}", "#e06c75")
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False

# --- MAIN APPLICATION ---
class AutoTyperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.apply_profile("Lazy Student")

    def init_ui(self):
        self.setWindowTitle("AutoTyper")
        self.resize(550, 700)
        self.setMinimumSize(450, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout
        self.layout = QVBoxLayout(central_widget)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # 1. TOOLBAR ROW
        top_bar = QHBoxLayout()
        
        lbl_title = QLabel("AutoTyper")
        lbl_title.setObjectName("Header")
        
        self.profile_combo = QComboBox()
        self.profile_combo.setFixedWidth(120)
        self.profile_combo.addItems(["Pro Typist", "Lazy Student", "Tired Human", "Just Type"])
        self.profile_combo.currentTextChanged.connect(self.apply_profile)
        
        btn_load = QPushButton("Load")
        btn_load.clicked.connect(self.load_file)
        btn_load.setToolTip("Load from .txt file")
        
        btn_paste = QPushButton("Paste")
        btn_paste.clicked.connect(self.paste_clipboard)
        btn_paste.setToolTip("Paste from Clipboard")

        self.top_check = QCheckBox("Top")
        self.top_check.setToolTip("Always on Top")
        self.top_check.stateChanged.connect(self.toggle_topmost)

        top_bar.addWidget(lbl_title)
        top_bar.addStretch()
        top_bar.addWidget(self.top_check)
        top_bar.addWidget(self.profile_combo)
        top_bar.addWidget(btn_load)
        top_bar.addWidget(btn_paste)
        
        self.layout.addLayout(top_bar)

        # 2. TEXT AREA (Expands)
        self.text_area = QPlainTextEdit()
        self.text_area.setPlaceholderText("Paste or type text here...")
        self.text_area.textChanged.connect(self.update_stats)
        self.layout.addWidget(self.text_area)

        # 3. STATS BAR (Minimal)
        stats_layout = QHBoxLayout()
        self.lbl_stats = QLabel("0 words | Est: 0m 0s")
        self.lbl_stats.setObjectName("SubLabel")
        
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_lbl.setStyleSheet("color: #007acc; font-weight: bold;")
        
        stats_layout.addWidget(self.lbl_stats)
        stats_layout.addStretch()
        stats_layout.addWidget(self.status_lbl)
        self.layout.addLayout(stats_layout)

        # 4. PROGRESS LINE
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # 5. SETTINGS GRID (Compact)
        # We use a Grid Layout to pack sliders efficiently
        # Col 0: Label, Col 1: Slider, Col 2: Value
        # Col 3: Spacer, Col 4: Label, Col 5: Slider, Col 6: Value
        
        settings_frame = QFrame()
        settings_frame.setStyleSheet("background-color: #252526; border-radius: 6px;")
        grid = QGridLayout(settings_frame)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(10)

        # Left Column (Speed)
        self.slider_wpm = self.add_slider_row(grid, 0, "Speed (WPM)", 10, 200, 70)
        self.slider_delay = self.add_slider_row(grid, 1, "Start Delay", 1, 15, 5)
        self.slider_fatigue = self.add_slider_row(grid, 2, "Fatigue %", 0, 50, 10)
        self.slider_para = self.add_slider_row(grid, 3, "Para Pause", 0, 5, 1.5, is_float=True)

        # Right Column (Errors/Behavior)
        self.slider_correct = self.add_slider_row(grid, 0, "Typo Fix %", 0, 20, 4, is_float=True, col_offset=3)
        self.slider_persist = self.add_slider_row(grid, 1, "Typo Keep %", 0, 10, 1, is_float=True, col_offset=3)
        self.slider_swap = self.add_slider_row(grid, 2, "Swap Err %", 0, 10, 1.5, is_float=True, col_offset=3)
        self.slider_rethink = self.add_slider_row(grid, 3, "Rethink %", 0, 10, 2, is_float=True, col_offset=3)
        # Hidden double space slider logic for compact view (handled in background default)
        self.slider_double = QSlider() 
        self.slider_double.scale_factor = 10
        self.set_slider_val(self.slider_double, 1.0) # Default hidden value

        self.layout.addWidget(settings_frame)

        # 6. ACTION BUTTONS
        btn_layout = QHBoxLayout()
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.clicked.connect(self.stop_typing)
        self.btn_stop.setEnabled(False)
        
        self.btn_start = QPushButton("START TYPING")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_typing)

        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_start)
        self.layout.addLayout(btn_layout)

    # --- UI HELPERS ---
    def add_slider_row(self, grid, row, label, min_v, max_v, default_v, is_float=False, col_offset=0):
        # Label
        lbl = QLabel(label)
        lbl.setObjectName("SubLabel")
        grid.addWidget(lbl, row, 0 + col_offset)
        
        # Slider
        slider = QSlider(Qt.Orientation.Horizontal)
        scale = 10 if is_float else 1
        slider.scale_factor = scale
        slider.setRange(int(min_v * scale), int(max_v * scale))
        slider.setValue(int(default_v * scale))
        grid.addWidget(slider, row, 1 + col_offset)
        
        # Value Label
        val_lbl = QLabel(str(default_v))
        val_lbl.setObjectName("ValueLabel")
        val_lbl.setFixedWidth(30)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid.addWidget(val_lbl, row, 2 + col_offset)

        # Connection
        def update_lbl(val):
            display_val = val / scale if is_float else val
            val_lbl.setText(str(display_val))
            self.update_stats()
            
        slider.valueChanged.connect(update_lbl)
        return slider

    def get_slider_val(self, slider):
        return slider.value() / slider.scale_factor

    def set_slider_val(self, slider, val):
        slider.setValue(int(val * slider.scale_factor))

    def toggle_topmost(self, state):
        flags = self.windowFlags()
        if state:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text (*.txt);;All (*)")
        if fname:
            with open(fname, 'r', encoding='utf-8') as f:
                self.text_area.setPlainText(f.read())

    def paste_clipboard(self):
        self.text_area.setPlainText(QApplication.clipboard().text())

    def apply_profile(self, name):
        # WPM, Delay, Fatigue, Correct, Persist, Swap, Rethink, Para
        if name == "Pro Typist":
            data = [110, 5, 5, 1.5, 0.1, 0.5, 0.5, 0.1]
        elif name == "Lazy Student":
            data = [65, 5, 15, 6.0, 2.0, 2.5, 3.0, 1.5]
        elif name == "Tired Human":
            data = [45, 5, 30, 8.0, 3.0, 4.0, 5.0, 2.0]
        else: # Just Type
            data = [90, 3, 0, 0.0, 0.0, 0.0, 0.0, 0.0]

        sliders = [self.slider_wpm, self.slider_delay, self.slider_fatigue, 
                   self.slider_correct, self.slider_persist, self.slider_swap,
                   self.slider_rethink, self.slider_para]
        
        for s, v in zip(sliders, data):
            self.set_slider_val(s, v)

    def update_stats(self):
        text = self.text_area.toPlainText().strip()
        words = len(text.split())
        chars = len(text)
        
        wpm = self.get_slider_val(self.slider_wpm)
        if chars > 0 and wpm > 0:
            base_delay = 60.0 / (wpm * 5.0)
            overhead = (chars * (self.get_slider_val(self.slider_correct)/100)) * 0.6
            overhead += (chars * (self.get_slider_val(self.slider_rethink)/100)) * 2.0
            overhead += text.count('\n') * self.get_slider_val(self.slider_para)
            total_seconds = (chars * base_delay) + overhead
            m, s = divmod(int(total_seconds), 60)
            self.lbl_stats.setText(f"{words} words | Est: {m}m {s}s")
        else:
            self.lbl_stats.setText("0 words | Est: 0m 0s")

    def start_typing(self):
        text = self.text_area.toPlainText()
        if not text:
            self.status_lbl.setText("No text!")
            self.status_lbl.setStyleSheet("color: #c93c37; font-weight: bold;")
            return

        config = {
            'wpm': self.get_slider_val(self.slider_wpm),
            'start_delay': int(self.get_slider_val(self.slider_delay)),
            'fatigue_rate': self.get_slider_val(self.slider_fatigue),
            'correct_rate': self.get_slider_val(self.slider_correct),
            'persist_rate': self.get_slider_val(self.slider_persist),
            'swap_rate': self.get_slider_val(self.slider_swap),
            'rethink_rate': self.get_slider_val(self.slider_rethink),
            'para_pause': self.get_slider_val(self.slider_para),
            'dbl_space_rate': self.get_slider_val(self.slider_double)
        }

        self.worker = TypingWorker(text, config)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.handle_status)
        self.worker.finished_signal.connect(self.on_typing_finished)
        self.worker.start()
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.text_area.setEnabled(False)
        self.profile_combo.setEnabled(False)

    def stop_typing(self):
        if self.worker:
            self.worker.stop()
            self.status_lbl.setText("Stopping...")

    def on_typing_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.text_area.setEnabled(True)
        self.profile_combo.setEnabled(True)
        self.worker = None

    def handle_status(self, msg, color):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = AutoTyperApp()
    window.show()
    sys.exit(app.exec())