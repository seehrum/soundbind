import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
from playsound import playsound
from pynput import keyboard, mouse
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SoundManager:
    def __init__(self, config_file='soundbind_config.json'):
        self.config_file = config_file
        self.sounds = {}
        self.mouse_sounds = {}
        self.universal_sound = ''
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                    self.sounds = config.get('sounds', {})
                    self.mouse_sounds = config.get('mouse_sounds', {})
                    self.universal_sound = config.get('universal_sound', '')
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON from config file: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'sounds': self.sounds, 'mouse_sounds': self.mouse_sounds, 'universal_sound': self.universal_sound}, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def assign_sound(self, key_name, sound_path, is_mouse=False):
        if is_mouse:
            self.mouse_sounds[key_name] = sound_path
        else:
            self.sounds[key_name] = sound_path
        self.save_config()

    def get_sound(self, key_name, is_mouse=False):
        if is_mouse:
            return self.mouse_sounds.get(key_name, '')
        return self.sounds.get(key_name, self.universal_sound)

class SoundPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Sound Bind')
        self.sound_manager = SoundManager()
        self.setup_ui()
        self.start_listening()

    def setup_ui(self):
        tk.Label(self.root, text='Configure sounds for keys and mouse buttons.').pack(pady=10)
        self.text_area = scrolledtext.ScrolledText(self.root, height=12)
        self.text_area.pack(pady=10)
        self.update_text_area()

        tk.Button(self.root, text='Set Universal Sound', command=self.choose_universal_sound).pack(side=tk.LEFT, padx=5)
        tk.Button(self.root, text='Add Key Sound', command=lambda: self.assign_sound('keyboard')).pack(side=tk.LEFT, padx=5)
        tk.Button(self.root, text='Add Mouse Sound', command=lambda: self.assign_sound('mouse')).pack(side=tk.LEFT, padx=5)
        tk.Button(self.root, text='Clear Sounds', command=self.clear_sounds).pack(side=tk.LEFT, padx=5)

    def start_listening(self):
        keyboard_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        mouse_thread = threading.Thread(target=self.mouse_listener, daemon=True)
        keyboard_thread.start()
        mouse_thread.start()

    def keyboard_listener(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

    def mouse_listener(self):
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

    def on_press(self, key):
        try:
            key_name = str(key)
            sound_to_play = self.sound_manager.get_sound(key_name)
            if sound_to_play:
                threading.Thread(target=lambda: playsound(sound_to_play), daemon=True).start()
        except Exception as e:
            logging.error(f"Error playing sound for key press: {e}")

    def on_click(self, x, y, button, pressed):
        try:
            if pressed:
                button_name = str(button)
                sound_to_play = self.sound_manager.get_sound(button_name, is_mouse=True)
                if sound_to_play:
                    threading.Thread(target=lambda: playsound(sound_to_play), daemon=True).start()
        except Exception as e:
            logging.error(f"Error playing sound for mouse click: {e}")

    def choose_universal_sound(self):
        sound = filedialog.askopenfilename(filetypes=[('Audio Files', '*.mp3 *.wav')])
        if sound:
            self.sound_manager.universal_sound = sound
            self.update_text_area()
            self.sound_manager.save_config()

    def assign_sound(self, device_type):
        sound_path = filedialog.askopenfilename(title=f'Select sound for {device_type}', filetypes=[('Audio Files', '*.mp3 *.wav')])
        if sound_path:
            if device_type == 'keyboard':
                messagebox.showinfo('Assign Key Sound', 'Press the key to assign the sound.')
                self.keyboard_listener = keyboard.Listener(on_press=lambda e: self.assign_key_sound(e, sound_path))
                self.keyboard_listener.start()
            elif device_type == 'mouse':
                messagebox.showinfo('Assign Mouse Sound', 'Click the mouse button to assign the sound.')
                self.mouse_listener = mouse.Listener(on_click=lambda x, y, button, pressed: self.assign_mouse_sound(button, sound_path, pressed))
                self.mouse_listener.start()

    def assign_key_sound(self, key, sound_path):
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            key_name = str(key)
            self.sound_manager.assign_sound(key_name, sound_path)
            self.update_text_area()
        except Exception as e:
            logging.error(f"Error assigning sound to key: {e}")

    def assign_mouse_sound(self, button, sound_path, pressed):
        try:
            if pressed:
                if self.mouse_listener:
                    self.mouse_listener.stop()
                button_name = str(button)
                self.sound_manager.assign_sound(button_name, sound_path, is_mouse=True)
                self.update_text_area()
        except Exception as e:
            logging.error(f"Error assigning sound to mouse button: {e}")

    def clear_sounds(self):
        self.sound_manager.sounds.clear()
        self.sound_manager.mouse_sounds.clear()
        self.sound_manager.universal_sound = ''
        self.sound_manager.save_config()
        self.update_text_area()

    def update_text_area(self):
        self.text_area.delete(1.0, tk.END)
        universal_sound = self.sound_manager.universal_sound or 'Not Set'
        self.text_area.insert(tk.END, f'Universal Sound: {universal_sound}\n\n')
        for key, sound in self.sound_manager.sounds.items():
            self.text_area.insert(tk.END, f'{key}: {sound}\n')
        for button, sound in self.sound_manager.mouse_sounds.items():
            self.text_area.insert(tk.END, f'{button}: {sound}\n')

def main():
    root = tk.Tk()
    app = SoundPlayerApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
