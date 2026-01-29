import sys
import time
import random
import pyautogui
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QPlainTextEdit, QProgressBar, QCheckBox, 
    QComboBox, QFileDialog, QGroupBox, QSlider, QFrame, QStyleFactory
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette, QIcon, QFont, QTextCursor

# --- CONFIGURATION & DATA ---
pyautogui.PAUSE = 0

KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}

COMMON_SWAPS = ['th', 'he', 'an', 'in', 'er', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed']

# --- MODERN STYLESHEET ---
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}
QGroupBox {
    border: 1px solid #333;
    border-radius: 6px;
    margin-top: 10px;
    font-weight: bold;
    color: #3b8ed0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QPlainTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 4px;
    color: #e0e0e0;
    font-family: 'Consolas', monospace;
    font-size: 11pt;
    selection-background-color: #3b8ed0;
}
QPushButton {
    background-color: #2d2d30;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    color: #e0e0e0;
}
QPushButton:hover {
    background-color: #3e3e42;
}
QPushButton:pressed {
    background-color: #007acc;
}
QPushButton#StartBtn {
    background-color: #28a745;
    color: white;
    font-weight: bold;
    font-size: 11pt;
}
QPushButton#StartBtn:hover {
    background-color: #218838;
}
QPushButton#StopBtn {
    background-color: #dc3545;
    color: white;
    font-weight: bold;
    font-size: 11pt;
}
QPushButton#StopBtn:hover {
    background-color: #c82333;
}
QPushButton:disabled {
    background-color: #333;
    color: #777;
}
QProgressBar {
    border: none;
    background-color: #2d2d30;
    border-radius: 2px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #3b8ed0;
    border-radius: 2px;
}
QSlider::groove:horizontal {
    border: 1px solid #333;
    height: 4px;
    background: #2d2d30;
    margin: 2px 0;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #3b8ed0;
    border: 1px solid #3b8ed0;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}
QComboBox {
    background-color: #2d2d30;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 4px;
}
"""

# --- WORKER THREAD ---
class TypingWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str, str) # message, color info
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
        # Countdown
        delay = self.config['start_delay']
        for i in range(delay, 0, -1):
            if not self.is_running: return
            self.status.emit(f"Starting in {i}...", "#ffc107")
            time.sleep(1)

        if not self.is_running: return
        self.status.emit("Typing...", "#28a745")
        
        try:
            text = self.text
            base_delay_target = self.calculate_base_delay()
            
            # Unpack config
            prob_correct = self.config['correct_rate'] / 100.0
            prob_persist = self.config['persist_rate'] / 100.0
            prob_rethink = self.config['rethink_rate'] / 100.0
            prob_swap = self.config['swap_rate'] / 100.0
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
                
                # Update progress
                if i % 5 == 0:
                    percent = int((chars_done / total_chars) * 100)
                    self.progress.emit(percent)

                # Fatigue & Flow
                progress_ratio = chars_done / max(total_chars, 1)
                fatigue_mult = 1.0 + (progress_ratio * fatigue_factor)
                flow += random.uniform(-0.15, 0.15)
                flow = max(0.6, min(1.6, flow))

                # 1. Paragraph Pause
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
                        
                        # Delete word
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

                # 3. Swap Error
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
                        # Don't increment i, retry normally

                # 4. Persistent Error
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
                delay_time = (base_delay_target * flow * fatigue_mult) * random.uniform(0.8, 1.2)
                time.sleep(delay_time)
                i += 1

            if self.is_running:
                self.status.emit("Done", "#28a745")
                self.progress.emit(100)
                self.finished_signal.emit()

        except pyautogui.FailSafeException:
            self.status.emit("Failsafe Triggered", "#dc3545")
            self.finished_signal.emit()
        except Exception as e:
            self.status.emit(f"Error: {str(e)}", "#dc3545")
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
        self.setWindowTitle("Humanized AutoTyper (PyQt6)")
        self.resize(600, 850)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("Humanized AutoTyper")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #3b8ed0;")
        
        self.top_check = QCheckBox("Always on Top")
        self.top_check.stateChanged.connect(self.toggle_topmost)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.top_check)
        main_layout.addLayout(header_layout)

        # --- TOOLBAR ---
        toolbar = QHBoxLayout()
        
        btn_load = QPushButton("📂 Load File")
        btn_load.clicked.connect(self.load_file)
        
        btn_paste = QPushButton("📋 Paste Clipboard")
        btn_paste.clicked.connect(self.paste_clipboard)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Pro Typist", "Lazy Student", "Tired Human", "Just Type"])
        self.profile_combo.currentTextChanged.connect(self.apply_profile)
        
        toolbar.addWidget(btn_load)
        toolbar.addWidget(btn_paste)
        toolbar.addWidget(QLabel("Profile:"))
        toolbar.addWidget(self.profile_combo)
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # --- TEXT INPUT ---
        self.text_area = QPlainTextEdit()
        self.text_area.setPlaceholderText("Enter or paste text here to auto-type...")
        self.text_area.textChanged.connect(self.update_stats)
        main_layout.addWidget(self.text_area)

        # --- STATS ---
        stats_layout = QHBoxLayout()
        self.lbl_words = QLabel("0 Words")
        self.lbl_est = QLabel("~ 0m 0s")
        self.lbl_words.setStyleSheet("color: #a0a0a0;")
        self.lbl_est.setStyleSheet("color: #a0a0a0;")
        
        stats_layout.addWidget(self.lbl_words)
        stats_layout.addStretch()
        stats_layout.addWidget(self.lbl_est)
        main_layout.addLayout(stats_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # --- SETTINGS GROUPS ---
        # 1. Speed
        speed_group = QGroupBox("SPEED & FATIGUE")
        speed_layout = QVBoxLayout()
        self.slider_wpm = self.create_slider(speed_layout, "Base Speed (WPM)", 10, 200, 70)
        self.slider_delay = self.create_slider(speed_layout, "Start Delay (sec)", 1, 15, 5)
        self.slider_fatigue = self.create_slider(speed_layout, "Fatigue Impact (%)", 0, 50, 10)
        speed_group.setLayout(speed_layout)
        main_layout.addWidget(speed_group)

        # 2. Imperfections
        error_group = QGroupBox("HUMAN IMPERFECTIONS")
        error_layout = QVBoxLayout()
        self.slider_correct = self.create_slider(error_layout, "Typos (Corrected) %", 0, 20, 4, is_float=True)
        self.slider_persist = self.create_slider(error_layout, "Typos (Ignored) %", 0, 10, 1, is_float=True)
        self.slider_swap = self.create_slider(error_layout, "Swap Errors (teh/the) %", 0, 10, 1.5, is_float=True)
        error_group.setLayout(error_layout)
        main_layout.addWidget(error_group)

        # 3. Behavior
        behav_group = QGroupBox("BEHAVIOR")
        behav_layout = QVBoxLayout()
        self.slider_rethink = self.create_slider(behav_layout, "Word Rethink Rate %", 0, 10, 2, is_float=True)
        self.slider_para = self.create_slider(behav_layout, "Paragraph Pause (sec)", 0, 5, 1.5, is_float=True)
        self.slider_double = self.create_slider(behav_layout, "Double Space Rate %", 0, 10, 1, is_float=True)
        behav_group.setLayout(behav_layout)
        main_layout.addWidget(behav_group)

        # --- FOOTER ---
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet("font-weight: bold; color: #3b8ed0;")
        main_layout.addWidget(self.status_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Typing")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_typing)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setCursor(Qt.CursorShape.ArrowCursor)
        self.btn_stop.clicked.connect(self.stop_typing)
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        main_layout.addLayout(btn_layout)

    # --- UI HELPERS ---
    def create_slider(self, layout, label_text, min_val, max_val, default_val, is_float=False):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(180)
        
        # Scale for sliders that need decimals (0-10.0 becomes 0-100)
        scale = 10 if is_float else 1
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(int(min_val * scale), int(max_val * scale))
        slider.setValue(int(default_val * scale))
        
        val_lbl = QLabel(str(default_val))
        val_lbl.setFixedWidth(40)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Update label on change
        def update_lbl(val):
            display_val = val / scale if is_float else val
            val_lbl.setText(str(display_val))
            self.update_stats()

        slider.valueChanged.connect(update_lbl)
        
        row.addWidget(lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)
        layout.addWidget(container)
        
        # Attach the scale factor to the slider object for later retrieval
        slider.scale_factor = scale 
        return slider

    def get_slider_val(self, slider):
        return slider.value() / slider.scale_factor

    def set_slider_val(self, slider, val):
        slider.setValue(int(val * slider.scale_factor))

    # --- LOGIC ---
    def toggle_topmost(self, state):
        if state:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt);;All Files (*)")
        if fname:
            with open(fname, 'r', encoding='utf-8') as f:
                self.text_area.setPlainText(f.read())

    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        self.text_area.setPlainText(clipboard.text())

    def apply_profile(self, name):
        # Data mapping
        if name == "Pro Typist":
            data = [110, 5, 5.0, 1.5, 0.1, 0.5, 0.5, 0.5, 0.1]
        elif name == "Lazy Student":
            data = [65, 5, 15.0, 6.0, 2.0, 2.5, 3.0, 1.5, 2.0]
        elif name == "Tired Human":
            data = [45, 5, 30.0, 8.0, 3.0, 4.0, 5.0, 2.0, 3.0]
        else: # Just Type
            data = [90, 3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Order matches creation order
        sliders = [self.slider_wpm, self.slider_delay, self.slider_fatigue, 
                   self.slider_correct, self.slider_persist, self.slider_swap,
                   self.slider_rethink, self.slider_para, self.slider_double]
        
        for s, v in zip(sliders, data):
            self.set_slider_val(s, v)

    def update_stats(self):
        text = self.text_area.toPlainText().strip()
        words = len(text.split())
        chars = len(text)
        self.lbl_words.setText(f"{words} Words")
        
        if chars == 0:
            self.lbl_est.setText("~ 0m 0s")
            return

        # Rough Estimation Logic
        wpm = self.get_slider_val(self.slider_wpm)
        base_delay = 60.0 / (max(wpm, 1) * 5.0)
        
        overhead = 0
        overhead += (chars * (self.get_slider_val(self.slider_correct)/100)) * 0.6
        overhead += (chars * (self.get_slider_val(self.slider_rethink)/100)) * 2.0
        overhead += text.count('\n') * self.get_slider_val(self.slider_para)
        
        total_seconds = (chars * base_delay) + overhead
        m, s = divmod(int(total_seconds), 60)
        self.lbl_est.setText(f"Est: {m}m {s}s")

    def start_typing(self):
        text = self.text_area.toPlainText()
        if not text:
            self.status_lbl.setText("No text to type!")
            self.status_lbl.setStyleSheet("color: #dc3545;")
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

    def stop_typing(self):
        if self.worker:
            self.worker.stop()
            self.status_lbl.setText("Stopping...")

    def on_typing_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.text_area.setEnabled(True)
        self.worker = None

    def handle_status(self, msg, color):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Good base for custom styling
    app.setStyleSheet(STYLESHEET)
    
    window = AutoTyperApp()
    window.show()
    
    sys.exit(app.exec())