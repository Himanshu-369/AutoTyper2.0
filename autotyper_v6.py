import sys
import time
import random
import pyautogui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QProgressBar, QComboBox, QCheckBox, QSlider, QFrame,
                             QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, QFont

# --- CONFIGURATION ---
pyautogui.PAUSE = 0 

# --- DATA ---
KEY_NEIGHBORS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'qweadz', 'd': 'ersfcx', 'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'j': 'uikmnh', 'k': 'iolmj', 'l': 'opk',
    'z': 'asx', 'x': 'sdzc', 'c': 'dfxv', 'v': 'fgcb', 'b': 'ghvn', 'n': 'hjbm', 'm': 'jkln'
}

COMMON_SWAPS = ['th', 'he', 'an', 'in', 'er', 're', 'on', 'at', 'en', 'nd', 'ti', 'es', 'or', 'te', 'of', 'ed']

# --- STYLESHEET ---
STYLESHEET = """
QMainWindow { background-color: #121212; }
QWidget { color: #E0E0E0; font-family: "Segoe UI", sans-serif; font-size: 10pt; }

QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical { border: none; background: #1E1E1E; width: 10px; }
QScrollBar::handle:vertical { background: #333; min-height: 20px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #BB86FC; }

QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 10px;
    color: #F0F0F0;
    font-family: "Consolas", monospace;
}

QLabel#StatsLabel { color: #03DAC6; font-weight: bold; }
QLabel#StatsValue { color: #A0A0A0; margin-right: 15px; }

QSlider::groove:horizontal { border: 1px solid #333; height: 6px; background: #252526; border-radius: 3px; }
QSlider::handle:horizontal { background: #BB86FC; border: 1px solid #BB86FC; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
QSlider::sub-page:horizontal { background: #BB86FC; border-radius: 3px; }

QPushButton { background-color: #2D2D30; border-radius: 6px; padding: 8px 16px; font-weight: 600; }
QPushButton#StartBtn { background-color: #03DAC6; color: #000; padding: 12px; }
QPushButton#StopBtn { background-color: #CF6679; color: #000; padding: 12px; }
QPushButton#StopBtn:disabled { background-color: #333; color: #555; }

QComboBox { background-color: #1E1E1E; border: 1px solid #333; padding: 5px; border-radius: 4px; }
"""

# --- CUSTOM PROGRESS BAR WITH INVERTING TEXT ---
class InvertingProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False) # We will draw our own text
        self.setFixedHeight(22)
        self.chunk_color = QColor("#03DAC6")
        self.bg_color = QColor("#1E1E1E")
        self.text_light = QColor("#E0E0E0")
        self.text_dark = QColor("#000000")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Draw Background
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)

        # 2. Calculate Progress Width
        width = self.rect().width()
        progress_width = int(width * (self.value() / self.maximum()))

        # 3. Draw Progress Chunk
        if progress_width > 0:
            painter.setBrush(self.chunk_color)
            painter.drawRoundedRect(0, 0, progress_width, self.height(), 4, 4)

        # 4. Draw Centered Percentage Text
        text = f"{self.value()}%"
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Prepare text drawing area
        rect = self.rect()
        
        # We draw the text twice using Clipping to get the color inversion
        
        # Part A: Draw light text for the area NOT covered by the bar
        painter.save()
        painter.setClipRect(progress_width, 0, width - progress_width, self.height())
        painter.setPen(self.text_light)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

        # Part B: Draw dark text for the area covered by the bar
        painter.save()
        painter.setClipRect(0, 0, progress_width, self.height())
        painter.setPen(self.text_dark)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

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
        char_lower = char.lower()
        if char_lower in KEY_NEIGHBORS:
            neighbor = random.choice(KEY_NEIGHBORS[char_lower])
            return neighbor.upper() if char.isupper() else neighbor
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

    def calculate_base_delay(self):
        wpm = self.config['wpm']
        return 60.0 / (max(wpm, 1) * 5.0)

    def run(self):
        try:
            delay = int(self.config['start_delay'])
            for i in range(delay, 0, -1):
                if not self.is_running: return
                self.status_signal.emit(f"Starting in {i}...")
                time.sleep(1)

            if not self.is_running: return
            self.status_signal.emit("Typing...")
            
            text = self.text
            base_delay_target = self.calculate_base_delay()
            
            p_correct = self.config['correct'] / 100.0
            p_persist = self.config['persist'] / 100.0
            p_rethink = self.config['rethink'] / 100.0
            p_swap = self.config['swap'] / 100.0
            p_dbl_space = self.config['double_space'] / 100.0
            fatigue_factor = self.config['fatigue'] / 100.0
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
                    self.progress_signal.emit(int((chars_done / total_chars) * 100))

                # Logic Flow
                progress_ratio = chars_done / max(total_chars, 1)
                fatigue_mult = 1.0 + (progress_ratio * fatigue_factor)
                flow += random.uniform(-0.15, 0.15)
                flow = max(0.6, min(1.6, flow))

                if char == '\n':
                    pyautogui.press('enter')
                    time.sleep(para_pause * random.uniform(0.8, 1.2))
                    i += 1; word_buffer = ""; continue

                if char in " .,?!":
                    if len(word_buffer) > 3 and random.random() < p_rethink:
                        self.press_key_human(char)
                        time.sleep(base_delay_target * 4)
                        if random.random() < 0.7:
                            pyautogui.hotkey('ctrl', 'backspace')
                        else:
                            for _ in range(len(word_buffer) + 1):
                                pyautogui.press('backspace')
                                time.sleep(0.04)
                        time.sleep(random.uniform(0.5, 1.2))
                        word_buffer = ""
                    else: word_buffer = ""
                else: word_buffer += char

                if i + 1 < len(text) and char.isalnum() and random.random() < p_swap:
                    next_char = text[i+1]
                    if (char + next_char).lower() in COMMON_SWAPS:
                        pyautogui.write(next_char)
                        time.sleep(base_delay_target * flow)
                        pyautogui.write(char)
                        time.sleep(0.2)
                        pyautogui.press('backspace'); pyautogui.press('backspace')
                        time.sleep(0.15)

                if char.isalnum() and random.random() < p_persist:
                    pyautogui.write(self.get_neighbor(char))
                    i += 1; time.sleep(base_delay_target * flow * fatigue_mult); continue

                if char.isalnum() and random.random() < p_correct:
                    pyautogui.write(self.get_neighbor(char))
                    time.sleep(random.uniform(0.15, 0.4))
                    pyautogui.press('backspace')

                if char == ' ' and random.random() < p_dbl_space:
                    pyautogui.write("  ")
                    if random.random() < 0.5:
                        time.sleep(0.2); pyautogui.press('backspace')
                    else: i += 1; continue

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

# --- UI HELPERS ---
class SliderWidget(QWidget):
    valueChanged = pyqtSignal(float)
    def __init__(self, title, min_val, max_val, default, suffix="", scale=1):
        super().__init__()
        self.scale, self.suffix = scale, suffix
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        header = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #A0A0A0; font-weight: 600;")
        self.lbl_val = QLabel(f"{default}{suffix}")
        self.lbl_val.setStyleSheet("color: #BB86FC; font-weight: bold; font-family: 'Consolas';")
        header.addWidget(self.lbl_title); header.addStretch(); header.addWidget(self.lbl_val)
        layout.addLayout(header)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * scale), int(max_val * scale))
        self.slider.setValue(int(default * scale))
        self.slider.valueChanged.connect(self.on_change)
        layout.addWidget(self.slider)

    def on_change(self, val):
        real_val = val / self.scale
        txt = f"{int(real_val)}" if self.scale == 1 else f"{real_val:.1f}"
        self.lbl_val.setText(f"{txt}{self.suffix}")
        self.valueChanged.emit(real_val)

    def get_value(self): return self.slider.value() / self.scale
    def set_value(self, val): self.slider.setValue(int(val * self.scale))

class SliderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.apply_profile("Lazy Student")

    def init_ui(self):
        self.setWindowTitle("AutoTyper Pro V6")
        self.resize(480, 680)
        
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
        head.addWidget(title); head.addStretch(); head.addWidget(self.chk_top)
        main.addLayout(head)

        # 2. Toolbar
        toolbar = QHBoxLayout()
        btn_load = QPushButton("📂 Load File")
        btn_load.clicked.connect(self.load_file)
        btn_paste = QPushButton("📋 Paste Clipboard")
        btn_paste.clicked.connect(self.paste_clipboard)
        toolbar.addWidget(btn_load); toolbar.addWidget(btn_paste); toolbar.addStretch()
        main.addLayout(toolbar)

        # 3. Input
        self.txt_in = QTextEdit()
        self.txt_in.setPlaceholderText("Paste text here...")
        self.txt_in.textChanged.connect(self.update_stats)
        main.addWidget(self.txt_in)

        # 4. Stats
        stats_row = QHBoxLayout()
        self.lbl_words_val = QLabel("0")
        self.lbl_words_val.setObjectName("StatsValue")
        self.lbl_time_val = QLabel("0m 0s")
        self.lbl_time_val.setObjectName("StatsValue")
        stats_row.addWidget(QLabel("WORDS:", objectName="StatsLabel"))
        stats_row.addWidget(self.lbl_words_val)
        stats_row.addSpacing(20)
        stats_row.addWidget(QLabel("EST. TIME:", objectName="StatsLabel"))
        stats_row.addWidget(self.lbl_time_val)
        stats_row.addStretch()
        main.addLayout(stats_row)

        # 5. Scroll Settings
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 10, 0)
        
        row_prof = QHBoxLayout()
        row_prof.addWidget(QLabel("Profile:"))
        self.cb_prof = QComboBox()
        self.cb_prof.addItems(["Pro Typist", "Lazy Student", "Tired Human", "Just Type"])
        self.cb_prof.currentTextChanged.connect(self.apply_profile)
        row_prof.addWidget(self.cb_prof, 1)
        settings_layout.addLayout(row_prof)

        self.sl_wpm = SliderWidget("Speed", 10, 200, 70, " WPM")
        self.sl_wpm.valueChanged.connect(self.update_stats)
        self.sl_delay = SliderWidget("Start Delay", 0, 30, 5, " s")
        self.sl_fatigue = SliderWidget("Fatigue Impact", 0, 50, 10, "%")
        
        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setStyleSheet("color: #333;")
        self.sl_correct = SliderWidget("Typos (Corrected)", 0, 20, 4, "%", scale=10) 
        self.sl_persist = SliderWidget("Typos (Ignored)", 0, 10, 1, "%", scale=10)
        self.sl_swap = SliderWidget("Swap Errors (teh/the)", 0, 10, 1.5, "%", scale=10)
        
        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine); line2.setStyleSheet("color: #333;")
        self.sl_rethink = SliderWidget("Hesitation (Rethink)", 0, 10, 2, "%", scale=10)
        self.sl_double = SliderWidget("Double Space Rate", 0, 10, 1, "%", scale=10)
        self.sl_pause = SliderWidget("Paragraph Pause", 0, 5, 1.5, " s", scale=10)
        self.sl_pause.valueChanged.connect(self.update_stats)

        settings_layout.addWidget(self.sl_wpm); settings_layout.addWidget(self.sl_delay)
        settings_layout.addWidget(self.sl_fatigue); settings_layout.addWidget(line1)
        settings_layout.addWidget(self.sl_correct); settings_layout.addWidget(self.sl_persist)
        settings_layout.addWidget(self.sl_swap); settings_layout.addWidget(line2)
        settings_layout.addWidget(self.sl_rethink); settings_layout.addWidget(self.sl_double)
        settings_layout.addWidget(self.sl_pause)

        self.scroll_area.setWidget(settings_widget)
        main.addWidget(self.scroll_area)

        # 6. Footer & Custom Progress Bar
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.lbl_status)
        
        self.bar = InvertingProgressBar()
        self.bar.setValue(0)
        main.addWidget(self.bar)

        h_btns = QHBoxLayout()
        self.btn_stop = QPushButton("STOP", objectName="StopBtn", enabled=False)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_start = QPushButton("START TYPING", objectName="StartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start)
        h_btns.addWidget(self.btn_stop); h_btns.addWidget(self.btn_start, 2)
        main.addLayout(h_btns)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt)")
        if fname: self.txt_in.setPlainText(open(fname, 'r', encoding='utf-8').read())

    def paste_clipboard(self): self.txt_in.setPlainText(QApplication.clipboard().text())

    def apply_profile(self, name):
        profiles = {
            "Pro Typist": [110, 5, 1.5, 0.1, 0.1, 0.5, 0.1, 0.5],
            "Lazy Student": [65, 15, 6.0, 2.0, 2.5, 3.0, 1.5, 2.0],
            "Tired Human": [45, 30, 8.0, 3.0, 4.0, 5.0, 3.0, 2.5],
            "Just Type": [90, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        }
        data = profiles.get(name, [70, 10, 4.0, 1.0, 1.5, 2.0, 1.0, 1.5])
        sliders = [self.sl_wpm, self.sl_fatigue, self.sl_correct, self.sl_persist, self.sl_swap, self.sl_rethink, self.sl_double, self.sl_pause]
        for s, v in zip(sliders, data): s.set_value(v)

    def update_stats(self):
        text = self.txt_in.toPlainText()
        self.lbl_words_val.setText(str(len(text.split())))
        if not text: self.lbl_time_val.setText("0m 0s"); return
        wpm = max(self.sl_wpm.get_value(), 1)
        base = (len(text) / 5.0) / wpm * 60.0
        overhead = (text.count('\n') * self.sl_pause.get_value()) + (base * (self.sl_rethink.get_value() + self.sl_correct.get_value())/100.0)
        m, s = divmod(int(base + overhead), 60)
        self.lbl_time_val.setText(f"{m}m {s}s")

    def start(self):
        txt = self.txt_in.toPlainText()
        if not txt: return
        self.btn_start.setEnabled(False); self.btn_stop.setEnabled(True); self.txt_in.setEnabled(False)
        self.worker = TypingWorker(txt, {
            'wpm': self.sl_wpm.get_value(), 'start_delay': self.sl_delay.get_value(),
            'fatigue': self.sl_fatigue.get_value(), 'correct': self.sl_correct.get_value(),
            'persist': self.sl_persist.get_value(), 'swap': self.sl_swap.get_value(),
            'rethink': self.sl_rethink.get_value(), 'double_space': self.sl_double.get_value(),
            'para_pause': self.sl_pause.get_value()
        })
        self.worker.progress_signal.connect(self.bar.setValue)
        self.worker.status_signal.connect(self.lbl_status.setText)
        self.worker.finished_signal.connect(self.reset)
        self.worker.start()

    def stop(self):
        if self.worker: self.worker.stop(); self.lbl_status.setText("Stopping...")

    def reset(self):
        self.btn_start.setEnabled(True); self.btn_stop.setEnabled(False); self.txt_in.setEnabled(True)
        self.bar.setValue(100 if self.lbl_status.text() == "Complete" else self.bar.value())
        self.worker = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = SliderApp(); win.show()
    sys.exit(app.exec())