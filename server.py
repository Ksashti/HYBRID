import socket
import threading

# Списки для хранения клиентов
clients = []           # Socket объекты
nicknames = []         # Никнеймы
voice_clients = []     # Клиенты для голоса (отдельное соединение)

# Текстовый сервер
text_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
text_server.bind(('localhost', 5555))
text_server.listen()

# Голосовой сервер (отдельный порт)
voice_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
voice_server.bind(('localhost', 5556))
voice_server.listen()

print("🟢 Текстовый сервер запущен на порту 5555")
print("🎤 Голосовой сервер запущен на порту 5556")
print("Ожидание подключений...\n")

# Рассылка текстовых сообщений
def broadcast_text(message, exclude_client=None):
    """Отправляет текстовое сообщение всем клиентам"""
    for client in clients:
        if client != exclude_client:
            try:
                client.send(message.encode('utf-8'))
            except:
                # Если ошибка - удаляем клиента
                remove_client(client)

# Рассылка голоса
def broadcast_voice(voice_data, sender):
    """Отправляет голосовые данные всем кроме отправителя"""
    for client in voice_clients:
        if client != sender:
            try:
                client.send(voice_data)
            except:
                if client in voice_clients:
                    voice_clients.remove(client)

# Удаление клиента
def remove_client(client):
    """Удаляет клиента из системы"""
    if client in clients:
        index = clients.index(client)
        nickname = nicknames[index]
        clients.remove(client)
        nicknames.remove(nickname)
        client.close()
        broadcast_text(f"❌ {nickname} покинул чат")
        print(f"❌ {nickname} отключился")

# Обработка текстовых сообщений
def handle_text_client(client):
    """Обрабатывает текстовые сообщения от клиента"""
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            
            if not message:
                remove_client(client)
                break
            
            # Получаем никнейм отправителя
            index = clients.index(client)
            nickname = nicknames[index]
            
            # Обработка команд
            if message.startswith('/'):
                if message == '/users':
                    users_list = ', '.join(nicknames)
                    client.send(f"👥 Онлайн: {users_list}".encode('utf-8'))
                elif message == '/help':
                    help_text = "📋 Команды:\n/users - список пользователей\n/help - эта справка"
                    client.send(help_text.encode('utf-8'))
                else:
                    client.send("❌ Неизвестная команда. Используйте /help".encode('utf-8'))
            else:
                # Обычное сообщение - рассылаем всем
                formatted_message = f"[{nickname}]: {message}"
                broadcast_text(formatted_message)
                print(f"📩 {formatted_message}")
            
        except:
            remove_client(client)
            break

# Обработка голосовых данных
def handle_voice_client(voice_client):
    """Обрабатывает голосовые данные от клиента"""
    while True:
        try:
            voice_data = voice_client.recv(4096)  # Больший буфер для аудио
            if voice_data:
                broadcast_voice(voice_data, voice_client)
        except:
            if voice_client in voice_clients:
                voice_clients.remove(voice_client)
            break

# Принимаем текстовых клиентов
def accept_text_clients():
    """Принимает новые текстовые подключения"""
    while True:
        client, address = text_server.accept()
        print(f"🔌 Новое подключение от {address}")
        
        # Запрашиваем никнейм
        client.send("NICK".encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        
        # Проверка уникальности никнейма
        if nickname in nicknames:
            client.send("NICK_TAKEN".encode('utf-8'))
            client.close()
            print(f"⚠️ Никнейм '{nickname}' уже занят")
            continue
        
        # Добавляем клиента
        nicknames.append(nickname)
        clients.append(client)
        
        print(f"✅ {nickname} присоединился к чату")
        broadcast_text(f"✅ {nickname} присоединился к чату!")
        client.send("✅ Подключено к серверу!".encode('utf-8'))
        
        # Запускаем поток для этого клиента
        thread = threading.Thread(target=handle_text_client, args=(client,))
        thread.start()

# Принимаем голосовых клиентов
def accept_voice_clients():
    """Принимает голосовые подключения"""
    while True:
        voice_client, address = voice_server.accept()
        voice_clients.append(voice_client)
        print(f"🎤 Голосовое подключение от {address}")
        
        # Запускаем поток для голоса
        thread = threading.Thread(target=handle_voice_client, args=(voice_client,))
        thread.start()

# Запускаем оба сервера параллельно
text_thread = threading.Thread(target=accept_text_clients)
voice_thread = threading.Thread(target=accept_voice_clients)

text_thread.start()
voice_thread.start()

text_thread.join()
voice_thread.join()