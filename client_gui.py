import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import pyaudio
import wave
import os

class VoiceChatClient:
    def __init__(self):
        # Настройки сети
        self.HOST = 'localhost'
        self.TEXT_PORT = 5555
        self.VOICE_PORT = 5556
        
        # Сокеты
        self.text_client = None
        self.voice_client = None
        self.nickname = ""
        
        # Настройки аудио
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.audio = pyaudio.PyAudio()
        
        # Флаги
        self.is_talking = False
        self.is_connected = False
        self.is_testing_mic = False
        
        # GUI
        self.chat_window = None
        self.chat_display = None
        self.status_label = None
        
        self.create_login_window()
    
    def create_login_window(self):
        """Окно входа - ввод никнейма и IP сервера"""
        self.login_window = tk.Tk()
        self.login_window.title("Вход в чат")
        self.login_window.geometry("350x270")
        self.login_window.resizable(False, False)

        # Центрируем окно
        self.center_window(self.login_window, 350, 270)

        tk.Label(self.login_window, text="IP сервера:", font=("Arial", 12)).pack(pady=(15, 0))

        self.ip_entry = tk.Entry(self.login_window, font=("Arial", 12), width=20)
        self.ip_entry.insert(0, "localhost")
        self.ip_entry.pack(pady=5)

        tk.Label(self.login_window, text="Никнейм:", font=("Arial", 12)).pack(pady=(10, 0))

        self.nickname_entry = tk.Entry(self.login_window, font=("Arial", 12), width=20)
        self.nickname_entry.pack(pady=5)
        self.nickname_entry.bind('<Return>', lambda e: self.connect_to_server())
        self.nickname_entry.focus()

        tk.Button(self.login_window, text="Подключиться", command=self.connect_to_server,
                 bg="#4CAF50", fg="white", font=("Arial", 10), width=15).pack(pady=5)

        # Кнопка проверки микрофона ДО подключения
        tk.Button(self.login_window, text="🎤 Проверить микрофон", command=self.test_microphone,
                 bg="#FF9800", fg="white", font=("Arial", 10), width=20).pack(pady=5)

        self.login_window.mainloop()
    
    def center_window(self, window, width, height):
        """Центрирует окно на экране"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def test_microphone(self):
        """Тест микрофона - запись 3 сек и воспроизведение"""
        if self.is_testing_mic:
            return
        
        self.is_testing_mic = True
        
        def record_and_play():
            try:
                messagebox.showinfo("Тест микрофона", "Сейчас будет запись 3 секунды.\nГоворите что-нибудь!\n\nНажмите OK для начала.")
                
                # Запись
                stream = self.audio.open(format=self.FORMAT,
                                        channels=self.CHANNELS,
                                        rate=self.RATE,
                                        input=True,
                                        frames_per_buffer=self.CHUNK)
                
                frames = []
                for _ in range(0, int(self.RATE / self.CHUNK * 3)):  # 3 секунды
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
                messagebox.showinfo("Тест микрофона", "Запись завершена!\n\nСейчас воспроизведу что записал.\n\nНажмите OK.")
                
                # Воспроизведение
                stream = self.audio.open(format=self.FORMAT,
                                        channels=self.CHANNELS,
                                        rate=self.RATE,
                                        output=True)
                
                for frame in frames:
                    stream.write(frame)
                
                stream.stop_stream()
                stream.close()
                
                messagebox.showinfo("Тест микрофона", "✅ Тест завершен!\n\nЕсли вы услышали свой голос - микрофон работает!")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при тесте микрофона:\n{e}")
            finally:
                self.is_testing_mic = False
        
        # Запускаем в отдельном потоке чтобы не блокировать GUI
        test_thread = threading.Thread(target=record_and_play)
        test_thread.daemon = True
        test_thread.start()
    
    def connect_to_server(self):
        """Подключение к серверу"""
        self.HOST = self.ip_entry.get().strip()
        self.nickname = self.nickname_entry.get().strip()

        if not self.HOST:
            messagebox.showerror("Ошибка", "Введите IP сервера!")
            return

        if not self.nickname:
            messagebox.showerror("Ошибка", "Введите никнейм!")
            return
        
        try:
            # Подключаемся к текстовому серверу
            self.text_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.text_client.connect((self.HOST, self.TEXT_PORT))
            
            # Подключаемся к голосовому серверу
            self.voice_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.voice_client.connect((self.HOST, self.VOICE_PORT))
            
            self.is_connected = True
            
            # Закрываем окно входа и открываем главное окно
            self.login_window.destroy()
            self.create_chat_window()
            
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к серверу:\n{e}\n\nУбедитесь что сервер запущен!")
    
    def create_chat_window(self):
        """Главное окно чата"""
        self.chat_window = tk.Tk()
        self.chat_window.title(f"Voice Chat - {self.nickname}")
        self.chat_window.geometry("600x550")
        
        # Центрируем окно
        self.center_window(self.chat_window, 600, 550)
        
        # НОВОЕ: Статус бар сверху
        status_frame = tk.Frame(self.chat_window, bg="#2196F3", height=30)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="🟢 Подключено", 
                                     bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)
        
        # Область сообщений
        self.chat_display = scrolledtext.ScrolledText(self.chat_window, wrap=tk.WORD, 
                                                       state='disabled', font=("Arial", 10),
                                                       bg="#ffffff", fg="#000000")
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # НОВОЕ: Цветовые теги для разных типов сообщений
        self.chat_display.tag_config("own_message", foreground="#1976D2", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("other_message", foreground="#000000")
        self.chat_display.tag_config("system_message", foreground="#4CAF50", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("error_message", foreground="#F44336", font=("Arial", 9, "italic"))
        
        # Фрейм для ввода
        input_frame = tk.Frame(self.chat_window)
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Поле ввода сообщения
        self.message_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.message_entry.focus()
        
        # Кнопка отправки
        send_btn = tk.Button(input_frame, text="Отправить", command=self.send_message,
                            bg="#2196F3", fg="white", font=("Arial", 10), width=10)
        send_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка Push-to-Talk
        self.ptt_button = tk.Button(self.chat_window, text="🎤 Удерживайте для голоса",
                                    font=("Arial", 12, "bold"), bg="#FF5722", fg="white",
                                    activebackground="#E64A19", height=2)
        self.ptt_button.pack(padx=10, pady=(0, 5), fill=tk.X)
        self.ptt_button.bind('<ButtonPress-1>', self.start_talking)
        self.ptt_button.bind('<ButtonRelease-1>', self.stop_talking)
        
        # НОВОЕ: Кнопка проверки микрофона в главном окне
        test_mic_btn = tk.Button(self.chat_window, text="🔊 Проверить микрофон",
                                command=self.test_microphone_in_chat,
                                bg="#FF9800", fg="white", font=("Arial", 9))
        test_mic_btn.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Обработка закрытия окна
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Показываем приветствие
        self.display_message("🎉 Добро пожаловать в чат!", "system")
        self.display_message("💡 Команды: /users, /help", "system")

        # Запускаем потоки приёма ПЕРЕД mainloop
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        voice_receive_thread = threading.Thread(target=self.receive_voice)
        voice_receive_thread.daemon = True
        voice_receive_thread.start()

        self.chat_window.mainloop()
    
    def test_microphone_in_chat(self):
        """Тест микрофона прямо в чате"""
        if self.is_testing_mic:
            return
        
        self.is_testing_mic = True
        self.display_message("🎤 Начинаю тест микрофона... Говорите 3 секунды!", "system")
        
        def record_and_play():
            try:
                # Запись
                stream = self.audio.open(format=self.FORMAT,
                                        channels=self.CHANNELS,
                                        rate=self.RATE,
                                        input=True,
                                        frames_per_buffer=self.CHUNK)
                
                frames = []
                for _ in range(0, int(self.RATE / self.CHUNK * 3)):  # 3 секунды
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
                self.display_message("✅ Запись завершена! Воспроизвожу...", "system")
                
                # Воспроизведение
                stream = self.audio.open(format=self.FORMAT,
                                        channels=self.CHANNELS,
                                        rate=self.RATE,
                                        output=True)
                
                for frame in frames:
                    stream.write(frame)
                
                stream.stop_stream()
                stream.close()
                
                self.display_message("✅ Тест завершен! Если услышали себя - микрофон работает!", "system")
                
            except Exception as e:
                self.display_message(f"❌ Ошибка теста: {e}", "error")
            finally:
                self.is_testing_mic = False
        
        test_thread = threading.Thread(target=record_and_play)
        test_thread.daemon = True
        test_thread.start()
    
    def display_message(self, message, msg_type="other"):
        """Отображает сообщение в чате с цветом (потокобезопасно)"""
        def _update():
            if self.chat_display:
                self.chat_display.config(state='normal')

                # Выбираем тег в зависимости от типа
                if msg_type == "own":
                    tag = "own_message"
                elif msg_type == "system":
                    tag = "system_message"
                elif msg_type == "error":
                    tag = "error_message"
                else:
                    tag = "other_message"

                self.chat_display.insert(tk.END, message + '\n', tag)
                self.chat_display.see(tk.END)
                self.chat_display.config(state='disabled')

        if self.chat_window:
            self.chat_window.after(0, _update)
    
    def send_message(self):
        """Отправка текстового сообщения"""
        message = self.message_entry.get().strip()
        
        if message:
            try:
                self.text_client.send(message.encode('utf-8'))
                # НОВОЕ: Показываем своё сообщение
                self.display_message(f"[Вы]: {message}", "own")
                self.message_entry.delete(0, tk.END)
            except:
                self.display_message("⚠️ Не удалось отправить сообщение", "error")
    
    def receive_messages(self):
        """Получение текстовых сообщений от сервера"""
        while self.is_connected:
            try:
                message = self.text_client.recv(1024).decode('utf-8')
                
                if message == "NICK":
                    self.text_client.send(self.nickname.encode('utf-8'))
                elif message == "NICK_TAKEN":
                    self.display_message("❌ Этот никнейм уже занят!", "error")
                    self.is_connected = False
                    break
                else:
                    # НОВОЕ: Системные сообщения отображаются по-другому
                    if message.startswith('✅') or message.startswith('❌') or message.startswith('👥') or message.startswith('📋'):
                        self.display_message(message, "system")
                    else:
                        self.display_message(message, "other")
                    
            except:
                if self.is_connected:
                    self.display_message("⚠️ Потеряно соединение с сервером", "error")
                    self.update_status("🔴 Отключено", "#F44336")
                self.is_connected = False
                break
    
    def update_status(self, text, color):
        """Обновляет статус бар (потокобезопасно)"""
        def _update():
            if self.status_label:
                self.status_label.config(text=text, bg=color)

        if self.chat_window:
            self.chat_window.after(0, _update)
    
    def start_talking(self, event):
        """Начать передачу голоса"""
        if not self.is_talking:
            self.is_talking = True
            self.ptt_button.config(text="🔴 ГОВОРИТЕ...", bg="#4CAF50")
            self.update_status("🎤 Вы говорите", "#4CAF50")
            
            # Запускаем поток для передачи голоса
            talk_thread = threading.Thread(target=self.send_voice)
            talk_thread.daemon = True
            talk_thread.start()
    
    def stop_talking(self, event):
        """Остановить передачу голоса"""
        self.is_talking = False
        self.ptt_button.config(text="🎤 Удерживайте для голоса", bg="#FF5722")
        self.update_status("🟢 Подключено", "#2196F3")
    
    def send_voice(self):
        """Отправка голосовых данных"""
        try:
            stream = self.audio.open(format=self.FORMAT,
                                    channels=self.CHANNELS,
                                    rate=self.RATE,
                                    input=True,
                                    frames_per_buffer=self.CHUNK)
            
            while self.is_talking:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.voice_client.send(data)
                except:
                    break
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.display_message(f"⚠️ Ошибка микрофона: {e}", "error")
    
    def receive_voice(self):
        """Получение и воспроизведение голоса"""
        try:
            stream = self.audio.open(format=self.FORMAT,
                                    channels=self.CHANNELS,
                                    rate=self.RATE,
                                    output=True,
                                    frames_per_buffer=self.CHUNK)
            
            while self.is_connected:
                try:
                    data = self.voice_client.recv(4096)
                    if data:
                        stream.write(data)
                        # НОВОЕ: Показываем что кто-то говорит
                        if not self.is_talking:
                            self.update_status("🔊 Кто-то говорит", "#9C27B0")
                            # Через секунду возвращаем статус обратно
                            threading.Timer(1.0, lambda: self.update_status("🟢 Подключено", "#2196F3") if not self.is_talking else None).start()
                except:
                    break
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.display_message(f"⚠️ Ошибка аудио: {e}", "error")
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.is_connected = False
        self.is_talking = False
        
        if self.text_client:
            try:
                self.text_client.close()
            except:
                pass
        
        if self.voice_client:
            try:
                self.voice_client.close()
            except:
                pass
        
        self.audio.terminate()
        
        if self.chat_window:
            self.chat_window.destroy()

if __name__ == "__main__":
    client = VoiceChatClient()