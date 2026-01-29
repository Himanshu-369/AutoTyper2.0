import sys
import time
import random
import pyautogui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QProgressBar, QComboBox, QCheckBox, QFrame, 
                             QGridLayout, QDoubleSpinBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QIcon

# --- CONFIGURATION ---
pyautogui.PAUSE = 0 

# --- LOGIC DATA ---
KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}
COMMON_SWAPS = ['th', 'he', 'an', 'in', 'er', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed']

# --- MODERN STYLESHEET ---
STYLESHEET = """
/* MAIN WINDOW */
QMainWindow {
    background-color: #121212;
}
QWidget {
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 10pt;
    color: #E0E0E0;
}

/* CARDS */
QFrame#Card {
    background-color: #1E1E1E;
    border-radius: 12px;
    border: 1px solid #2C2C2C;
}

/* HEADERS & LABELS */
QLabel#Title {
    font-size: 16pt;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#SectionHeader {
    font-size: 9pt;
    font-weight: 700;
    color: #BB86FC; /* Soft Purple Accent */
    text-transform: uppercase;
    letter-spacing: 1px;
}
QLabel#Stats {
    color: #757575;
    font-size: 9pt;
}

/* INPUTS & EDITS */
QTextEdit {
    background-color: #252526;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 10px;
    color: #F0F0F0;
    font-family: "Consolas", monospace;
    font-size: 11pt;
}
QTextEdit:focus {
    border: 1px solid #BB86FC;
}

/* COMBO BOX */
QComboBox {
    background-color: #252526;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 5px 10px;
    min-width: 100px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #BB86FC;
    margin-right: 5px;
}

/* SPIN BOXES */
QDoubleSpinBox {
    background-color: #252526;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 4px 8px;
    color: #BB86FC;
    font-weight: bold;
}
QDoubleSpinBox:focus {
    border: 1px solid #BB86FC;
}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: transparent;
    width: 15px;
}

/* BUTTONS */
QPushButton {
    background-color: #2D2D30;
    color: #E0E0E0;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #3E3E42;
}
QPushButton#PrimaryBtn {
    background-color: #BB86FC;
    color: #121212;
    font-size: 11pt;
    border-radius: 8px;
    padding: 12px;
}
QPushButton#PrimaryBtn:hover {
    background-color: #9965f4;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #333333;
    color: #555555;
}
QPushButton#StopBtn {
    background-color: #CF6679;
    color: #121212;
    border-radius: 8px;
}
QPushButton#StopBtn:disabled {
    background-color: #333333;
    color: #555555;
}

/* PROGRESS BAR */
QProgressBar {
    background-color: #252526;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #03DAC6; /* Teal Accent */
    border-radius: 4px;
}

/* CHECKBOX */
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #555;
}
QCheckBox::indicator:checked {
    background-color: #BB86FC;
    border-color: #BB86FC;
}
"""

# --- WORKER THREAD (Logic) ---
class TypingWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str) 
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

    def run(self):
        try:
            delay = int(self.config['start_delay'])
            for i in range(delay, 0, -1):
                if not self.is_running: return
                self.status_signal.emit(f"Starting in {i}s...")
                time.sleep(1)

            if not self.is_running: return

            text = self.text
            wpm = self.config['wpm']
            base_delay_target = 60.0 / (max(wpm, 1) * 5.0)
            
            # Unpack rates (0-100 to 0.0-1.0)
            p_correct = self.config['correct'] / 100.0
            p_persist = self.config['persist'] / 100.0
            p_swap = self.config['swap'] / 100.0
            p_rethink = self.config['rethink'] / 100.0
            p_fatigue = self.config['fatigue'] / 100.0
            
            chars_done = 0
            total_chars = len(text)
            word_buffer = ""
            flow = 1.0 
            i = 0

            self.status_signal.emit("Typing in progress...")

            while i < len(text):
                if not self.is_running: break
                
                char = text[i]
                chars_done += 1
                
                # UI Update (Throttle)
                if i % 5 == 0:
                    self.progress_signal.emit(int((chars_done / total_chars) * 100))

                # Fatigue & Flow
                progress = chars_done / max(total_chars, 1)
                fatigue_mult = 1.0 + (progress * p_fatigue)
                flow += random.uniform(-0.15, 0.15)
                flow = max(0.6, min(1.6, flow))

                # Logic 1: Rethink
                if char in " .,?!" and len(word_buffer) > 3 and random.random() < p_rethink:
                    self.press_key_human(char)
                    time.sleep(base_delay_target * 4)
                    for _ in range(len(word_buffer) + 1):
                        pyautogui.press('backspace')
                        time.sleep(0.04)
                    time.sleep(0.8)
                    word_buffer = ""
                else:
                    if char not in " .,?!": word_buffer += char
                    else: word_buffer = ""

                # Logic 2: Paragraph Pause
                if char == '\n':
                    pyautogui.press('enter')
                    time.sleep(self.config['para_pause'] * random.uniform(0.9, 1.1))
                    i += 1
                    continue

                # Logic 3: Swap (the/teh)
                if i + 1 < len(text) and char.isalnum() and random.random() < p_swap:
                    pair = (char + text[i+1]).lower()
                    if pair in COMMON_SWAPS:
                        pyautogui.write(text[i+1])
                        time.sleep(base_delay_target)
                        pyautogui.write(char)
                        time.sleep(0.25)
                        pyautogui.press('backspace', presses=2)
                        time.sleep(0.1)

                # Logic 4: Typos
                if char.isalnum():
                    if random.random() < p_persist: # Ignored typo
                        pyautogui.write(self.get_neighbor(char))
                        i += 1
                        time.sleep(base_delay_target * flow)
                        continue
                    elif random.random() < p_correct: # Corrected typo
                        pyautogui.write(self.get_neighbor(char))
                        time.sleep(0.2)
                        pyautogui.press('backspace')

                self.press_key_human(char)
                time.sleep((base_delay_target * flow * fatigue_mult) * random.uniform(0.8, 1.2))
                i += 1

            self.progress_signal.emit(100)
            self.status_signal.emit("Complete")
        except Exception as e:
            self.status_signal.emit(f"Error: {e}")
        finally:
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False

# --- CUSTOM UI COMPONENTS ---
class SettingCard(QFrame):
    def __init__(self, title, items):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header = QLabel(title)
        header.setObjectName("SectionHeader")
        layout.addWidget(header)
        
        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(15)
        
        for idx, (label_txt, spinbox) in enumerate(items):
            lbl = QLabel(label_txt)
            lbl.setStyleSheet("color: #A0A0A0;")
            grid.addWidget(lbl, idx, 0)
            grid.addWidget(spinbox, idx, 1)
            
        layout.addLayout(grid)

# --- MAIN WINDOW ---
class MinimalTyperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.apply_profile("Lazy Student")

    def init_ui(self):
        self.setWindowTitle("Humanized AutoTyper")
        self.resize(500, 780)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main Layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # 1. Header
        header = QHBoxLayout()
        title = QLabel("AutoTyper")
        title.setObjectName("Title")
        
        self.top_check = QCheckBox("Topmost")
        self.top_check.toggled.connect(lambda c: self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, c) or self.show())
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.top_check)
        main_layout.addLayout(header)

        # 2. Text Area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste text to type here...")
        self.text_edit.textChanged.connect(self.update_est)
        main_layout.addWidget(self.text_edit, stretch=1)

        # 3. Toolbar (Profile & Stats)
        toolbar = QHBoxLayout()
        
        # Profile Selector
        self.profile_cb = QComboBox()
        self.profile_cb.addItems(["Pro Typist", "Lazy Student", "Tired Human", "Just Type"])
        self.profile_cb.currentTextChanged.connect(self.apply_profile)
        toolbar.addWidget(self.profile_cb)
        
        toolbar.addStretch()
        
        # Stats
        self.lbl_words = QLabel("0 Words")
        self.lbl_words.setObjectName("Stats")
        self.lbl_time = QLabel("~ 0m")
        self.lbl_time.setObjectName("Stats")
        toolbar.addWidget(self.lbl_words)
        toolbar.addSpacing(15)
        toolbar.addWidget(self.lbl_time)
        
        main_layout.addLayout(toolbar)

        # 4. Settings Area (Cards)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(15)

        # Create Spinboxes
        self.s_wpm = self.make_spin(10, 200, 70)
        self.s_delay = self.make_spin(0, 60, 5)
        self.s_fatigue = self.make_spin(0, 100, 10)
        self.s_correct = self.make_spin(0, 100, 4)
        self.s_persist = self.make_spin(0, 100, 1)
        self.s_swap = self.make_spin(0, 100, 1.5)
        self.s_rethink = self.make_spin(0, 100, 2)
        self.s_pause = self.make_spin(0, 10, 1.5)

        # Card 1: Speed
        card_speed = SettingCard("Speed & Flow", [
            ("Base Speed (WPM)", self.s_wpm),
            ("Start Delay (s)", self.s_delay),
            ("Fatigue Impact (%)", self.s_fatigue)
        ])
        settings_layout.addWidget(card_speed)

        # Card 2: Imperfections
        card_errors = SettingCard("Imperfections", [
            ("Typos (Fixed) %", self.s_correct),
            ("Typos (Missed) %", self.s_persist),
            ("Word Rethink %", self.s_rethink),
            ("Swap Error %", self.s_swap)
        ])
        settings_layout.addWidget(card_errors)
        
        main_layout.addLayout(settings_layout)

        # 5. Footer (Status & Buttons)
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #BB86FC; font-weight: 600;")
        main_layout.addWidget(self.lbl_status)
        
        self.p_bar = QProgressBar()
        self.p_bar.setValue(0)
        self.p_bar.setTextVisible(False)
        main_layout.addWidget(self.p_bar)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.clicked.connect(self.stop_typing)
        
        self.btn_start = QPushButton("START TYPING")
        self.btn_start.setObjectName("PrimaryBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_typing)

        btns.addWidget(self.btn_stop)
        btns.addWidget(self.btn_start)
        main_layout.addLayout(btns)

    def make_spin(self, min_v, max_v, val):
        s = QDoubleSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(val)
        s.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons) # Cleaner look
        s.setAlignment(Qt.AlignmentFlag.AlignRight)
        s.setFixedWidth(70)
        s.valueChanged.connect(self.update_est)
        return s

    def update_est(self):
        text = self.text_edit.toPlainText()
        words = len(text.split())
        self.lbl_words.setText(f"{words} Words")
        
        if not text:
            self.lbl_time.setText("~ 0m")
            return

        # Simple estimation logic
        chars = len(text)
        wpm = self.s_wpm.value()
        base_sec = (chars / 5) / max(wpm, 1) * 60
        overhead = chars * 0.05 + text.count('\n') * 1.5
        total = base_sec + overhead
        self.lbl_time.setText(f"~ {int(total // 60)}m {int(total % 60)}s")

    def apply_profile(self, name):
        p = {"wpm": 70, "correct": 4, "persist": 1, "rethink": 2, "swap": 1.5, "fatigue": 10}
        if name == "Pro Typist": p = {"wpm": 110, "correct": 1.5, "persist": 0.1, "rethink": 0.5, "swap": 0.5, "fatigue": 5}
        elif name == "Lazy Student": p = {"wpm": 65, "correct": 6, "persist": 2, "rethink": 3, "swap": 2.5, "fatigue": 15}
        elif name == "Tired Human": p = {"wpm": 45, "correct": 8, "persist": 3, "rethink": 5, "swap": 4, "fatigue": 30}
        elif name == "Just Type": p = {"wpm": 90, "correct": 0, "persist": 0, "rethink": 0, "swap": 0, "fatigue": 0}

        self.s_wpm.setValue(p['wpm'])
        self.s_correct.setValue(p['correct'])
        self.s_persist.setValue(p['persist'])
        self.s_rethink.setValue(p['rethink'])
        self.s_swap.setValue(p['swap'])
        self.s_fatigue.setValue(p['fatigue'])

    def start_typing(self):
        text = self.text_edit.toPlainText()
        if not text: return
        
        cfg = {
            'wpm': self.s_wpm.value(), 'start_delay': self.s_delay.value(),
            'fatigue': self.s_fatigue.value(), 'correct': self.s_correct.value(),
            'persist': self.s_persist.value(), 'swap': self.s_swap.value(),
            'rethink': self.s_rethink.value(), 'para_pause': self.s_pause.value()
        }
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.text_edit.setEnabled(False)
        
        self.worker = TypingWorker(text, cfg)
        self.worker.progress_signal.connect(self.p_bar.setValue)
        self.worker.status_signal.connect(self.lbl_status.setText)
        self.worker.finished_signal.connect(self.reset_ui)
        self.worker.start()

    def stop_typing(self):
        if self.worker: self.worker.stop()

    def reset_ui(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.text_edit.setEnabled(True)
        self.p_bar.setValue(100)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MinimalTyperWindow()
    window.show()
    sys.exit(app.exec())