import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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
from PIL import Image, ImageTk
import queue
import sys

# ============ CONFIGURATION MANAGER ============
class ConfigManager:
    def __init__(self):
        self.config_file = "recorder_config.json"
        self.default_config = {
            "voice": {
                "sample_rate": 44100,
                "channels": 1,
                "format": "int16",
                "save_path": "recordings/voice"
            },
            "screen": {
                "fps": 20,
                "save_path": "recordings/screen",
                "quality": "high"
            },
            "keylogger": {
                "log_file": "keylog.txt",
                "max_log_size_mb": 5,
                "log_mouse": True,
                "save_path": "logs"
            },
            "app": {
                "theme": "dark",
                "auto_save": True,
                "minimize_to_tray": False
            }
        }
        self.config = self.load_config()
        self.create_directories()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config=None):
        if config is None:
            config = self.config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def create_directories(self):
        for key in self.config:
            if 'save_path' in self.config[key]:
                os.makedirs(self.config[key]['save_path'], exist_ok=True)

# ============ VOICE RECORDER ============
class VoiceRecorderGUI:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.recording = False
        self.audio_data = []
        self.stream = None
        
    def record(self):
        self.recording = True
        self.audio_data = []
        
        def callback(indata, frames, time, status):
            if self.recording:
                self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.config['voice']['sample_rate'],
            channels=self.config['voice']['channels'],
            callback=callback,
            dtype=self.config['voice']['format']
        )
        self.stream.start()
    
    def stop(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        audio = np.concatenate(self.audio_data, axis=0)
        filename = f"{self.config['voice']['save_path']}/voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        wav.write(filename, self.config['voice']['sample_rate'], audio)
        return filename

# ============ SCREEN RECORDER ============
class ScreenRecorderGUI:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.recording = False
        self.out = None
        self.recording_thread = None
        
    def start_recording(self):
        screen_size = pyautogui.size()
        filename = f"{self.config['screen']['save_path']}/screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(filename, fourcc, self.config['screen']['fps'], screen_size)
        
        self.recording = True
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
        return filename
    
    def _record(self):
        while self.recording:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            self.out.write(frame)
            time.sleep(1.0 / self.config['screen']['fps'])
    
    def stop_recording(self):
        self.recording = False
        if self.recording_thread:
            self.recording_thread.join()
        if self.out:
            self.out.release()

# ============ KEYLOGGER ============
class KeyloggerGUI:
    def __init__(self, parent, config, log_callback):
        self.parent = parent
        self.config = config
        self.log_callback = log_callback
        self.running = False
        self.keys = []
        self.mouse_events = []
        self.keyboard_listener = None
        self.mouse_listener = None
        
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
            else:
                self.keys.append(f'[{key}]')
        
        # Real-time log display
        if self.keys:
            self.log_callback(''.join(self.keys[-10:]))
    
    def on_click(self, x, y, button, pressed):
        action = "clicked" if pressed else "released"
        msg = f"Mouse {action} at ({x}, {y}) with {button}"
        self.mouse_events.append(msg)
        self.log_callback(msg)
    
    def start(self):
        self.running = True
        self.keyboard_listener = pynput_keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()
        
        if self.config['keylogger']['log_mouse']:
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.mouse_listener.start()
    
    def stop(self):
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        # Save logs
        filename = f"{self.config['keylogger']['save_path']}/keylog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(f"Keylog saved at: {datetime.now()}\n")
            f.write(''.join(self.keys))
            f.write('\n\n' + '\n'.join(self.mouse_events))
        return filename

# ============ MAIN GUI APPLICATION ============
class RecorderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎤🔐🎥 Ultimate Recorder Suite")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.voice_recorder = None
        self.screen_recorder = None
        self.keylogger = None
        
        # Status variables
        self.voice_status = False
        self.screen_status = False
        self.keylog_status = False
        
        # Setup UI
        self.setup_ui()
        
        # Message queue for thread safety
        self.message_queue = queue.Queue()
        self.process_messages()
        
    def setup_ui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(fill='x', padx=20, pady=10)
        
        title = tk.Label(title_frame, text="🎤🔐🎥 ULTIMATE RECORDER SUITE", 
                        font=('Arial', 20, 'bold'), bg='#1e1e1e', fg='#00ff00')
        title.pack()
        
        subtitle = tk.Label(title_frame, text="Professional Recording Tool | Voice | Screen | Keylogger", 
                           font=('Arial', 10), bg='#1e1e1e', fg='#888888')
        subtitle.pack()
        
        # Main Container
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left Panel - Controls
        left_panel = tk.Frame(main_container, bg='#2d2d2d', relief='ridge', bd=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Voice Recorder Section
        voice_frame = tk.LabelFrame(left_panel, text="🎤 Voice Recorder", 
                                    font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00', 
                                    relief='ridge', bd=2)
        voice_frame.pack(fill='x', padx=10, pady=10)
        
        self.voice_btn = tk.Button(voice_frame, text="🔴 Start Recording", 
                                   command=self.toggle_voice, bg='#ff4444', fg='white',
                                   font=('Arial', 10, 'bold'), height=2)
        self.voice_btn.pack(pady=10, padx=20, fill='x')
        
        self.voice_status_label = tk.Label(voice_frame, text="● Idle", 
                                          font=('Arial', 10), bg='#2d2d2d', fg='#888888')
        self.voice_status_label.pack()
        
        # Screen Recorder Section
        screen_frame = tk.LabelFrame(left_panel, text="🎥 Screen Recorder", 
                                     font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00',
                                     relief='ridge', bd=2)
        screen_frame.pack(fill='x', padx=10, pady=10)
        
        self.screen_btn = tk.Button(screen_frame, text="🎬 Start Recording", 
                                    command=self.toggle_screen, bg='#ff4444', fg='white',
                                    font=('Arial', 10, 'bold'), height=2)
        self.screen_btn.pack(pady=10, padx=20, fill='x')
        
        self.screen_status_label = tk.Label(screen_frame, text="● Idle", 
                                           font=('Arial', 10), bg='#2d2d2d', fg='#888888')
        self.screen_status_label.pack()
        
        # Keylogger Section
        keylog_frame = tk.LabelFrame(left_panel, text="🔐 Keylogger", 
                                     font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00',
                                     relief='ridge', bd=2)
        keylog_frame.pack(fill='x', padx=10, pady=10)
        
        self.keylog_btn = tk.Button(keylog_frame, text="🔑 Start Keylogger", 
                                    command=self.toggle_keylogger, bg='#ff4444', fg='white',
                                    font=('Arial', 10, 'bold'), height=2)
        self.keylog_btn.pack(pady=10, padx=20, fill='x')
        
        self.keylog_status_label = tk.Label(keylog_frame, text="● Stopped", 
                                           font=('Arial', 10), bg='#2d2d2d', fg='#888888')
        self.keylog_status_label.pack()
        
        # Settings Button
        settings_btn = tk.Button(left_panel, text="⚙️ Settings", 
                                 command=self.open_settings, bg='#555555', fg='white',
                                 font=('Arial', 10, 'bold'), height=2)
        settings_btn.pack(pady=10, padx=20, fill='x')
        
        # Right Panel - Live Log
        right_panel = tk.Frame(main_container, bg='#2d2d2d', relief='ridge', bd=2)
        right_panel.pack(side='right', fill='both', expand=True)
        
        log_label = tk.Label(right_panel, text="📋 Live Activity Log", 
                            font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00')
        log_label.pack(pady=10)
        
        self.log_area = scrolledtext.ScrolledText(right_panel, height=30, width=40,
                                                  bg='#1e1e1e', fg='#00ff00',
                                                  insertbackground='white',
                                                  font=('Consolas', 9))
        self.log_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Status Bar
        self.status_bar = tk.Label(self.root, text="Ready | All systems operational", 
                                   bg='#2d2d2d', fg='#888888', relief='sunken')
        self.status_bar.pack(fill='x', side='bottom')
        
    def toggle_voice(self):
        if not self.voice_status:
            self.voice_recorder = VoiceRecorderGUI(self.root, self.config_manager.config)
            self.voice_recorder.record()
            self.voice_status = True
            self.voice_btn.config(text="⏹️ Stop Recording", bg='#44ff44', fg='black')
            self.voice_status_label.config(text="● Recording...", fg='#ff4444')
            self.add_log("🎤 Voice recording started")
            self.status_bar.config(text="Recording voice...")
        else:
            filename = self.voice_recorder.stop()
            self.voice_status = False
            self.voice_btn.config(text="🔴 Start Recording", bg='#ff4444', fg='white')
            self.voice_status_label.config(text="● Idle", fg='#888888')
            self.add_log(f"✅ Voice saved: {filename}")
            self.status_bar.config(text=f"Voice saved: {os.path.basename(filename)}")
    
    def toggle_screen(self):
        if not self.screen_status:
            self.screen_recorder = ScreenRecorderGUI(self.root, self.config_manager.config)
            filename = self.screen_recorder.start_recording()
            self.screen_status = True
            self.screen_btn.config(text="⏹️ Stop Recording", bg='#44ff44', fg='black')
            self.screen_status_label.config(text="● Recording...", fg='#ff4444')
            self.add_log(f"🎥 Screen recording started: {filename}")
            self.status_bar.config(text="Recording screen...")
        else:
            self.screen_recorder.stop_recording()
            self.screen_status = False
            self.screen_btn.config(text="🎬 Start Recording", bg='#ff4444', fg='white')
            self.screen_status_label.config(text="● Idle", fg='#888888')
            self.add_log("✅ Screen recording stopped")
            self.status_bar.config(text="Screen recording saved")
    
    def toggle_keylogger(self):
        if not self.keylog_status:
            self.keylogger = KeyloggerGUI(self.root, self.config_manager.config, self.add_log)
            self.keylogger.start()
            self.keylog_status = True
            self.keylog_btn.config(text="⏹️ Stop Keylogger", bg='#44ff44', fg='black')
            self.keylog_status_label.config(text="● Running", fg='#ff4444')
            self.add_log("🔐 Keylogger started - Press ESC to stop")
            self.status_bar.config(text="Keylogger running... Press ESC to stop")
        else:
            filename = self.keylogger.stop()
            self.keylog_status = False
            self.keylog_btn.config(text="🔑 Start Keylogger", bg='#ff4444', fg='white')
            self.keylog_status_label.config(text="● Stopped", fg='#888888')
            self.add_log(f"✅ Keylogger stopped. Logs saved: {filename}")
            self.status_bar.config(text=f"Keylogger saved: {os.path.basename(filename)}")
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x500")
        settings_window.configure(bg='#2d2d2d')
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Voice Settings
        voice_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(voice_frame, text="🎤 Voice")
        
        tk.Label(voice_frame, text="Sample Rate:", bg='#2d2d2d', fg='white').grid(row=0, column=0, pady=5, padx=10, sticky='w')
        sample_rate_var = tk.StringVar(value=str(self.config_manager.config['voice']['sample_rate']))
        tk.Entry(voice_frame, textvariable=sample_rate_var, bg='#1e1e1e', fg='white').grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(voice_frame, text="Save Path:", bg='#2d2d2d', fg='white').grid(row=1, column=0, pady=5, padx=10, sticky='w')
        save_path_var = tk.StringVar(value=self.config_manager.config['voice']['save_path'])
        tk.Entry(voice_frame, textvariable=save_path_var, bg='#1e1e1e', fg='white', width=30).grid(row=1, column=1, pady=5, padx=10)
        
        # Screen Settings
        screen_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(screen_frame, text="🎥 Screen")
        
        tk.Label(screen_frame, text="FPS:", bg='#2d2d2d', fg='white').grid(row=0, column=0, pady=5, padx=10, sticky='w')
        fps_var = tk.StringVar(value=str(self.config_manager.config['screen']['fps']))
        tk.Entry(screen_frame, textvariable=fps_var, bg='#1e1e1e', fg='white').grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(screen_frame, text="Save Path:", bg='#2d2d2d', fg='white').grid(row=1, column=0, pady=5, padx=10, sticky='w')
        screen_path_var = tk.StringVar(value=self.config_manager.config['screen']['save_path'])
        tk.Entry(screen_frame, textvariable=screen_path_var, bg='#1e1e1e', fg='white', width=30).grid(row=1, column=1, pady=5, padx=10)
        
        # Keylogger Settings
        keylog_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(keylog_frame, text="🔐 Keylogger")
        
        tk.Label(keylog_frame, text="Save Path:", bg='#2d2d2d', fg='white').grid(row=0, column=0, pady=5, padx=10, sticky='w')
        keylog_path_var = tk.StringVar(value=self.config_manager.config['keylogger']['save_path'])
        tk.Entry(keylog_frame, textvariable=keylog_path_var, bg='#1e1e1e', fg='white', width=30).grid(row=0, column=1, pady=5, padx=10)
        
        log_mouse_var = tk.BooleanVar(value=self.config_manager.config['keylogger']['log_mouse'])
        tk.Checkbutton(keylog_frame, text="Log Mouse Events", variable=log_mouse_var, bg='#2d2d2d', fg='white').grid(row=1, column=0, columnspan=2, pady=5)
        
        def save_settings():
            self.config_manager.config['voice']['sample_rate'] = int(sample_rate_var.get())
            self.config_manager.config['voice']['save_path'] = save_path_var.get()
            self.config_manager.config['screen']['fps'] = int(fps_var.get())
            self.config_manager.config['screen']['save_path'] = screen_path_var.get()
            self.config_manager.config['keylogger']['save_path'] = keylog_path_var.get()
            self.config_manager.config['keylogger']['log_mouse'] = log_mouse_var.get()
            self.config_manager.save_config()
            self.config_manager.create_directories()
            self.add_log("⚙️ Settings saved")
            settings_window.destroy()
        
        tk.Button(settings_window, text="Save Settings", command=save_settings, 
                 bg='#00ff00', fg='black', font=('Arial', 10, 'bold')).pack(pady=10)
    
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_queue.put(f"[{timestamp}] {message}\n")
    
    def process_messages(self):
        try:
            while True:
                msg = self.message_queue.get_nowait()
                self.log_area.insert(tk.END, msg)
                self.log_area.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_messages)
    
    def on_closing(self):
        if self.voice_status:
            self.voice_recorder.stop()
        if self.screen_status:
            self.screen_recorder.stop_recording()
        if self.keylog_status:
            self.keylogger.stop()
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

# ============ ENTRY POINT ============
if __name__ == "__main__":
    app = RecorderApp()
    app.run()
