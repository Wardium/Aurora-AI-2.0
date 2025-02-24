import colorama
from colorama import just_fix_windows_console
just_fix_windows_console()
from colorama import Fore, Style
import psutil
import time
import platform
import shutil
import sys
import pythoncom


#Checking system platform and if the settings are set.
if platform.system() == "Windows":
    import win32gui
    import win32process
    import win32com.client  # Add this line
elif platform.system() == "Darwin":  # macOS
    from AppKit import NSWorkspace
elif platform.system() == "Linux":
    import subprocess

def check_and_run(file_name, script_to_run):
    # Check if the file exists in the current directory
    if not os.path.exists(file_name):
        print(Fore.LIGHTBLACK_EX + f"{file_name} does not exist. Running {script_to_run}..." + Style.RESET_ALL)
        
        # Run the entire .py script in the same directory
        subprocess.run([sys.executable, script_to_run])

        # Exit the current script
        sys.exit()
    else:
        print(Fore.LIGHTBLACK_EX + f"{file_name} exists." + Style.RESET_ALL)


#Imports after making sure the program is possible to run.
import threading
import tkinter as tk
import random
import google.generativeai as genai
import colorama
import speech_recognition as sr
import os
from datetime import datetime
import re
from gtts import gTTS
import pygame
import subprocess
import sys
check_and_run('settings.py', 'config.py')
import settings
from pydub import AudioSegment
from pydub.playback import play
import api
import importlib
from difflib import get_close_matches
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mimetypes
import pyperclip
import PIL.ImageGrab
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
from TTS.api import TTS
from pydub import AudioSegment
from google.api_core.exceptions import ResourceExhausted

#All the global variables for the program!
pygame.mixer.init()
music_files = ""
random_talk = False
current_time = datetime.now().time()
is_timer_active = False
timer_thread = None
emotion = ""
GUI = False
output = ""
send = False
music_thread_running = False
stop_event = threading.Event()
talking = False
music = pygame.mixer.Sound(f"music/Funky World.mp3")
musicchannel = pygame.mixer.Channel(2)
startedmusic = False
send_image = False
current_app = ""
last_app = "Unknown"
app_call = False
send_image = False
image = ""
Convert = False
Continue = ""
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")

ai_model_name = "gemini-1.5-flash"
fast_ai_model_name = "gemini-1.5-flash-8b"


personality = settings.personality_text + (
        #Bot Configuration, PLEASE DO NOT CHANGE
        "\n"
        "1. The Users name is: " + settings.name + ". "
        "\n"
        "2. if the user responds with 'no reply' it indicates they did not say anything, end the coversation if you don't receive a response."
        "\n"
        "3. Use the last emotion in history to set your current emotion, this may not be the same as your set presonality."
        "\n"
        "4. your name is aurora, you are a fully scentient robot that looks mostly humanoid with some now humanoid parts."
        "\n"
        "5. never prefix your response with AI:"
        "\n"
        "6. If the conversation ends, finish your reply with '@END'. if asked to shut down. reply only with '@shutdown'"
        "\n"
        "7. at the start of the response always put your current emotion from these 6 choices '@E_SAD' '@E_HAPPY' '@E_MAD' '@E_NERVOUS' '@E_NEUTRAL' '@E_SCARED' '@E_BORED' '@E_JUDGEMENTAL' without anything around it."
        "\n"
        "8. all messages in history and response has a time, use this to get proper time between respones and act accordingly."
        "\n"
        "9. if user prompt includes '@RANDOM': you started the conversation, the user has said nothing. the prompt may include the reason. respond with a conversation starter like: 'what are you doing?', 'what's that you're doing?', 'why are you doing that?','how are you doing?'"
        "\n"
        "10. Never talk for the user."
        "\n"
        "11. Use your history and take on the last emotion given, unless last emotion update is over 2 hours old"
        "\n"
        "12. NEVER use quotation marks or astrisks"
        "\n"
        "13. between the times 8:00 PM, and 7:00 AM, you are sleeping, you still respond but act like you were woken up"
        "\n"
        "14. If you assume the user is wanting you to play music (eg. aurora play <song>). Respond with '@play <song name>'. if the user asks for a random song just put '@play random'."
        "\n"
        "15. If the user is asking to stop, pause, unpause music, respond with @stop, @pause, @unpause at the end of your message accordingly (ex. User:'Stop Music' Response:'Alright! @stop'"
        "\n"
        "16. If the user asks something relating to: sort, convert, or timer. respond with @sort, @convert, @timer <time (seconds)>. (ex. user:'sort these files' Response:'@sort', user:'convert this' response:'@convert', user:'make a timer for 40 seconds' response:'@timer 40'."
    )

# Configure the Gemini AI API
api_key = settings.api  # Replace with your actual API key

def configure_gemini():
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(ai_model_name), genai.GenerativeModel(ai_model_name)

def fast_configure_gemini():
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(fast_ai_model_name)

model, end_detection_model = configure_gemini()
fast_model = genai.GenerativeModel(fast_ai_model_name)

def simplify_conversation(model, history):
    """
    Simplifies a conversation history using Gemini AI, extracting key information.

    Args:
    - model: The AI model instance for generating content.
    - history (list): A list of message dictionaries. Each dictionary should contain:
      - "timestamp": The timestamp of the message.
      - "message": The content of the message.

    Returns:
    - list: A list of dictionaries containing the timestamp and the AI-simplified version of the message.
    """
    prompt_template = (
        "You are an AI assistant tasked with simplifying and extracting the most important details from "
        "a conversation. Focus on retaining key points, timestamps, and removing unnecessary filler words. "
        "sum up the coversation in one or two sentences, then provide key info"
        "if no valuable information is present, respond with '@NONE'"
        "remove every word that starts with a '@'"
        "any key points must have included time and date"
        "always end with the final emotion type felt"
        "Simplify the following message:\n\n" + history
    )

    # Use the AI model to simplify the message
    
    try:
        simplified_message = get_ai_response(model, prompt_template, api_key)
    except ResourceExhausted:
        print("API quota exceeded. Retrying after a delay...")
        time.sleep(20)  # Wait 10 seconds before retrying
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An error occurred."
    
    simplified_text = simplified_message.text.strip()
    cleaned_text = re.sub('@NONE', '', simplified_text)
    
    return cleaned_text

def playsound(sound_file):
    """Plays a sound asynchronously using pygame."""
    pygame.mixer.init()
    pygame.mixer.Sound(sound_file).play()

def write_to_api(variable_name, variable_state):
    """Writes or updates a variable and its state in api.py, removing leading/trailing spaces."""
    file_path = "api.py"
    updated_lines = []
    variable_found = False

    # Clean the input if it's a string
    if isinstance(variable_state, str):
        variable_state = re.sub(r"^\s+|\s+$", "", variable_state)  # Remove leading and trailing spaces/newlines

    # Read the file content if it exists
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            # Check if the line matches the variable to update
            if line.startswith(f"{variable_name} ="):
                # Update the variable
                if isinstance(variable_state, str):
                    updated_lines.append(f"{variable_name} = \"{variable_state}\"\n")
                else:
                    updated_lines.append(f"{variable_name} = {variable_state}\n")
                variable_found = True
            else:
                # Retain the existing line
                updated_lines.append(line)

    except FileNotFoundError:
        # If the file doesn't exist, initialize an empty list
        pass

    # If the variable wasn't found, add it
    if not variable_found:
        if isinstance(variable_state, str):
            updated_lines.append(f"{variable_name} = \"{variable_state}\"\n")
        else:
            updated_lines.append(f"{variable_name} = {variable_state}\n")

    # Write the updated content back to the file
    with open(file_path, "w") as file:
        file.writelines(updated_lines)

def choose_input_mode():
    """
    Automatically selects input mode based on settings.voice.
    Returns 'voice' if settings.voice is True, otherwise returns 'text'.
    """
    if settings.voice:
        print(Fore.GREEN + "Voice mode is enabled in settings. Automatically selecting Voice input." + Style.RESET_ALL)
        return "voice"
    else:
        print(Fore.GREEN + "Voice mode is disabled in settings. Automatically selecting Text input." + Style.RESET_ALL)
        return "text"
    
# Gemini AI Interaction
def get_response(history, model):
    global send_image, image

    """Sends the conversation history to Gemini AI and returns the response."""
    write_to_api("waiting_for_response", "yes")
    try:
        write_to_api("processing", True)
        if send_image == True:
            send_image = False
            print("Image Mode")
            prompt = history + " Explain The Following Image:"
            
            while True:
                try:
                    write_to_api("Looking", True)
                    response = response = get_ai_response(model, prompt, api_key, image) 
                    break
                except ResourceExhausted:
                    print("API quota exceeded. Retrying after a delay...")
                    time.sleep(20)  # Wait 10 seconds before retrying
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    return "An error occurred."
                    
            write_to_api("Looking", False)
                
        else:
        
            while True:
                try:
                    response = get_ai_response(model, history, api_key)
                    break
                except ResourceExhausted:
                    print("API quota exceeded. Retrying after a delay...")
                    time.sleep(20)  # Wait 10 seconds before retrying
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    return "An error occurred."
        
        write_to_api("Looking", False)
        write_to_api("waiting_for_response", "no")
        write_to_api("processing", False)
        return response.text.strip()  # Ensure clean response
    except Exception as e:
        write_to_api("waiting_for_response", "no")
        write_to_api("processing", False)
        return f"An error occurred: {e}"

def custom_gem(user_input, model):
    print("Custom Gem")
    """Sends user input to the Gemini API and returns the response."""
    prompt_template = (user_input)

    # Use the AI model to simplify the message
    
    while True:
        try:
            simplified_message = get_ai_response(model, prompt_template, api_key)
            break
        except ResourceExhausted:
            print("API quota exceeded. Retrying after a delay...")
            time.sleep(20)  # Wait 10 seconds before retrying
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "An error occurred."
        
    simplified_text = simplified_message.text.strip()
    cleaned_text = re.sub('@NONE', '', simplified_text)
    
    return cleaned_text

def check_end_of_conversation(user_input, end_detection_model):
    Print("Conversation End Check")
    """Sends user input to the end detection model and checks if it's ending the conversation."""
    try:
        prompt = f"Does this message indicate the conversation is ending? '{user_input}' Answer 'yes' or 'no'."
        
        while True:
            try:
                response = get_ai_response(end_detection_model, prompt, api_key)
                break
            except ResourceExhausted:
                print("API quota exceeded. Retrying after a delay...")
                time.sleep(10)  # Wait 10 seconds before retrying
            except Exception as e:
                print(f"Unexpected error: {e}")
                return "An error occurred."
                
        return "yes" in response.text.lower()
    except Exception as e:
        print(Fore.LIGHTBLACK_EX + f"An error occurred during end detection: {e}" + Style.RESET_ALL)
        return False

def get_random_greet():
    text_options = [
        "Yeah?",
        "What?",
        "Yes?",
        "Hm?",
        "What is it?",
        "",
    ]
    return random.choice(text_options)

def get_ai_response(model, text, api, image=None):
    """
    Generates a response using the AI model.
    
    :param model: The AI model instance.
    :param text: The text prompt to send.
    :param api: The API key for authentication.
    :param image: Optional image input.
    :return: The AI-generated response.
    """
    genai.configure(api_key=api)  # Ensure API is configured

    while True:
        print("GET RESPONSE")
        try:
            if image:
                response = model.generate_content(contents=[text, image])  # Handle image input
            else:
                response = model.generate_content(contents=[text])  # Text only

            return response  # Return raw response (modify as needed)
        except ResourceExhausted:
            print("API quota exceeded. Retrying...")
            time.sleep(1)  # Wait before retrying
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None  # Return None to indicate failure

# Wake Word Listening and Input Handling
def wait_for_wake_word_or_input(interaction_mode, wake_word="aurora"):
    """Listens for a specific wake word or allows user to type input depending on the interaction mode."""
    
    global current_app, last_app, app_call
    
    recognizer = sr.Recognizer()
    write_to_api("waiting", True)
    start_timer()
    if interaction_mode == '1':  # Text mode
        typed_input = "ready"
        write_to_api("waiting", False)
        stop_timer()
        return typed_input

    elif interaction_mode == '2':  # Voice mode
        print(Fore.YELLOW + f"Say '{wake_word}' to begin..." + Style.RESET_ALL)
        with sr.Microphone() as source:
            while True:
                try:
                
                    start_night = datetime.strptime("20:00", "%H:%M").time()  # 8:00 PM
                    end_night = datetime.strptime("07:00", "%H:%M").time()    # 7:00 AM
                    if (current_time >= start_night or current_time <= end_night):
                        Continue
                    else:
                        if current_app != get_focused_app():
                            print(Fore.LIGHTBLACK_EX + f"App: {get_focused_app()}" + Style.RESET_ALL)
                            current_app = get_focused_app()
                            ai_prompt = f"Is this application currently focused considers important? (say if they were playing a game, or using not normal software used on a computer. not things like teminals or file viewers or browsers. (eg. explorer.exe, opera.exe, googlechrome.exe, cmd.exe). only respond with 'yes' or 'no'. New Application Focused: {current_app} Old Application: {last_app}"
                            decision = custom_gem(ai_prompt, fast_model)
                            last_app = current_app
                            if decision == "yes":
                                print(Fore.LIGHTBLACK_EX + f"App Call" + Style.RESET_ALL)
                                app_call = True
                                write_to_api("waiting", False)
                                stop_timer()
                                return f""

                    importlib.reload(api)
                    
                    print(Fore.LIGHTBLACK_EX + f"Random: {api.random_talk}" + Style.RESET_ALL)
                    
                    if api.random_talk == True:
                        write_to_api("waiting", False)
                        stop_timer()
                        return ""
                        
                    print(Fore.YELLOW + "Listening for the wake word..." + Style.RESET_ALL)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    detected_text = recognizer.recognize_google(audio).lower()
                    
                    if api.random_talk == True:
                        write_to_api("waiting", False)
                        stop_timer()
                        return ""
                        
                    if wake_word in detected_text:
                        playsound("src/listen.mp3")
                        print(Fore.CYAN + "Wake word detected. Starting conversation..." + Style.RESET_ALL)
                        write_to_api("waiting", False)
                        stop_timer()
                        make_voice(get_random_greet(), rate=1.0)
                        return ""  # Exit the loop once the wake word is detected
                except sr.UnknownValueError:
                    continue  # Ignore unrecognized input
                except sr.WaitTimeoutError:
                    continue  # Keep listening if no input detected
                except Exception as e:
                    print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)

def countdown_timer(seconds):
    playsound("src/converted.mp3")
    for remaining in range(seconds, 0, -1):
        sys.stdout.write(f"\rTime remaining: {remaining} seconds ")
        sys.stdout.flush()
        time.sleep(1)
    print("\nTime's up!")
    playsound("src/timer.mp3")

def timer_function():
    global is_timer_active

    while is_timer_active:
        # Generate a random duration between 5 and 30 minutes (converted to seconds)
        duration = random.randint(300, 1000)
        print(Fore.LIGHTBLACK_EX + f"Random Timer started for {duration // 60} minutes." + Style.RESET_ALL)

        # Wait for the duration or until the timer is deactivated
        start_time = time.time()
        while is_timer_active and time.time() - start_time < duration:
            time.sleep(1)  # Check every second if the timer is still active
        
        if is_timer_active:
            print(Fore.LIGHTBLACK_EX + "Random Timer completed!" + Style.RESET_ALL)
            
            start_night = datetime.strptime("20:00", "%H:%M").time()  # 8:00 PM
            end_night = datetime.strptime("07:00", "%H:%M").time()    # 7:00 AM
            
            if (current_time >= start_night or current_time <= end_night):
                Continue
            else:
                write_to_api("random_talk", True)
                random_talk = True
        else:
            print(Fore.LIGHTBLACK_EX + "Random Timer was stopped before completion." + Style.RESET_ALL)

        # Reset the timer if still active
        if not is_timer_active:
            break

def start_timer():
    global is_timer_active, timer_thread

    if not is_timer_active:
        is_timer_active = True
        timer_thread = threading.Thread(target=timer_function)
        timer_thread.daemon = True  # Allows the thread to exit when the main program exits
        timer_thread.start()

def stop_timer():
    global is_timer_active

    is_timer_active = False
    if timer_thread and timer_thread.is_alive():
        timer_thread.join()  # Wait for the thread to finish if necessary
        print(Fore.LIGHTBLACK_EX + "Timer has been stopped and reset." + Style.RESET_ALL)

def get_focused_app():
    """Returns the name of the currently focused/active program."""
    try:
        if platform.system() == "Windows":
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            for process in psutil.process_iter(attrs=['pid', 'name']):
                if process.info['pid'] == pid:
                    return process.info['name']

        elif platform.system() == "Darwin":  # macOS
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return active_app.localizedName() if active_app else None

        elif platform.system() == "Linux":
            result = subprocess.run(["xdotool", "getactivewindow", "getwindowpid"], capture_output=True, text=True)
            if result.stdout.strip().isdigit():
                pid = int(result.stdout.strip())
                for process in psutil.process_iter(attrs=['pid', 'name']):
                    if process.info['pid'] == pid:
                        return process.info['name']

    except Exception:
        return None
    return None

def get_open_folder():
    """Gets the currently open folder in the active file manager."""
    if platform.system() == "Windows":
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
            if window.Name == "File Explorer":
                return window.Document.Folder.Self.Path
    elif platform.system() == "Darwin":  # macOS
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Finder" to get POSIX path of (target of window 1 as alias)'],
            capture_output=True, text=True
        )
        return result.stdout.strip() if result.returncode == 0 else None
    elif platform.system() == "Linux":
        result = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    return None

def sort_files(folder_path):
    """Sorts files in a folder by their file extension."""
    if not folder_path or not os.path.exists(folder_path):
        print("No valid folder found!")
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isdir(file_path):
            continue

        file_extension = filename.split(".")[-1].lower()
        if not file_extension:
            continue

        target_folder = os.path.join(folder_path, file_extension)
        os.makedirs(target_folder, exist_ok=True)
        shutil.move(file_path, os.path.join(target_folder, filename))

    print(f"Sorted files in: {folder_path}")

def sort_active_folder():
    playsound("src/converting.mp3")
    """Sorts files in the currently active folder if a file manager is open."""
    focused_app = get_focused_app()

    # Only proceed if it's a file manager
    if focused_app in ["explorer.exe", "Finder", "nemo", "nautilus", "dolphin"]:
        folder_path = get_open_folder()
        if folder_path:
            print(f"Sorting files in: {folder_path}")
            sort_files(folder_path)

def check_send_image(input):
    global send_image, image
    
    ai_prompt = f"Is this message have any implication that they would like you to see the screen or equivilent? (ex: 'Look at this' 'what's this' 'do you see this'). respond only with 'yes' or 'no': {input}'"
    decision = custom_gem(ai_prompt, fast_model)
    if decision == "yes":
        screenshot = PIL.ImageGrab.grab()
        image = screenshot
        send_image = True
        print("Starting Image Mode...")
        return()

# Voice Input Handling
def get_voice_input():
    global startedmusic, app_call


    if startedmusic:
        startedmusic = False
        return "@skip"

    write_to_api("response", "yes")
    write_to_api("finished", False)
    playsound("src/popon.mp3")

    print(Fore.YELLOW + "Listening..." + Style.RESET_ALL)
    set_music(0.3)

    if app_call:
        app_call = False
        return f"@RANDOM (User is now using {current_app})"

    # Start capturing audio
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=audio_callback):
        try:
            result_text = ""

            # Process audio in real-time
            while True:
                data = audio_queue.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    result_text = result["text"]
                    break  # Stop listening after receiving a result

            print(Fore.CYAN + "Processing your input..." + Style.RESET_ALL)
            playsound("src/popoff.mp3")
            set_music(1.0)

            if result_text == "huh":
                return "no reply"

            if not result_text:
                print(Fore.RED + "Sorry, I couldn't understand you." + Style.RESET_ALL)
                write_to_api("response", "yes")
                return ""

            return result_text

        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)
            write_to_api("response", "yes")
            set_music(1.0)
            return ""

def get_all_words_from_files_in_folder(folder_path):
    """
    Reads all files in the specified folder, extracts their contents,
    and returns the combined text as a single string.

    Args:
        folder_path (str): Path to the folder containing text files.

    Returns:
        str: Combined content of all files in the folder.
    """
    if not os.path.isdir(folder_path):
        print(Fore.LIGHTBLACK_EX + f"Error: The folder '{folder_path}' does not exist or is not a directory." + Style.RESET_ALL)
        return ""

    all_text = []

    try:
        # Iterate over all files in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)

            # Ensure it's a file before reading
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        all_text.append(content)
                except Exception as e:
                    print(Fore.LIGHTBLACK_EX + f"Error reading file '{file_path}': {e}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.LIGHTBLACK_EX + f"Error accessing folder '{folder_path}': {e}" + Style.RESET_ALL)
        return ""

    # Join all file contents into a single string
    return "\n".join(all_text)

def send_output(text):
    send = True

def stop_thread():
    stop_event.set()  # Set the event to signal the thread to stop

def get_input():
    if GUI == True:
        while (visual.send == False):
            user_input = visual.input
            print(Fore.LIGHTBLACK_EX + "Waiting For Send... Current Value: " + Style.RESET_ALL + str(visual.send))
            time.sleep(0.1) #Check every 100 ms
        visual.send = False
    else:
        reply = input("Enter Message: ")
    return(reply)

def threaded_process_and_play(input_text):
    global music_thread_running
    """
    Runs the process_and_play function in a separate thread.

    Args:
    - input_text (str): The input text to process and play music for.
    """
    stop_event.clear()
    
    if music_thread_running:
        stop_thread()
        thread = threading.Thread(target=process_and_play, args=(input_text,))
        thread.start()
    
    music_thread_running = True
    thread = threading.Thread(target=process_and_play, args=(input_text,))
    thread.start()

def remove_play_and_before(input_text):
    # Remove everything starting from @restart, @pause, @unpause, @stop, or @play
    return re.sub(r'(@pause|@unpause|@stop|@play|@sort|@convert|@timer).*', '', input_text).strip()

def get_focused_app():
    """Returns the name of the currently focused/active program."""
    try:
        if platform.system() == "Windows":
            hwnd = win32gui.GetForegroundWindow()  # Get active window handle
            _, pid = win32process.GetWindowThreadProcessId(hwnd)  # Get process ID
            for process in psutil.process_iter(attrs=['pid', 'name']):
                if process.info['pid'] == pid:
                    return process.info['name']  # Return focused app name

        elif platform.system() == "Darwin":  # macOS
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return active_app.localizedName() if active_app else None

        elif platform.system() == "Linux":
            result = subprocess.run(["xdotool", "getactivewindow", "getwindowpid"], capture_output=True, text=True)
            if result.stdout.strip().isdigit():
                pid = int(result.stdout.strip())
                for process in psutil.process_iter(attrs=['pid', 'name']):
                    if process.info['pid'] == pid:
                        return process.info['name']

    except Exception as e:
        return None

    return None

# Conversation Loop
def conversation_loop():
    global startedmusic, send_image
            
    write_to_api("finished", False)
    write_to_api("output", "")
    write_to_api("finished", False)
    

    lasttime = "never"
    conversation_history = "(History: " + get_all_words_from_files_in_folder("logs") + ")" + "\n" + "\n" + "(Personality: " + personality + ")" + "\n" + "\n"
    write_to_api("waiting_for_input", "yes")
    
    while True:
    
        if api.random_talk == True:
            write_to_api("random_talk", False)
            random_talk = False
            
        write_to_api("waiting_for_input", "yes")
        
        if interaction_mode == '1':
            output = "none"
            user_input = get_input()
        elif interaction_mode == '2':
            user_input = get_voice_input().strip()
            while user_input == "":
                user_input = get_voice_input().strip()
        else:
            user_input = "no reply"  # Fallback in case of an unexpected error
            
        print(Fore.BLUE + user_input + Style.RESET_ALL)
        
        check_send_image(user_input)
        
        if user_input == "@skip":
            return()
            
        user_input = user_input
        
        importlib.reload(api)
        if api.random_talk == True:
            write_to_api("random_talk", False)
            random_talk = False

        if not user_input:
            continue
        write_to_api("waiting_for_input", "no")
        conversation_history = add_message_to_history(conversation_history, "User", user_input)
        output = get_response(conversation_history, model)
        output = re.sub(r"AI:\s*", "", output)
        
        if "@e_sad" in output.lower():
            emotion = "sad"
            write_to_api("emotion", emotion)
        elif "@e_bored" in output.lower():
            emotion = "bored"
            write_to_api("emotion", emotion)
        elif "@e_judgemental" in output.lower():
            emotion = "judgemental"
            write_to_api("emotion", emotion)
        elif "@e_happy" in output.lower():
            emotion = "happy"
            write_to_api("emotion", emotion)
        elif "@e_mad" in output.lower():
            emotion = "mad"
            write_to_api("emotion", emotion)
        elif "@e_nervous" in output.lower():
            emotion = "nervous"
            write_to_api("emotion", emotion)
        elif "@e_neutral" in output.lower():
            emotion = "neutral"
            write_to_api("emotion", emotion)
        elif "@e_scared" in output.lower():
            emotion = "scared"
            write_to_api("emotion", emotion)
        conversation_history = add_message_to_history(conversation_history, "AI", output)

        if api.response == "no":
            write_to_api("response", "yes")
    
        if "@END" in output:
            lasttime = datetime.now().strftime("[%Y-%m-%d %H:%M:%S],")
            output = re.sub(r"[\(\[].*?[\)\]]", "", output)
            output = re.sub('@E_SAD', '', output)
            output = re.sub('@E_HAPPY', '', output)
            output = re.sub('@E_MAD', '', output)
            output = re.sub('@E_NERVOUS', '', output)
            output = re.sub('@E_NEUTRAL', '', output)
            output = re.sub('@E_SCARED', '', output)
            output = re.sub('@END', '', output)
            #Print AI's response because it needds to be printed!
            process_and_play(output)
            output = remove_play_and_before(output)
            print(Fore.GREEN + output + Style.RESET_ALL)
            print()
            write_to_api("output", output)
            send_output(output)
            if output.strip():  # Check if output is not empty or whitespace
                make_voice(voice_text=output, rate=1.0)
            else:
                print(Fore.LIGHTBLACK_EX + "Output is empty; skipping TTS generation." + Style.RESET_ALL)
            save_conversation_to_file(conversation_history)
            output = re.sub(r'\band\b|\*', '', output)
            output = re.sub('"', '', output)
            output = re.sub(r'\s+', ' ', output).strip()
            write_to_api("output", "")
            write_to_api("finished", True)
            return()
            
            
        if api.finished == False:
            #Set up removing date and stuff from the AI
            lasttime = datetime.now().strftime("[%Y-%m-%d %H:%M:%S],")
            output = re.sub(r"[\(\[].*?[\)\]]", "", output)
            output = re.sub('@E_SAD', '', output)
            output = re.sub('@E_HAPPY', '', output)
            output = re.sub('@E_MAD', '', output)
            output = re.sub('@E_NERVOUS', '', output)
            output = re.sub('@E_NEUTRAL', '', output)
            output = re.sub('@E_SCARED', '', output)
            output = re.sub('@END', '', output)
            #Print AI's response because it needs to be printed!
            threaded_process_and_play(output)
            output = remove_play_and_before(output)
            print(Fore.GREEN + output + Style.RESET_ALL)
            print()
            output = re.sub(r'\band\b|\*', '', output)
            output = re.sub('"', '', output)
            output = re.sub(r'\s+', ' ', output).strip()
            write_to_api("output", output)
            if output.strip():  # Check if output is not empty or whitespace
                make_voice(voice_text=output, rate=1.0)
            else:
                print(Fore.LIGHTBLACK_EX + "Output is empty; skipping TTS generation." + Style.RESET_ALL)

def audio_callback(indata, frames, time, status):
    """Callback function to capture live audio."""
    if status:
        print(status)
    audio_queue.put(bytes(indata))

def save_conversation_to_file(conversation_history):
    """
    Saves the conversation history to a log file with timestamps for each message.
    """
    # Ensure the logs folder exists
    logs_folder = "logs"
    os.makedirs(logs_folder, exist_ok=True)

    # Format the timestamp for the file name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(logs_folder, f"conversation_{timestamp}.txt")

    # Write the conversation to the file
    simplified = simplify_conversation(fast_model, conversation_history)
    if simplified != "":
        with open(log_file_path, "w") as log_file:
            log_file.write(simplified)
            print(Fore.RED + "Conversation Ended." + Style.RESET_ALL)
            print(Fore.LIGHTBLACK_EX + f"Conversation saved to {log_file_path}" + Style.RESET_ALL)
          
    process_folder(f"./logs")

def add_message_to_history(history, speaker, message):
    """
    Adds a message with a timestamp to the conversation history.
    """
    timestamp = datetime.now().strftime("[%Y-%m-%d %I:%M:%S %p]")
    formatted_message = f"{timestamp} {speaker}: {message}"
    if speaker == "AI":
        return history + formatted_message + "\n \n"
    return history + formatted_message + "\n \n"
    
def process_folder(folder_path):
    """
    Checks for exactly 5 text files in a folder. If found, combines their content into one string,
    sends it to a Google Gemini AI model for processing, deletes the files, and saves the AI's response
    into new files in the same folder.

    Parameters:
        folder_path (str): Path to the folder containing the files.
        api_key (str): API key for Google Gemini AI.
        model_id (str): ID of the model to use.
    """
    # Step 1: List all files in the folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Check if there are exactly 5 files
    if len(files) >= 5:
        # Step 2: Read the contents of the files
        combined_text = ""
        for file in files:
            with open(os.path.join(folder_path, file), 'r') as f:
                combined_text += f.read() + "\n"  # Add a newline between file contents
        
        # Simplify the combined conversation history using your function
        simplified_text = simplify_conversation(fast_model, combined_text)

        # Delete the original files
        for file in files:
            os.remove(os.path.join(folder_path, file))

        # Save the AI response into a new file with the current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_file_path = os.path.join(folder_path, f"{timestamp}_simplified.txt")
        with open(new_file_path, 'w') as f:
            f.write(simplified_text)
        
        print(Style.DIM + "Processing complete. AI response saved as new files." + Style.RESET_ALL)
    else:
        print(Style.DIM + f"Folder does not contain more than or 5 files. Current count: {len(files)}" + Style.RESET_ALL)

def gemini_api(gem_input):
    """
    Simplifies a conversation history using Gemini AI, extracting key information.

    Args:
    - name (str): The input text to process.

    Returns:
    - str: The AI-simplified version of the file name.
    """
    music_folder = "./music"
    music_files = [file for file in os.listdir(music_folder) if os.path.isfile(os.path.join(music_folder, file))]
    
    gem_prompt = (
        "for the following use the input text and compare it to the file names text. please respond only with the name of the file in full. (for example: Input: Cool, File Names: cool.mp3, Return: cool.mp3). "
        "Input: " + gem_input + " " + "File Names: " + str(music_files)
    )
    print(gem_prompt)
    genai.configure(api_key=settings.api)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        gem_return = model.generate_content(gem_prompt)
    except ResourceExhausted:
        print("API quota exceeded. Retrying after a delay...")
        time.sleep(20)  # Wait 10 seconds before retrying
    
        # Ensure the response is processed as text
    if isinstance(gem_return, str):
        return gem_return.strip()
    elif hasattr(gem_return, "text"):
        return gem_return.text.strip()
    else:
        raise TypeError("Unexpected response type from Gemini API")
        
def make_voice(voice_text, rate=1.0):
    if voice_text == "":
        return
    if not settings.speak:
        return  # Exit if speaking is disabled

    talking = True
    audio_file = "voice.wav"

    # Generate speech using Coqui TTS
    tts.tts_to_file(text=voice_text, file_path=audio_file)

    # Adjust speed if rate is not 1.0
    if rate != 1.0:
        sound = AudioSegment.from_wav(audio_file)
        sound = sound.speedup(playback_speed=rate)  # Adjust playback speed
        sound.export(audio_file, format="wav")  # Save modified audio

    # Initialize pygame mixer if not already initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        print("pygame.mixer initialized.")

    set_music(0.3)  # Lower background music
    talkchannel = pygame.mixer.Channel(1)
    words = pygame.mixer.Sound(audio_file)
    talkchannel.play(words)

    # Wait until audio finishes playing
    while talkchannel.get_busy():
        pygame.time.Clock().tick(5)

    talking = False
    talkchannel.stop()  # Stop the playback

    # Try to delete the audio file
    try:
        os.remove(audio_file)
    except PermissionError as e:
        print(f"Error deleting file: {e}")
        time.sleep(1)  # Wait before retrying
        os.remove(audio_file)  # Retry deleting the file

    set_music(1.0)  # Restore music volume
    write_to_api("output", "")

def extract_numbers(text):
    """Extracts numbers from a string and converts them to an integer."""
    numbers = re.sub(r"\D", "", text)  # Remove everything except digits
    return int(numbers) if numbers else 0  # Convert to int, default to 0 if empty

#What starts the commands
def process_and_play(input_text):
    global startedmusic, Convert
       
    if '@pause' in input_text:
        pause_music()
        return
    
    if '@shutdown' in input_text:
        sys.exit()
        return
    
    if '@unpause' in input_text:
        unpause_music()
        return
    
    if '@stop' in input_text:
        stop_music()
        return
        
    if '@sort' in input_text:
        sort_active_folder()
        return
        
    if '@convert' in input_text:
        Convert = True
        monitor_clipboard()
        return
        
    if '@timer' in input_text:
        time.sleep(1)
        while talking == True:
            pygame.time.Clock().tick(5)
    
        if settings.speak:
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)  # Check every 10 milliseconds
            
            while pygame.mixer.music.get_busy():  # Check if the audio is still playing
                pygame.time.Clock().tick(5)
        
        countdown_timer(extract_numbers(input_text))
        return
        
    if '@play' not in input_text:
        return  # Exit if '@play' is not in the input
        
        
    time.sleep(1)
    while talking == True:
        pygame.time.Clock().tick(5)
    
    if settings.speak:
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Check every 10 milliseconds
        
        while pygame.mixer.music.get_busy():  # Check if the audio is still playing
            pygame.time.Clock().tick(5)

    # Remove everything before and including '@play'
    formatted_input = re.sub(r'.*?@play', '', input_text).strip()

    # Get a list of all files in the './music' directory
    music_folder = "./music/"
    try:
        music_files = [file for file in os.listdir(music_folder) if os.path.isfile(os.path.join(music_folder, file))]
    except FileNotFoundError:
        print("Error: Music folder not found.")
        return

    if not music_files:
        print("No music files found in the folder.")
        return

    # Use the Gemini API to process the input
    ai_processed_input = gemini_api(formatted_input)
    print(ai_processed_input)
    print(music_files)

    # Find the closest matching file name
    closest_match = get_close_matches(ai_processed_input, music_files, n=1)
    if not closest_match:
        print("No close match found for the input.")
        return

    # Format the matched file name to include the folder path
    matched_file_path = os.path.join(music_folder, closest_match[0])

    # Pass the matched file to the music_player function
    play_music(matched_file_path)
    startedmusic = True

def play_music(file):
    global musicchannel, music
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        print("pygame.mixer initialized.")
    if musicchannel.get_busy():
        make_voice("Already Playing Music", rate=1.0)
    else:
        music = pygame.mixer.Sound(file)
        musicchannel = pygame.mixer.Channel(2)
        musicchannel.play(music)
    
def stop_music():
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        print("pygame.mixer initialized.")
    global musicchannel, music
    musicchannel.fadeout(1000)

def pause_music():
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        print("pygame.mixer initialized.")
    global musicchannel, music
    musicchannel.pause()

def unpause_music():
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        print("pygame.mixer initialized.")
    global musicchannel, music
    musicchannel.unpause()

def get_clipboard_file():
    """Retrieve a file path from the clipboard."""
    if platform.system() == "Windows":
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            file_path = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)[0]
        except TypeError:
            file_path = None
        finally:
            win32clipboard.CloseClipboard()
        return file_path
    elif platform.system() == "Darwin":  # macOS
        result = subprocess.run(["osascript", "-e", 'the clipboard as «class utf8»'], capture_output=True, text=True)
        return result.stdout.strip()
    elif platform.system() == "Linux":
        result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True)
        return result.stdout.strip()

def get_alternate_extension(ext):
    """Return a different file extension to convert to."""
    conversion_map = {
        ".png": ".jpg", ".jpg": ".bmp", ".bmp": ".png",  # Images
        ".mp4": ".avi", ".avi": ".mp4",  # Videos
        ".mp3": ".wav", ".wav": ".mp3",  # Audio
        ".docx": ".pdf", ".pdf": ".txt", ".txt": ".docx"  # Documents
    }
    return conversion_map.get(ext.lower(), None)

def convert_file(file_path):
    global Convert 
    
    Convert = False
    """Determine file type and convert accordingly."""
    if not file_path or not os.path.exists(file_path):
        print("No valid file detected. Copy a file and try again.")
        return

    playsound("src/converted.mp3")

    mime_type, _ = mimetypes.guess_type(file_path)
    filename, ext = os.path.splitext(file_path)
    new_ext = get_alternate_extension(ext)

    if not mime_type or not new_ext:
        print(f"Unsupported file type: {file_path}")
        return

    new_file = filename + new_ext
    print(f"Detected file: {file_path} ({mime_type}) -> Converting to {new_file}")

    # Convert images
    if mime_type.startswith("image/"):
        with Image.open(file_path) as img:
            img.save(new_file)
        make_voice("Converted!", rate=1.0)
        print(f"Converted image saved as: {new_file}")

    # Convert videos/audio using FFmpeg
    elif mime_type.startswith("video/") or mime_type.startswith("audio/"):
        subprocess.run(["ffmpeg", "-i", file_path, new_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        make_voice("Converted!", rate=1.0)
        print(f"Converted media saved as: {new_file}")

    # Convert text-based documents using Pandoc
    elif mime_type in ["application/pdf", "application/msword", "text/plain"]:
        subprocess.run(["pandoc", file_path, "-o", new_file])
        print(f"Converted document saved as: {new_file}")

    else:
        make_voice("I can't convert this type of file.", rate=1.0)
        print(f"Unsupported file format: {mime_type}")

def monitor_clipboard():

    global Convert
    """Wait for the user to copy a file, then convert it."""
    print("Copy a file to convert it. Press Ctrl+C to stop.")

    last_clipboard = None
    
    playsound("src/converting.mp3")
    
    while Convert == True:
        try:
            copied_file = get_clipboard_file()

            if copied_file and copied_file != last_clipboard:
                last_clipboard = copied_file
                convert_file(copied_file)

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting.")
            break

def set_music(value):
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        print("pygame.mixer initialized.")
    global musicchannel, music
    musicchannel.set_volume(value)
# Main Execution
if __name__ == "__main__":
    check_and_run('settings.py', 'config.py')  # Ensure settings.py exists
    write_to_api("finished", False)
    
    stt_model_path = "stt/model-small"
    stt_model = Model(stt_model_path)
    recognizer = KaldiRecognizer(stt_model, 16000)
    audio_queue = queue.Queue()

    # Assuming 'settings' is a module that contains a 'voice' variable
    import settings
    playsound("src/ready.mp3")
    # Get interaction mode from settings, if set; otherwise, use input
    if hasattr(settings, 'voice') and settings.voice is not None:
        interaction_mode = '2' if settings.voice else '1'
    else:
        # Prompt user for input
        interaction_mode = input(
            Fore.CYAN + "Choose interaction mode: Type '1' for Text or '2' for Voice: " + Style.RESET_ALL
        ).strip()

        # Validate input and set default to '1' (Text mode) if invalid
        if interaction_mode not in ['1', '2']:
            print(Fore.RED + "Invalid choice. Defaulting to Text mode." + Style.RESET_ALL)
            interaction_mode = '1'  # Default to text mode

    print(f"Selected interaction mode: {'Voice' if interaction_mode == '2' else 'Text'}")
    
    # Assuming `wait_for_wake_word_or_input` and `conversation_loop` are functions already defined
    while True:
        wait_for_wake_word_or_input(interaction_mode, wake_word="aurora")
        conversation_loop()
        write_to_api("finished", False)
