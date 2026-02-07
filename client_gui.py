import socket
import threading
import struct
import time
import ctypes
import tkinter as tk
from tkinter import scrolledtext, messagebox
import pyaudio

# Discord-style цвета
BG_DARK = "#202225"
BG_MAIN = "#36393f"
BG_SIDEBAR = "#2f3136"
BG_INPUT = "#40444b"
BG_HOVER = "#4f545c"
TEXT_NORMAL = "#dcddde"
TEXT_BRIGHT = "#ffffff"
TEXT_MUTED = "#72767d"
ACCENT = "#7289da"
GREEN = "#43b581"
RED = "#f04747"
YELLOW = "#faa61a"


class VoiceChatClient:
    def __init__(self):
        self.HOST = 'localhost'
        self.TEXT_PORT = 5555
        self.VOICE_PORT = 5556

        self.text_client = None
        self.voice_client = None
        self.nickname = ""

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.audio = pyaudio.PyAudio()

        self.is_talking = False
        self.is_connected = False
        self.is_testing_mic = False
        self.voice_mode = "ptt"
        self.va_active = False
        self.va_running = False

        self.input_devices = []
        self.output_devices = []
        self.selected_input = None
        self.selected_output = None
        self.volume = 100
        self.user_volumes = {}  # {nickname: volume 0-200}

        self.online_users = []
        self.speaking_users = set()
        self.user_labels = {}

        self.last_typing_sent = 0
        self.typing_label = None
        self.recv_buffer = ""

        self.chat_window = None
        self.chat_display = None
        self.status_label = None

        self._enumerate_devices()
        self.create_login_window()

    # ==================== УСТРОЙСТВА ====================

    def _get_winmm_names(self):
        """Получает правильные Unicode-имена устройств через Windows MME API"""
        input_names = {}
        output_names = {}
        try:
            winmm = ctypes.windll.winmm

            class WAVEINCAPSW(ctypes.Structure):
                _fields_ = [
                    ('wMid', ctypes.c_ushort),
                    ('wPid', ctypes.c_ushort),
                    ('vDriverVersion', ctypes.c_uint),
                    ('szPname', ctypes.c_wchar * 32),
                    ('dwFormats', ctypes.c_uint),
                    ('wChannels', ctypes.c_ushort),
                    ('wReserved1', ctypes.c_ushort),
                ]

            class WAVEOUTCAPSW(ctypes.Structure):
                _fields_ = [
                    ('wMid', ctypes.c_ushort),
                    ('wPid', ctypes.c_ushort),
                    ('vDriverVersion', ctypes.c_uint),
                    ('szPname', ctypes.c_wchar * 32),
                    ('dwFormats', ctypes.c_uint),
                    ('wChannels', ctypes.c_ushort),
                    ('wReserved1', ctypes.c_ushort),
                    ('dwSupport', ctypes.c_uint),
                ]

            for i in range(winmm.waveInGetNumDevs()):
                caps = WAVEINCAPSW()
                if winmm.waveInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    input_names[i] = caps.szPname

            for i in range(winmm.waveOutGetNumDevs()):
                caps = WAVEOUTCAPSW()
                if winmm.waveOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    output_names[i] = caps.szPname
        except Exception:
            pass
        return input_names, output_names

    def _enumerate_devices(self):
        """Получает список аудиоустройств с правильными Unicode-именами"""
        self.input_devices = []
        self.output_devices = []

        win_in, win_out = self._get_winmm_names()

        try:
            default_host = self.audio.get_default_host_api_info()['index']
        except Exception:
            default_host = 0

        try:
            host_info = self.audio.get_host_api_info_by_index(default_host)
        except Exception:
            return

        seen_input = set()
        seen_output = set()
        mme_in_idx = 0
        mme_out_idx = 0

        for local_idx in range(host_info['deviceCount']):
            try:
                info = self.audio.get_device_info_by_host_api_device_index(default_host, local_idx)
                global_idx = info['index']

                if info['maxInputChannels'] > 0:
                    name = win_in.get(mme_in_idx, info['name'])
                    mme_in_idx += 1
                    if name not in seen_input:
                        self.input_devices.append((global_idx, name))
                        seen_input.add(name)

                if info['maxOutputChannels'] > 0:
                    name = win_out.get(mme_out_idx, info['name'])
                    mme_out_idx += 1
                    if name not in seen_output:
                        self.output_devices.append((global_idx, name))
                        seen_output.add(name)
            except Exception:
                pass

        if self.input_devices:
            self.selected_input = self.input_devices[0][0]
        if self.output_devices:
            self.selected_output = self.output_devices[0][0]

    # ==================== ОКНО ВХОДА ====================

    def create_login_window(self):
        self.login_window = tk.Tk()
        self.login_window.title("HYBRID - Вход")
        self.login_window.geometry("380x300")
        self.login_window.resizable(False, False)
        self.login_window.configure(bg=BG_DARK)
        self.center_window(self.login_window, 380, 300)

        tk.Label(self.login_window, text="HYBRID", font=("Arial", 20, "bold"),
                 bg=BG_DARK, fg=ACCENT).pack(pady=(20, 5))
        tk.Label(self.login_window, text="Голосовой чат", font=("Arial", 10),
                 bg=BG_DARK, fg=TEXT_MUTED).pack()

        tk.Label(self.login_window, text="IP сервера", font=("Arial", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_NORMAL, anchor='w').pack(padx=40, pady=(15, 2), fill='x')
        self.ip_entry = tk.Entry(self.login_window, font=("Arial", 11),
                                 bg=BG_INPUT, fg=TEXT_BRIGHT, insertbackground=TEXT_BRIGHT,
                                 relief='flat', bd=5)
        self.ip_entry.insert(0, "95.37.140.186")
        self.ip_entry.pack(padx=40, fill='x')

        tk.Label(self.login_window, text="Никнейм", font=("Arial", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_NORMAL, anchor='w').pack(padx=40, pady=(10, 2), fill='x')
        self.nickname_entry = tk.Entry(self.login_window, font=("Arial", 11),
                                       bg=BG_INPUT, fg=TEXT_BRIGHT, insertbackground=TEXT_BRIGHT,
                                       relief='flat', bd=5)
        self.nickname_entry.pack(padx=40, fill='x')
        self.nickname_entry.bind('<Return>', lambda e: self.connect_to_server())
        self.nickname_entry.focus()

        btn_frame = tk.Frame(self.login_window, bg=BG_DARK)
        btn_frame.pack(padx=40, pady=15, fill='x')

        tk.Button(btn_frame, text="Подключиться", command=self.connect_to_server,
                  bg=ACCENT, fg=TEXT_BRIGHT, font=("Arial", 10, "bold"),
                  relief='flat', bd=0, padx=15, pady=5,
                  activebackground="#677bc4", activeforeground=TEXT_BRIGHT).pack(side='left')

        tk.Button(btn_frame, text="Тест микрофона", command=self.test_microphone,
                  bg=BG_INPUT, fg=TEXT_NORMAL, font=("Arial", 10),
                  relief='flat', bd=0, padx=15, pady=5,
                  activebackground=BG_HOVER, activeforeground=TEXT_BRIGHT).pack(side='right')

        self.login_window.mainloop()

    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    # ==================== ПОДКЛЮЧЕНИЕ ====================

    def connect_to_server(self):
        self.HOST = self.ip_entry.get().strip()
        self.nickname = self.nickname_entry.get().strip()

        if not self.HOST:
            messagebox.showerror("Ошибка", "Введите IP сервера!")
            return
        if not self.nickname:
            messagebox.showerror("Ошибка", "Введите никнейм!")
            return

        try:
            self.text_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.text_client.connect((self.HOST, self.TEXT_PORT))

            self.voice_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.voice_client.connect((self.HOST, self.VOICE_PORT))
            self.voice_client.send(self.nickname.encode('utf-8'))

            self.is_connected = True
            self.login_window.destroy()
            self.create_chat_window()

        except Exception as e:
            messagebox.showerror("Ошибка подключения",
                                 f"Не удалось подключиться:\n{e}\n\nУбедитесь что сервер запущен!")

    # ==================== ГЛАВНОЕ ОКНО ====================

    def create_chat_window(self):
        self.chat_window = tk.Tk()
        self.chat_window.title(f"HYBRID - {self.nickname}")
        self.chat_window.geometry("850x600")
        self.chat_window.configure(bg=BG_DARK)
        self.chat_window.minsize(700, 500)
        self.center_window(self.chat_window, 850, 600)

        # ---- Верхняя панель ----
        top_bar = tk.Frame(self.chat_window, bg=BG_DARK, height=35)
        top_bar.pack(fill='x')
        top_bar.pack_propagate(False)

        tk.Label(top_bar, text="# голосовой-чат", font=("Arial", 12, "bold"),
                 bg=BG_DARK, fg=TEXT_BRIGHT).pack(side='left', padx=15, pady=5)

        self.status_label = tk.Label(top_bar, text="Подключено", font=("Arial", 9),
                                     bg=BG_DARK, fg=GREEN)
        self.status_label.pack(side='right', padx=15)

        # Шестерёнка настроек
        settings_btn = tk.Button(top_bar, text="\u2699", font=("Arial", 14),
                                  bg=BG_DARK, fg=TEXT_MUTED, relief='flat', bd=0,
                                  command=self.open_settings,
                                  activebackground=BG_DARK, activeforeground=TEXT_BRIGHT)
        settings_btn.pack(side='right', padx=5)

        tk.Frame(self.chat_window, bg=BG_HOVER, height=1).pack(fill='x')

        # ---- Основная область ----
        main_frame = tk.Frame(self.chat_window, bg=BG_MAIN)
        main_frame.pack(fill='both', expand=True)

        # Sidebar
        self.sidebar = tk.Frame(main_frame, bg=BG_SIDEBAR, width=180)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        self.users_header = tk.Label(self.sidebar, text="ОНЛАЙН — 0",
                                     font=("Arial", 9, "bold"), bg=BG_SIDEBAR, fg=TEXT_MUTED, anchor='w')
        self.users_header.pack(padx=12, pady=(12, 5), fill='x')

        self.users_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        self.users_frame.pack(fill='both', expand=True, padx=8)

        tk.Frame(main_frame, bg=BG_HOVER, width=1).pack(side='left', fill='y')

        # Чат
        chat_area = tk.Frame(main_frame, bg=BG_MAIN)
        chat_area.pack(side='left', fill='both', expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_area, wrap='word', state='disabled',
            font=("Consolas", 10), bg=BG_MAIN, fg=TEXT_NORMAL,
            relief='flat', bd=0, padx=15, pady=10,
            insertbackground=TEXT_BRIGHT, selectbackground=ACCENT
        )
        self.chat_display.pack(fill='both', expand=True)
        self.chat_display.vbar.configure(bg=BG_DARK, troughcolor=BG_MAIN,
                                          activebackground=BG_HOVER, relief='flat', width=8)

        self.chat_display.tag_config("own_msg", foreground=ACCENT, font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("other_msg", foreground=TEXT_NORMAL)
        self.chat_display.tag_config("system_msg", foreground=GREEN, font=("Consolas", 9, "italic"))
        self.chat_display.tag_config("error_msg", foreground=RED, font=("Consolas", 9, "italic"))

        # Typing
        self.typing_label = tk.Label(chat_area, text="", font=("Arial", 9, "italic"),
                                      bg=BG_MAIN, fg=TEXT_MUTED, anchor='w')
        self.typing_label.pack(fill='x', padx=15)

        # Быстрые команды
        cmd_frame = tk.Frame(chat_area, bg=BG_MAIN)
        cmd_frame.pack(fill='x', padx=10, pady=(0, 2))

        for text, cmd in [("Онлайн", self._cmd_users), ("Тест микро", self.test_microphone_in_chat),
                          ("Отключиться", self.on_closing)]:
            btn = tk.Button(cmd_frame, text=text, command=cmd,
                            bg=BG_INPUT, fg=TEXT_MUTED, font=("Arial", 8),
                            relief='flat', bd=0, padx=8, pady=2,
                            activebackground=BG_HOVER, activeforeground=TEXT_BRIGHT)
            btn.pack(side='left', padx=2)

        # Поле ввода
        input_frame = tk.Frame(chat_area, bg=BG_INPUT, bd=0)
        input_frame.pack(fill='x', padx=10, pady=(0, 8))

        self.message_entry = tk.Entry(input_frame, font=("Arial", 11),
                                       bg=BG_INPUT, fg=TEXT_BRIGHT, insertbackground=TEXT_BRIGHT,
                                       relief='flat', bd=8)
        self.message_entry.pack(side='left', fill='x', expand=True)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.message_entry.bind('<Key>', self._on_key_press)
        self.message_entry.focus()

        send_btn = tk.Button(input_frame, text="Отправить", command=self.send_message,
                             bg=ACCENT, fg=TEXT_BRIGHT, font=("Arial", 9, "bold"),
                             relief='flat', bd=0, padx=12, pady=6,
                             activebackground="#677bc4")
        send_btn.pack(side='right', padx=(0, 5), pady=3)

        # ---- Нижняя панель (голос) ----
        bottom_panel = tk.Frame(self.chat_window, bg=BG_DARK, height=45)
        bottom_panel.pack(fill='x')
        bottom_panel.pack_propagate(False)

        tk.Frame(self.chat_window, bg=BG_HOVER, height=1).pack(fill='x', before=bottom_panel)

        row = tk.Frame(bottom_panel, bg=BG_DARK)
        row.pack(fill='x', padx=10, pady=8)

        self.ptt_button = tk.Button(row, text="Нажми для голоса",
                                     font=("Arial", 10, "bold"), bg=RED, fg=TEXT_BRIGHT,
                                     activebackground="#d84040", relief='flat', bd=0, padx=12, pady=4)
        self.ptt_button.pack(side='left')
        self.ptt_button.bind('<ButtonPress-1>', self.start_talking)
        self.ptt_button.bind('<ButtonRelease-1>', self.stop_talking)

        self.mode_btn = tk.Button(row, text="PTT", command=self.toggle_voice_mode,
                                   bg=BG_INPUT, fg=TEXT_NORMAL, font=("Arial", 9),
                                   relief='flat', bd=0, padx=10, pady=4,
                                   activebackground=BG_HOVER)
        self.mode_btn.pack(side='left', padx=5)

        tk.Label(row, text="Громкость:", font=("Arial", 9),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(side='left', padx=(10, 0))

        self.volume_slider = tk.Scale(row, from_=0, to=200, orient='horizontal',
                                       bg=BG_DARK, fg=TEXT_NORMAL, troughcolor=BG_INPUT,
                                       highlightthickness=0, sliderrelief='flat',
                                       length=120, showvalue=True, font=("Arial", 8),
                                       activebackground=ACCENT, command=self._change_volume)
        self.volume_slider.set(100)
        self.volume_slider.pack(side='left', padx=5)

        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.display_message("Добро пожаловать в HYBRID!", "system")

        threading.Thread(target=self.receive_messages, daemon=True).start()
        threading.Thread(target=self.receive_voice, daemon=True).start()

        self.chat_window.mainloop()

    # ==================== НАСТРОЙКИ (POPUP) ====================

    def open_settings(self):
        """Открывает окно настроек аудиоустройств"""
        win = tk.Toplevel(self.chat_window)
        win.title("Настройки")
        win.geometry("420x300")
        win.configure(bg=BG_DARK)
        win.resizable(False, False)
        self.center_window(win, 420, 300)
        win.transient(self.chat_window)
        win.grab_set()

        tk.Label(win, text="Настройки аудио", font=("Arial", 14, "bold"),
                 bg=BG_DARK, fg=TEXT_BRIGHT).pack(pady=(15, 10))

        # Микрофон
        tk.Label(win, text="Микрофон (ввод)", font=("Arial", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_NORMAL, anchor='w').pack(padx=20, fill='x')

        input_var = tk.StringVar()
        input_names = [d[1] for d in self.input_devices] if self.input_devices else ["Нет устройств"]
        # Найти текущий
        current_input = input_names[0]
        for idx, name in self.input_devices:
            if idx == self.selected_input:
                current_input = name
                break
        input_var.set(current_input)

        input_menu = tk.OptionMenu(win, input_var, *input_names)
        input_menu.configure(bg=BG_INPUT, fg=TEXT_BRIGHT, font=("Arial", 9),
                             relief='flat', bd=0, highlightthickness=0, width=40,
                             activebackground=BG_HOVER, activeforeground=TEXT_BRIGHT)
        input_menu["menu"].configure(bg=BG_INPUT, fg=TEXT_BRIGHT, activebackground=ACCENT)
        input_menu.pack(padx=20, pady=(2, 10), fill='x')

        # Динамики
        tk.Label(win, text="Динамики (вывод)", font=("Arial", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_NORMAL, anchor='w').pack(padx=20, fill='x')

        output_var = tk.StringVar()
        output_names = [d[1] for d in self.output_devices] if self.output_devices else ["Нет устройств"]
        current_output = output_names[0]
        for idx, name in self.output_devices:
            if idx == self.selected_output:
                current_output = name
                break
        output_var.set(current_output)

        output_menu = tk.OptionMenu(win, output_var, *output_names)
        output_menu.configure(bg=BG_INPUT, fg=TEXT_BRIGHT, font=("Arial", 9),
                              relief='flat', bd=0, highlightthickness=0, width=40,
                              activebackground=BG_HOVER, activeforeground=TEXT_BRIGHT)
        output_menu["menu"].configure(bg=BG_INPUT, fg=TEXT_BRIGHT, activebackground=ACCENT)
        output_menu.pack(padx=20, pady=(2, 10), fill='x')

        # Кнопки
        btn_frame = tk.Frame(win, bg=BG_DARK)
        btn_frame.pack(padx=20, pady=10, fill='x')

        def apply_and_close():
            for idx, name in self.input_devices:
                if name == input_var.get():
                    self.selected_input = idx
                    break
            for idx, name in self.output_devices:
                if name == output_var.get():
                    self.selected_output = idx
                    break
            win.destroy()

        tk.Button(btn_frame, text="Применить", command=apply_and_close,
                  bg=ACCENT, fg=TEXT_BRIGHT, font=("Arial", 10, "bold"),
                  relief='flat', bd=0, padx=15, pady=5,
                  activebackground="#677bc4").pack(side='left')

        tk.Button(btn_frame, text="Тест микрофона", command=self.test_microphone_in_chat,
                  bg=BG_INPUT, fg=TEXT_NORMAL, font=("Arial", 10),
                  relief='flat', bd=0, padx=15, pady=5,
                  activebackground=BG_HOVER).pack(side='right')

    # ==================== СПИСОК ПОЛЬЗОВАТЕЛЕЙ ====================

    def update_user_list(self, users):
        self.online_users = users
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        self.user_labels.clear()

        self.users_header.config(text=f"ОНЛАЙН — {len(users)}")

        for user in users:
            frame = tk.Frame(self.users_frame, bg=BG_SIDEBAR)
            frame.pack(fill='x', pady=1)

            color = GREEN if user in self.speaking_users else TEXT_MUTED
            dot = tk.Label(frame, text="\u25CF", font=("Arial", 10), bg=BG_SIDEBAR, fg=color)
            dot.pack(side='left', padx=(4, 6))

            name_label = tk.Label(frame, text=user, font=("Arial", 10), bg=BG_SIDEBAR,
                                   fg=TEXT_BRIGHT if user == self.nickname else TEXT_NORMAL, anchor='w')
            name_label.pack(side='left', fill='x')

            self.user_labels[user] = (dot, name_label, frame)

            # Правый клик
            for widget in (frame, dot, name_label):
                widget.bind('<Button-3>', lambda e, u=user: self._user_right_click(e, u))

    def _user_right_click(self, event, username):
        """Контекстное меню при правом клике на пользователе"""
        menu = tk.Menu(self.chat_window, tearoff=0, bg=BG_INPUT, fg=TEXT_BRIGHT,
                       activebackground=ACCENT, activeforeground=TEXT_BRIGHT,
                       font=("Arial", 10))
        menu.add_command(label=f"Громкость: {username}", command=lambda: self._open_user_volume(username))

        current_vol = self.user_volumes.get(username, 100)
        menu.add_separator()
        menu.add_command(label=f"Текущая: {current_vol}%", state='disabled')

        menu.tk_popup(event.x_root, event.y_root)

    def _open_user_volume(self, username):
        """Окно регулировки громкости пользователя"""
        win = tk.Toplevel(self.chat_window)
        win.title(f"Громкость: {username}")
        win.geometry("300x120")
        win.configure(bg=BG_DARK)
        win.resizable(False, False)
        self.center_window(win, 300, 120)
        win.transient(self.chat_window)

        tk.Label(win, text=f"Громкость: {username}", font=("Arial", 11, "bold"),
                 bg=BG_DARK, fg=TEXT_BRIGHT).pack(pady=(15, 5))

        current = self.user_volumes.get(username, 100)

        slider = tk.Scale(win, from_=0, to=200, orient='horizontal',
                          bg=BG_DARK, fg=TEXT_NORMAL, troughcolor=BG_INPUT,
                          highlightthickness=0, sliderrelief='flat',
                          length=250, showvalue=True, font=("Arial", 9),
                          activebackground=ACCENT,
                          command=lambda v, u=username: self._set_user_volume(u, int(v)))
        slider.set(current)
        slider.pack(padx=20, pady=5)

    def _set_user_volume(self, username, value):
        self.user_volumes[username] = value

    def highlight_speaking(self, nickname):
        self.speaking_users.add(nickname)
        if nickname in self.user_labels:
            dot, name_label, frame = self.user_labels[nickname]
            dot.config(fg=GREEN)
            frame.config(bg="#2d3d2f")
            dot.config(bg="#2d3d2f")
            name_label.config(bg="#2d3d2f")

        def remove():
            self.speaking_users.discard(nickname)
            if nickname in self.user_labels:
                dot, name_label, frame = self.user_labels[nickname]
                dot.config(fg=TEXT_MUTED, bg=BG_SIDEBAR)
                frame.config(bg=BG_SIDEBAR)
                name_label.config(bg=BG_SIDEBAR)

        if self.chat_window:
            self.chat_window.after(500, remove)

    # ==================== СООБЩЕНИЯ ====================

    def display_message(self, message, msg_type="other"):
        def _update():
            if not self.chat_display:
                return
            self.chat_display.config(state='normal')
            tag = {"own": "own_msg", "system": "system_msg", "error": "error_msg"}.get(msg_type, "other_msg")
            self.chat_display.insert('end', message + '\n', tag)
            self.chat_display.see('end')
            self.chat_display.config(state='disabled')

        if self.chat_window:
            self.chat_window.after(0, _update)

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            try:
                self.text_client.send((message + "\n").encode('utf-8'))
                self.display_message(f"[Вы]: {message}", "own")
                self.message_entry.delete(0, 'end')
            except:
                self.display_message("Не удалось отправить сообщение", "error")

    def _cmd_users(self):
        try:
            self.text_client.send("/users\n".encode('utf-8'))
        except:
            pass

    def _on_key_press(self, event):
        now = time.time()
        if now - self.last_typing_sent > 2:
            self.last_typing_sent = now
            try:
                self.text_client.send("TYPING\n".encode('utf-8'))
            except:
                pass

    def show_typing(self, nickname):
        def _update():
            if self.typing_label:
                self.typing_label.config(text=f"{nickname} печатает...")
        def _clear():
            if self.typing_label:
                self.typing_label.config(text="")
        if self.chat_window:
            self.chat_window.after(0, _update)
            self.chat_window.after(3000, _clear)

    def _process_line(self, line):
        """Обрабатывает одну строку от сервера"""
        if line == "NICK":
            self.text_client.send((self.nickname + "\n").encode('utf-8'))
        elif line == "NICK_TAKEN":
            self.display_message("Этот никнейм уже занят!", "error")
            self.is_connected = False
        elif line.startswith("USERLIST:"):
            users = line[9:].split(",") if line[9:] else []
            if self.chat_window:
                self.chat_window.after(0, lambda u=users: self.update_user_list(u))
        elif line.startswith("TYPING:"):
            self.show_typing(line[7:])
        elif line.startswith("[Сервер]"):
            self.display_message(line, "system")
        else:
            self.display_message(line, "other")

    def receive_messages(self):
        while self.is_connected:
            try:
                data = self.text_client.recv(4096).decode('utf-8')
                if not data:
                    break

                self.recv_buffer += data
                while "\n" in self.recv_buffer:
                    line, self.recv_buffer = self.recv_buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._process_line(line)

            except:
                if self.is_connected:
                    self.display_message("Потеряно соединение с сервером", "error")
                    self.update_status("Отключено", RED)
                self.is_connected = False
                break

    # ==================== ГОЛОС ====================

    def toggle_voice_mode(self):
        if self.voice_mode == "ptt":
            self.voice_mode = "voice_activity"
            self.mode_btn.config(text="VA", bg=GREEN)
            self.ptt_button.config(text="Голос. активация ВКЛ", bg=GREEN)
            self.ptt_button.unbind('<ButtonPress-1>')
            self.ptt_button.unbind('<ButtonRelease-1>')
            self.ptt_button.config(command=self.toggle_va)
            self.va_active = True
            self._start_voice_activity()
        else:
            self.voice_mode = "ptt"
            self.va_active = False
            self.va_running = False
            self.mode_btn.config(text="PTT", bg=BG_INPUT)
            self.ptt_button.config(text="Нажми для голоса", bg=RED, command=lambda: None)
            self.ptt_button.bind('<ButtonPress-1>', self.start_talking)
            self.ptt_button.bind('<ButtonRelease-1>', self.stop_talking)

    def toggle_va(self):
        if self.va_active:
            self.va_active = False
            self.va_running = False
            self.ptt_button.config(text="Голос. активация ВЫКЛ", bg=RED)
        else:
            self.va_active = True
            self.ptt_button.config(text="Голос. активация ВКЛ", bg=GREEN)
            self._start_voice_activity()

    def _start_voice_activity(self):
        if self.va_running:
            return
        self.va_running = True

        def va_loop():
            try:
                stream = self.audio.open(
                    format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                    input=True, frames_per_buffer=self.CHUNK,
                    input_device_index=self.selected_input)
                THRESHOLD = 500
                while self.va_active and self.is_connected:
                    try:
                        data = stream.read(self.CHUNK, exception_on_overflow=False)
                        rms = 0
                        for i in range(0, len(data), 2):
                            if i + 1 < len(data):
                                sample = struct.unpack('<h', data[i:i+2])[0]
                                rms += sample * sample
                        rms = (rms / (len(data) / 2)) ** 0.5
                        if rms > THRESHOLD:
                            self.voice_client.send(data)
                            if not self.is_talking:
                                self.is_talking = True
                                self.chat_window.after(0, lambda: self.update_status("Вы говорите", GREEN))
                        else:
                            if self.is_talking:
                                self.is_talking = False
                                self.chat_window.after(0, lambda: self.update_status("Подключено", GREEN))
                    except:
                        break
                stream.stop_stream()
                stream.close()
            except Exception as e:
                self.display_message(f"Ошибка микрофона: {e}", "error")
            finally:
                self.va_running = False
                self.is_talking = False

        threading.Thread(target=va_loop, daemon=True).start()

    def start_talking(self, event):
        if not self.is_talking and self.voice_mode == "ptt":
            self.is_talking = True
            self.ptt_button.config(text="ГОВОРИТЕ...", bg=GREEN)
            self.update_status("Вы говорите", GREEN)
            threading.Thread(target=self.send_voice, daemon=True).start()

    def stop_talking(self, event):
        if self.voice_mode == "ptt":
            self.is_talking = False
            self.ptt_button.config(text="Нажми для голоса", bg=RED)
            self.update_status("Подключено", GREEN)

    def send_voice(self):
        try:
            stream = self.audio.open(
                format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                input=True, frames_per_buffer=self.CHUNK,
                input_device_index=self.selected_input)
            while self.is_talking:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.voice_client.send(data)
                except:
                    break
            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.display_message(f"Ошибка микрофона: {e}", "error")

    def receive_voice(self):
        try:
            stream = self.audio.open(
                format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                output=True, frames_per_buffer=self.CHUNK,
                output_device_index=self.selected_output)

            while self.is_connected:
                try:
                    raw = self.voice_client.recv(8192)
                    if not raw:
                        break
                    if len(raw) < 2:
                        continue
                    nick_len = struct.unpack('>H', raw[:2])[0]
                    if len(raw) < 2 + nick_len:
                        continue
                    sender = raw[2:2+nick_len].decode('utf-8')
                    audio_data = raw[2+nick_len:]

                    if audio_data:
                        # Громкость: per-user > global
                        user_vol = self.user_volumes.get(sender, 100)
                        vol = (self.volume / 100.0) * (user_vol / 100.0)

                        if vol != 1.0:
                            adjusted = bytearray()
                            for i in range(0, len(audio_data) - 1, 2):
                                sample = struct.unpack('<h', audio_data[i:i+2])[0]
                                sample = int(sample * vol)
                                sample = max(-32768, min(32767, sample))
                                adjusted.extend(struct.pack('<h', sample))
                            audio_data = bytes(adjusted)

                        stream.write(audio_data)

                        if self.chat_window and sender:
                            self.chat_window.after(0, lambda s=sender: self.highlight_speaking(s))
                except:
                    break

            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.display_message(f"Ошибка аудио: {e}", "error")

    # ==================== УТИЛИТЫ ====================

    def _change_volume(self, val):
        self.volume = int(val)

    def update_status(self, text, color):
        def _update():
            if self.status_label:
                self.status_label.config(text=text, fg=color)
        if self.chat_window:
            self.chat_window.after(0, _update)

    def test_microphone(self):
        if self.is_testing_mic:
            return
        self.is_testing_mic = True
        def record_and_play():
            try:
                messagebox.showinfo("Тест", "Запись 3 секунды. Говорите!\n\nOK для старта.")
                stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, input=True, frames_per_buffer=self.CHUNK,
                                         input_device_index=self.selected_input)
                frames = [stream.read(self.CHUNK, exception_on_overflow=False)
                          for _ in range(int(self.RATE / self.CHUNK * 3))]
                stream.stop_stream(); stream.close()
                messagebox.showinfo("Тест", "Воспроизвожу...\n\nOK.")
                stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, output=True,
                                         output_device_index=self.selected_output)
                for f in frames: stream.write(f)
                stream.stop_stream(); stream.close()
                messagebox.showinfo("Тест", "Готово! Если слышали себя - работает!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка теста:\n{e}")
            finally:
                self.is_testing_mic = False
        threading.Thread(target=record_and_play, daemon=True).start()

    def test_microphone_in_chat(self):
        if self.is_testing_mic:
            return
        self.is_testing_mic = True
        self.display_message("Тест микрофона... Говорите 3 секунды!", "system")
        def record_and_play():
            try:
                stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, input=True, frames_per_buffer=self.CHUNK,
                                         input_device_index=self.selected_input)
                frames = [stream.read(self.CHUNK, exception_on_overflow=False)
                          for _ in range(int(self.RATE / self.CHUNK * 3))]
                stream.stop_stream(); stream.close()
                self.display_message("Воспроизвожу...", "system")
                stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                         rate=self.RATE, output=True,
                                         output_device_index=self.selected_output)
                for f in frames: stream.write(f)
                stream.stop_stream(); stream.close()
                self.display_message("Тест завершён!", "system")
            except Exception as e:
                self.display_message(f"Ошибка теста: {e}", "error")
            finally:
                self.is_testing_mic = False
        threading.Thread(target=record_and_play, daemon=True).start()

    def on_closing(self):
        self.is_connected = False
        self.is_talking = False
        self.va_active = False
        self.va_running = False
        for sock in (self.text_client, self.voice_client):
            if sock:
                try: sock.close()
                except: pass
        self.audio.terminate()
        if self.chat_window:
            self.chat_window.destroy()


if __name__ == "__main__":
    client = VoiceChatClient()
