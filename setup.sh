#!/bin/bash
# ==========================================
# Raspberry Pi Voice Assistant Setup Script
# ==========================================

echo "🔧 Starting Raspberry Pi setup..."

# --- Update system ---
echo "📦 Updating system packages..."
sudo apt update -y && sudo apt upgrade -y

# --- Install Python & pip ---
echo "🐍 Installing Python3, pip and essentials..."
sudo apt install -y python3 python3-pip python3-venv python3-tk

# --- Install audio & camera dependencies ---
echo "🎙️ Installing audio, speech, and camera packages..."
sudo apt install -y portaudio19-dev espeak fswebcam libcamera-apps

# --- Create project directory (if not exists) ---
PROJECT_DIR=~/HPCS_VoiceAssistant
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit

# --- Create virtual environment ---
echo "🌐 Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# --- Upgrade pip inside venv ---
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# --- Check for requirements.txt ---
if [ ! -f "requirements.txt" ]; then
    echo "⚠️ requirements.txt not found in current directory!"
    echo "Please place your requirements.txt file in $PROJECT_DIR"
    deactivate
    exit 1
fi

# --- Install Python dependencies ---
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# --- Cleanup cache ---
pip cache purge -q

# --- Test basic imports ---
echo "✅ Verifying installation..."
python3 - <<'EOF'
try:
    import speech_recognition, pyttsx3, pyaudio, PIL, RPi.GPIO
    print("✅ All core modules imported successfully!")
except ImportError as e:
    print("❌ Missing module:", e)
EOF

echo "🎉 Setup complete! Activate the environment using:"
echo "    source $PROJECT_DIR/.venv/bin/activate"
echo "Then run your script with:"
echo "    python3 your_script.py"
