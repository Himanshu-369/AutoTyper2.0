# AutoTyper_v2
This reposity shows multiple version of the AutoTyper, changed the classic theme to modern and minimalistic altervatives.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

> Automate your typing with realistic human behavior. Typos, hesitation, and fatigue included.

> **AutoTyper_v2** is a sophisticated automation tool written in Python that goes beyond standard text injection. It simulates the nuances of human typing, including variable WPM, fatigue, backspacing, and "thinking" pauses. Perfect for UI testing, generating realistic user data, or pranking your friends.


## ✨ Features

### 🎭 Realistic Simulation
Break the "robot" stereotype with advanced behavioral algorithms.
*   **Variable Speed:** Mimic natural fluctuation in Words Per Minute (WPM).
*   **Intelligent Typos:** Introduce random errors that are automatically corrected (backspaced) or ignored.
*   **Fatigue System:** Watch the typing speed degrade and error rates increase as the "user" gets tired.
*   **Hesitation:** Simulate "thinking" pauses (Word Rethink) or moments of distraction.

### 🎛️ Highly Configurable
Fine-tune every aspect of the typing engine:
*   **Base Speed:** Set your starting WPM.
*   **Start Delay:** Configurable countdown before execution.
*   **Error Types:** Control frequency of swap errors (e.g., "teh" vs "the"), double spaces, and paragraph pauses.

### 🎨 Modern GUIs
This project showcases an iterative development process featuring two distinct GUI architectures:
*   **CustomTkinter Version:** A lightweight, modern take on the classic Tkinter framework.
*   **PyQt6 Versions:** A series of refined, dark-themed interfaces with modular components, custom sliders, and robust styling (QSS).

### 📝 Flexible Input
*   Type directly into the app.
*   Load from `.txt` files.
*   Paste directly from the clipboard.

---

## 📸 Gallery

> *Custom tkinter GUI*

|autotyper_v1.py|
|:---:|
|<img width="60%" height="60%" alt="autotyper_v1" src="https://github.com/user-attachments/assets/8bdffa3a-2b4f-4d84-9a5e-2a06c8a5465c" />|
---
> *PyQt6 GUI*

|autotyper_v2_1.py|autotyper_v2_2.py|autotyper_v2_3.py|
|:---:|:---:|:---:|
|<img width="702" height="932" alt="autotyper_v2_1" src="https://github.com/user-attachments/assets/d9455415-6b5d-4dbb-a6cc-4abbbaa74bf4" />|<img width="602" height="882" alt="autotyper_v2_2" src="https://github.com/user-attachments/assets/7e467627-937a-4286-a804-a91c5e317f3d" />|<img width="553" height="732" alt="autotyper_v2_3" src="https://github.com/user-attachments/assets/295a75e0-2148-4856-bf4a-0b0984c5d2d6" />|
---
> *PyQt6 Minimalistic & Modern GUI*

|autotyper_v3.py|autotyper_v4.py|autotyper_v5.py|
|:---:|:---:|:---:|
|<img width="502" height="824" alt="autotyper_v3" src="https://github.com/user-attachments/assets/fb1e9725-8aac-4f91-afdf-c0939287b7ef" />|<img width="453" height="788" alt="autotyper_v4" src="https://github.com/user-attachments/assets/3d9318cd-dc7c-4d12-84e5-e02feb0f8a5f" />|<img width="453" height="832" alt="autotyper_v5" src="https://github.com/user-attachments/assets/9f522bc4-e277-48f7-8480-4309834853fe" />|

---

## 🚀 Quick Start

### Prerequisites
*   Python 3.10+ installed.

### Installation

1.  **Clone the repo**
    ```bash
    git clone https://github.com/Himanshu-369/AutoTyper_v2.git
    cd AutoTyper_v2
    ```

2.  **Install Dependencies**
    
    **Option A: For the CustomTkinter version (`autotyper_v1.py`)**
    ```bash
    pip install customtkinter pyautogui
    ```

    **Option B: For the PyQt6 versions (`autotyper_v2_1.py` through `autotyper_v5.py`)**
    ```bash
    pip install PyQt6 pyautogui
    ```

### Running the App

Simply run the specific script you prefer:

```bash
# Run the CustomTkinter version
python autotyper_v1.py

# Run the latest PyQt6 version
python autotyper_v5.py
```

---

## 🎮 Usage Guide

1.  **Launch:** Execute the script. The window supports "Always on Top" mode so you can drag it over your target text field.
2.  **Input Text:** Type your message, paste from clipboard, or load a text file.
3.  **Select Profile:**
    *   **Pro Typist:** Fast, low errors.
    *   **Lazy Student:** Slow, inconsistent, frequent pauses.
    *   **Tired Human:** High fatigue, increasing error rate.
    *   **Just Type:** Standard settings.
4.  **Customize (Optional):** Manually adjust sliders to tweak specific behaviors (e.g., increase "Swap Errors").
5.  **Execute:** Click **START TYPING**. Switch focus to your target window immediately after the countdown.

---

## ⚙️ Configuration Parameters

| Parameter | Description |
| :--- | :--- |
| **WPM (Speed)** | The base typing speed in Words Per Minute. |
| **Start Delay** | Seconds to wait before typing begins (gives you time to click the target field). |
| **Fatigue** | How much the speed drops and errors rise over time. |
| **Typos (Corrected)** | Random mistakes that are immediately backspaced and fixed. |
| **Typos (Ignored)** | Mistakes that are left in the final text. |
| **Swap Errors** | Transposes adjacent letters (e.g., "adn" instead of "and"). |
| **Word Rethink** | Types a word, deletes it, then retypes it (simulates hesitation). |
| **Double Space** | Chance to hit the spacebar twice after a word. |
| **Paragraph Pause** | Extra delay added when encountering newlines (`\n`). |

---

## 📂 Project Structure

This repository serves as a history of development, showcasing the transition from basic scripts to polished GUI applications.

```text
.
├── autotyper_v1.py           # Initial version using CustomTkinter.
├── autotyper_v2_1.py       # First PyQt6 iteration.
├── autotyper_v2_2.py       # UI improvements and layout adjustments.
├── autotyper_v2_3.py       # Enhanced grouping and modular widgets.
├── autotyper_v3.py         # Introduction of custom reusable components.
├── autotyper_v4.py         # Advanced styling and aesthetics.
├── autotyper_v5.py         # Latest version with refined logic and UI.
└── README.md           # This file.
```

### 🛠️ Tech Stack
*   **Logic:** `Python 3.10+`
*   **Automation:** `pyautogui` (Keyboard simulation)
*   **GUI:**
    *   `PyQt6` (Primary versions)
    *   `CustomTkinter` (Legacy version)

---

## 🤝 Contributing

This project is open to improvements! If you have a idea for a new "human" behavior (e.g., "Caffeinated Jitter" or "Angry Typing"), feel free to open an issue or submit a pull request.

---

## ⚠️ Disclaimer

This tool is for educational purposes, UI testing, and legitimate automation. Please use responsibly. Misuse of automated typing tools to violate terms of service (e.g., in online games or restricted chats) is not endorsed by the author.

---

<div align="center">
  <sub>Built with ❤️ and a lot of coffee.</sub>
</div>
