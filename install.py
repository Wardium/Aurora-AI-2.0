import os
import sys
import subprocess
import platform
import zipfile
import requests
import time

def download_and_setup_vosk():
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    model_dir = "stt/model-small"
    zip_path = "stt/vosk-model.zip"

    # Create the "stt" directory if it doesn't exist
    os.makedirs("stt", exist_ok=True)

    # Check if the model is already downloaded
    if os.path.exists(model_dir):
        print("Vosk model is already installed.")
        return

    # Download the model
    print("Downloading Vosk model... This may take a few minutes.")
    response = requests.get(model_url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
            f.write(chunk)

    print("Download complete. Extracting...")

    # Extract the ZIP file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("stt")

    # Rename extracted folder to "model-small"
    extracted_folder = "stt/vosk-model-small-en-us-0.15"
    if os.path.exists(extracted_folder):
        os.rename(extracted_folder, model_dir)

    # Remove the ZIP file
    os.remove(zip_path)
    
    print("Vosk model is ready in 'stt/model-small'.")

def run_command(command, check=True):
    """Runs a shell command safely."""
    try:
        subprocess.run(command, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")

def install_pip_packages():
    """Installs common Python dependencies."""
    print("Installing Python dependencies...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    run_command(f"{sys.executable} -m pip install -r requirements.txt")

    system = platform.system()
    if system == "Windows":
        run_command(f"{sys.executable} -m pip install psutil pywin32")
    elif system == "Linux":
        run_command(f"{sys.executable} -m pip install psutil")
        run_command("sudo apt install xdotool || sudo pacman -S xdotool || sudo dnf install xdotool")
    elif system == "Darwin":  # macOS
        run_command(f"{sys.executable} -m pip install psutil pyobjc-framework-AppKit")

def install_ffmpeg():
    """Guides the user to install FFmpeg."""
    print("\nFFmpeg is required for this project.")
    if platform.system() == "Windows":
        print("Download it from: https://www.ffmpeg.org")
    else:
        run_command("sudo apt install ffmpeg || sudo pacman -S ffmpeg || sudo dnf install ffmpeg || brew install ffmpeg")

def setup_repository():
    """Clones and sets up the Aurora AI repository."""
    repo_url = "https://github.com/Wardium/auroraai.git"
    repo_name = "auroraai"
    
    if not os.path.exists(repo_name):
        print("Cloning repository...")
        run_command(f"git clone {repo_url}")
    
    os.chdir(repo_name)

def main():
    print("Setting up Aurora AI...")
    
    time.sleep(3)
    
    # Step 2: Install FFmpeg
    install_ffmpeg()
    time.sleep(3)
    # Step 3: Install Python Dependencies
    install_pip_packages()
    time.sleep(3)
    download_and_setup_vosk()
    time.sleep(1)
    print("\nInstallation complete! You may need to restart your terminal or system for changes to take effect.")

if __name__ == "__main__":
    main()
