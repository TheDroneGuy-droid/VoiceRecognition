import time
import shutil
import subprocess
import threading
from datetime import datetime
import os

os.environ["TCL_LIBRARY"] = r"C:\Users\Murli Sharma\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
os.environ["TK_LIBRARY"] = r"C:\Users\Murli Sharma\AppData\Local\Programs\Python\Python313\tcl\tk8.6"
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import speech_recognition as sr

# --- GPIO Setup ---
try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BOARD)
    RELAY_PIN = 12
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

# --- Create Capture Directory ---
CAPTURE_DIR = os.path.expanduser("~/HPCS_Captures")
os.makedirs(CAPTURE_DIR, exist_ok=True)


# --- Text-to-Speech ---
def init_tts():
    import pyttsx3
    try:
        eng = pyttsx3.init()
        eng.setProperty('rate', 160)
        return eng
    except Exception:
        return None


engine = init_tts()


def speak(text):
    """Speaks text using pyttsx3 or espeak fallback."""
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
            return
        except Exception:
            pass
    subprocess.run(["espeak", text])


# --- Microphone Auto Detection ---
def detect_microphone():
    mics = sr.Microphone.list_microphone_names()
    if not mics:
        return None, []
    for i, name in enumerate(mics):
        if any(k in name.lower() for k in ["usb", "mic", "microphone", "audio"]):
            return i, mics
    return 0, mics  # fallback


def listen_command(status_var):
    recognizer = sr.Recognizer()
    mic_index, _ = detect_microphone()

    if mic_index is None:
        status_var.set("❌ No microphone detected")
        return ""

    status_var.set("🎤 Listening...")
    try:
        with sr.Microphone(device_index=mic_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)
        status_var.set("Processing...")
        return recognizer.recognize_google(audio).lower()

    except Exception:
        return ""


# --- Capture Photo ---
def capture_photo():
    filename = time.strftime("capture_%Y%m%d_%H%M%S.jpg")
    path = os.path.join(CAPTURE_DIR, filename)

    if shutil.which("fswebcam"):
        cmd = ["fswebcam", "-r", "640x480", "--no-banner", path]
    elif shutil.which("libcamera-still"):
        cmd = ["libcamera-still", "-o", path, "--width", "640", "--height", "480", "-n"]
    else:
        return None

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return path
    except:
        return None


# --- Relay Control ---
def activate_relay(status_var, answer_label):
    if not GPIO_AVAILABLE:
        answer_label.configure(text="Relay hardware not available.")
        speak("Relay hardware not available")
        return

    GPIO.output(RELAY_PIN, GPIO.HIGH)
    status_var.set("Relay ON")
    answer_label.configure(text="Relay is operated.")
    speak("Relay is operated")
    time.sleep(2)
    GPIO.output(RELAY_PIN, GPIO.LOW)
    status_var.set("Relay OFF")


# --- UI Application ---
class PiVoiceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pi Voice Assistant + Relay Control")
        self.geometry("800x600")

        self.status_var = tk.StringVar(value="Ready")
        self.relay_status = tk.StringVar(value="Relay OFF")

        ttk.Label(self, text="Raspberry Pi Voice Assistant", font=("Arial", 18, "bold")).pack(pady=10)
        self.answer_label = ttk.Label(self, text="Say a command...", font=("Arial", 14))
        self.answer_label.pack(pady=10)

        self.image_label = ttk.Label(self)
        self.image_label.pack(pady=10)

        frame = ttk.Frame(self)
        frame.pack(pady=20)
        ttk.Button(frame, text="🎤 Listen", command=self.listener).grid(row=0, column=0, padx=15)
        ttk.Button(frame, text="⚡ Relay", command=self.relay_manual).grid(row=0, column=1, padx=15)

        ttk.Label(self, textvariable=self.status_var, foreground="blue").pack(pady=5)
        ttk.Label(self, textvariable=self.relay_status, foreground="green").pack(pady=5)

    def listener(self):
        cmd = listen_command(self.status_var)

        if "time" in cmd:
            ans = datetime.now().strftime("The time is %H:%M:%S")
        elif "date" in cmd:
            ans = datetime.now().strftime("Today's date is %d %B %Y")
        elif "photo" in cmd:
            path = capture_photo()
            if path:
                img = Image.open(path).resize((350, 260))
                self.imgtk = ImageTk.PhotoImage(img)
                self.image_label.configure(image=self.imgtk)
                ans = "Photo captured"
            else:
                ans = "Camera not found"
        elif "relay" in cmd:
            threading.Thread(target=activate_relay, args=(self.relay_status, self.answer_label), daemon=True).start()
            ans = "Relay command executed"
        else:
            ans = "Sorry, I didn't understand"

        self.answer_label.configure(text=ans)
        speak(ans)
        self.status_var.set("Ready")

    def relay_manual(self):
        threading.Thread(target=activate_relay, args=(self.relay_status, self.answer_label), daemon=True).start()


if __name__ == "__main__":
    try:
        app = PiVoiceApp()
        app.mainloop()
    finally:
        if GPIO_AVAILABLE:
            GPIO.cleanup()
