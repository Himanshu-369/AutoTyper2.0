import sys
import time
import random
import pyautogui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QProgressBar, QComboBox, QCheckBox, QSlider, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor

# --- CONFIGURATION ---
pyautogui.PAUSE = 0 

# --- DATA ---
KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}

# --- STYLESHEET ---
STYLESHEET = """
QMainWindow { background-color: #121212; }
QWidget { color: #E0E0E0; font-family: "Segoe UI", sans-serif; font-size: 10pt; }

/* TEXT EDIT */
QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 10px;
    color: #F0F0F0;
    font-family: "Consolas", monospace;
}

/* STATS LABELS */
QLabel#StatsLabel {
    color: #03DAC6; /* Teal Accent */
    font-weight: bold;
    font-size: 10pt;
}
QLabel#StatsValue {
    color: #A0A0A0;
    margin-right: 15px;
}

/* SLIDERS */
QSlider::groove:horizontal {
    border: 1px solid #333;
    height: 6px;
    background: #252526;
    margin: 2px 0;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #BB86FC; /* Purple Accent */
    border: 1px solid #BB86FC;
    width: 16px;
    height: 16px;
    margin: -6px 0; 
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #D0A0FF;
}
QSlider::sub-page:horizontal {
    background: #BB86FC;
    border-radius: 3px;
}

/* BUTTONS */
QPushButton {
    background-color: #2D2D30;
    border-radius: 6px;
    padding: 10px;
    font-weight: 600;
}
QPushButton#StartBtn {
    background-color: #03DAC6;
    color: #000;
}
QPushButton#StartBtn:hover { background-color: #05E5D0; }
QPushButton#StopBtn {
    background-color: #CF6679;
    color: #000;
}
QPushButton#StopBtn:disabled { background-color: #333; color: #555; }

/* PROGRESS */
QProgressBar {
    background-color: #1E1E1E;
    border: none;
    height: 4px;
}
QProgressBar::chunk { background-color: #03DAC6; }

/* COMBO */
QComboBox {
    background-color: #1E1E1E;
    border: 1px solid #333;
    padding: 5px;
    border-radius: 4px;
}
"""

# --- WORKER THREAD ---
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
        if char.lower() in KEY_NEIGHBORS:
            n = random.choice(KEY_NEIGHBORS[char.lower()])
            return n.upper() if char.isupper() else n
        return char

    def press_key_human(self, char):
        if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?':
            pyautogui.keyDown('shift')
            time.sleep(random.uniform(0.06, 0.11))
            pyautogui.press(char.lower())
            time.sleep(random.uniform(0.05, 0.09))
            pyautogui.keyUp('shift')
        else:
            pyautogui.press(char)

    def run(self):
        try:
            # Countdown
            for i in range(int(self.config['start_delay']), 0, -1):
                if not self.is_running: return
                self.status_signal.emit(f"Starting in {i}...")
                time.sleep(1)

            if not self.is_running: return

            text = self.text
            # Basic WPM calc
            base_delay = 60.0 / (max(self.config['wpm'], 1) * 5.0)
            
            p_correct = self.config['correct'] / 100.0
            p_persist = self.config['persist'] / 100.0
            p_rethink = self.config['rethink'] / 100.0
            p_fatigue = self.config['fatigue'] / 100.0
            
            chars_done = 0
            total = len(text)
            word_buf = ""
            flow = 1.0

            self.status_signal.emit("Typing...")

            i = 0
            while i < len(text):
                if not self.is_running: break
                char = text[i]
                chars_done += 1

                if i % 5 == 0:
                    self.progress_signal.emit(int((chars_done/total)*100))

                # Fatigue
                fatigue = 1.0 + ((chars_done/total) * p_fatigue)
                flow += random.uniform(-0.1, 0.1)
                flow = max(0.7, min(1.4, flow))

                # Logic 1: Rethink
                if char in " .,?!" and len(word_buf) > 3 and random.random() < p_rethink:
                    self.press_key_human(char)
                    time.sleep(base_delay * 5)
                    for _ in range(len(word_buf)+1):
                        pyautogui.press('backspace')
                        time.sleep(0.05)
                    time.sleep(0.5)
                    word_buf = ""
                else:
                    word_buf = "" if char in " .,?!" else word_buf + char

                # Logic 2: Paragraph
                if char == '\n':
                    pyautogui.press('enter')
                    time.sleep(self.config['para_pause'])
                    i += 1
                    continue

                # Logic 3: Typos
                if char.isalnum():
                    if random.random() < p_persist:
                        pyautogui.write(self.get_neighbor(char))
                        i += 1; time.sleep(base_delay); continue
                    elif random.random() < p_correct:
                        pyautogui.write(self.get_neighbor(char))
                        time.sleep(0.2)
                        pyautogui.press('backspace')

                self.press_key_human(char)
                # Final Delay Calc
                time.sleep((base_delay * flow * fatigue) * random.uniform(0.85, 1.15))
                i += 1

            self.progress_signal.emit(100)
            self.status_signal.emit("Complete")
        except Exception as e:
            self.status_signal.emit(f"Error: {e}")
        finally:
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False

# --- CUSTOM SLIDER WIDGET ---
class SliderWidget(QWidget):
    # Emits the real float value when changed
    valueChanged = pyqtSignal(float)

    def __init__(self, title, min_val, max_val, default, suffix="", scale=1):
        super().__init__()
        self.scale = scale
        self.suffix = suffix
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)
        
        # Header Row: Title + Value
        header = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #A0A0A0; font-weight: 600;")
        
        self.lbl_val = QLabel(f"{default}{suffix}")
        self.lbl_val.setStyleSheet("color: #BB86FC; font-weight: bold; font-family: 'Consolas';")
        
        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_val)
        layout.addLayout(header)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * scale), int(max_val * scale))
        self.slider.setValue(int(default * scale))
        self.slider.valueChanged.connect(self.on_change)
        layout.addWidget(self.slider)

    def on_change(self, val):
        real_val = val / self.scale
        # Display integer if scale is 1, else decimal
        txt = f"{int(real_val)}" if self.scale == 1 else f"{real_val:.1f}"
        self.lbl_val.setText(f"{txt}{self.suffix}")
        
        # Emit signal for parent to catch
        self.valueChanged.emit(real_val)

    def get_value(self):
        return self.slider.value() / self.scale

    def set_value(self, val):
        self.slider.setValue(int(val * self.scale))

# --- MAIN WINDOW ---
class SliderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_profile("Lazy Student")

    def init_ui(self):
        self.setWindowTitle("AutoTyper Pro")
        self.resize(450, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(15)

        # 1. Header
        head = QHBoxLayout()
        title = QLabel("Human Typer")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: white;")
        
        self.chk_top = QCheckBox("Topmost")
        self.chk_top.toggled.connect(lambda c: self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, c) or self.show())
        
        head.addWidget(title)
        head.addStretch()
        head.addWidget(self.chk_top)
        main.addLayout(head)

        # 2. Input Area
        self.txt_in = QTextEdit()
        self.txt_in.setPlaceholderText("Paste text here...")
        self.txt_in.textChanged.connect(self.update_stats) # Connect text change
        main.addWidget(self.txt_in)

        # 3. Stats Row (NEW)
        stats_row = QHBoxLayout()
        
        lbl_w = QLabel("WORDS:")
        lbl_w.setObjectName("StatsLabel")
        self.lbl_words_val = QLabel("0")
        self.lbl_words_val.setObjectName("StatsValue")
        
        lbl_t = QLabel("EST. TIME:")
        lbl_t.setObjectName("StatsLabel")
        self.lbl_time_val = QLabel("0m 0s")
        self.lbl_time_val.setObjectName("StatsValue")

        stats_row.addWidget(lbl_w)
        stats_row.addWidget(self.lbl_words_val)
        stats_row.addSpacing(20)
        stats_row.addWidget(lbl_t)
        stats_row.addWidget(self.lbl_time_val)
        stats_row.addStretch()
        main.addLayout(stats_row)

        # 4. Profile
        row_prof = QHBoxLayout()
        row_prof.addWidget(QLabel("Profile:"))
        self.cb_prof = QComboBox()
        self.cb_prof.addItems(["Pro Typist", "Lazy Student", "Tired Human", "Just Type"])
        self.cb_prof.currentTextChanged.connect(self.apply_profile)
        row_prof.addWidget(self.cb_prof, 1)
        main.addLayout(row_prof)

        # 5. Sliders
        sliders = QVBoxLayout()
        sliders.setSpacing(10)

        # (Title, Min, Max, Default, Suffix, Scale)
        self.sl_wpm = SliderWidget("Speed", 10, 200, 70, " WPM")
        self.sl_wpm.valueChanged.connect(lambda: self.update_stats()) # Update time when WPM changes

        self.sl_delay = SliderWidget("Start Delay", 0, 30, 5, " s")
        self.sl_fatigue = SliderWidget("Fatigue", 0, 50, 10, "%")
        
        self.sl_correct = SliderWidget("Mistakes (Fixed)", 0, 20, 4, "%", scale=10) 
        self.sl_persist = SliderWidget("Mistakes (Missed)", 0, 10, 1, "%", scale=10)
        self.sl_rethink = SliderWidget("Hesitation", 0, 10, 2, "%", scale=10)
        
        self.sl_pause = SliderWidget("Paragraph Pause", 0, 5, 1.5, " s", scale=10)
        self.sl_pause.valueChanged.connect(lambda: self.update_stats()) # Update time when Pause changes

        sliders.addWidget(self.sl_wpm)
        sliders.addWidget(self.sl_delay)
        sliders.addWidget(self.sl_fatigue)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #333;")
        sliders.addWidget(line)
        
        sliders.addWidget(self.sl_correct)
        sliders.addWidget(self.sl_persist)
        sliders.addWidget(self.sl_rethink)
        sliders.addWidget(self.sl_pause)
        
        main.addLayout(sliders)

        # 6. Footer
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.lbl_status)
        
        self.bar = QProgressBar()
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        main.addWidget(self.bar)

        h_btns = QHBoxLayout()
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop)
        
        self.btn_start = QPushButton("START TYPING")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start)
        
        h_btns.addWidget(self.btn_stop)
        h_btns.addWidget(self.btn_start, 2)
        main.addLayout(h_btns)

    def apply_profile(self, name):
        p = {"wpm": 70, "fatigue": 10, "correct": 4.0, "persist": 1.0, "rethink": 2.0, "pause": 1.5}
        
        if name == "Pro Typist":
            p = {"wpm": 110, "fatigue": 5, "correct": 1.5, "persist": 0.1, "rethink": 0.5, "pause": 0.5}
        elif name == "Lazy Student":
            p = {"wpm": 65, "fatigue": 15, "correct": 6.0, "persist": 2.0, "rethink": 3.0, "pause": 2.0}
        elif name == "Tired Human":
            p = {"wpm": 45, "fatigue": 30, "correct": 8.0, "persist": 3.0, "rethink": 5.0, "pause": 2.5}
        elif name == "Just Type":
            p = {"wpm": 90, "fatigue": 0, "correct": 0.0, "persist": 0.0, "rethink": 0.0, "pause": 0.0}

        self.sl_wpm.set_value(p['wpm'])
        self.sl_fatigue.set_value(p['fatigue'])
        self.sl_correct.set_value(p['correct'])
        self.sl_persist.set_value(p['persist'])
        self.sl_rethink.set_value(p['rethink'])
        self.sl_pause.set_value(p['pause'])

    def update_stats(self):
        text = self.txt_in.toPlainText()
        words = len(text.split())
        self.lbl_words_val.setText(f"{words}")

        if not text:
            self.lbl_time_val.setText("0m 0s")
            return

        chars = len(text)
        wpm = self.sl_wpm.get_value()
        
        # Estimation Logic
        # 1. Base typing time: (chars / 5) / WPM * 60
        base_seconds = (chars / 5.0) / max(wpm, 1) * 60.0
        
        # 2. Add Paragraph Pause overhead
        para_count = text.count('\n')
        pause_overhead = para_count * self.sl_pause.get_value()
        
        # 3. Add slight overhead for corrections/hesitation (approx 10%)
        misc_overhead = base_seconds * 0.10

        total_seconds = base_seconds + pause_overhead + misc_overhead
        
        m, s = divmod(int(total_seconds), 60)
        self.lbl_time_val.setText(f"{m}m {s}s")

    def start(self):
        txt = self.txt_in.toPlainText()
        if not txt: return
        
        cfg = {
            'wpm': self.sl_wpm.get_value(),
            'start_delay': self.sl_delay.get_value(),
            'fatigue': self.sl_fatigue.get_value(),
            'correct': self.sl_correct.get_value(),
            'persist': self.sl_persist.get_value(),
            'rethink': self.sl_rethink.get_value(),
            'para_pause': self.sl_pause.get_value()
        }
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.txt_in.setEnabled(False)
        
        self.worker = TypingWorker(txt, cfg)
        self.worker.progress_signal.connect(self.bar.setValue)
        self.worker.status_signal.connect(self.lbl_status.setText)
        self.worker.finished_signal.connect(self.reset)
        self.worker.start()

    def stop(self):
        if hasattr(self, 'worker'): self.worker.stop()

    def reset(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.txt_in.setEnabled(True)
        self.bar.setValue(100)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = SliderApp()
    win.show()
    sys.exit(app.exec())