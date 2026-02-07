import socket
import threading
import struct

# Списки для хранения клиентов
clients = []           # Socket объекты
nicknames = []         # Никнеймы
voice_clients = []     # Клиенты для голоса (отдельное соединение)
voice_nicknames = []   # Никнеймы для голосовых клиентов (по порядку)

# Определяем локальный IP для вывода
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "не удалось определить"

# Текстовый сервер (0.0.0.0 = принимать со всех интерфейсов)
text_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
text_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
text_server.bind(('0.0.0.0', 5555))
text_server.listen()

# Голосовой сервер (отдельный порт)
voice_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
voice_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
voice_server.bind(('0.0.0.0', 5556))
voice_server.listen()

local_ip = get_local_ip()
print("Текстовый сервер запущен на порту 5555")
print("Голосовой сервер запущен на порту 5556")
print(f"Локальный IP: {local_ip}")
print(f"Клиенты в локальной сети: вводят {local_ip}")
print(f"Клиенты из интернета: вводят ваш публичный IP (проброс портов 5555, 5556)")
print("Ожидание подключений...\n")


def send_msg(client, message):
    """Отправляет сообщение клиенту с \\n разделителем"""
    client.send((message + "\n").encode('utf-8'))


def broadcast_text(message, exclude_client=None):
    """Отправляет текстовое сообщение всем клиентам"""
    for client in clients[:]:
        if client != exclude_client:
            try:
                send_msg(client, message)
            except:
                remove_client(client)


def send_userlist():
    """Рассылает актуальный список пользователей всем клиентам"""
    userlist_msg = "USERLIST:" + ",".join(nicknames)
    for client in clients[:]:
        try:
            send_msg(client, userlist_msg)
        except:
            remove_client(client)


def broadcast_voice(voice_data, sender):
    """Отправляет голосовые данные всем кроме отправителя, с ником в заголовке"""
    sender_nick = ""
    if sender in voice_clients:
        idx = voice_clients.index(sender)
        if idx < len(voice_nicknames):
            sender_nick = voice_nicknames[idx]

    nick_bytes = sender_nick.encode('utf-8')
    header = struct.pack('>H', len(nick_bytes)) + nick_bytes
    tagged_data = header + voice_data

    for client in voice_clients[:]:
        if client != sender:
            try:
                client.send(tagged_data)
            except:
                if client in voice_clients:
                    idx = voice_clients.index(client)
                    voice_clients.remove(client)
                    if idx < len(voice_nicknames):
                        voice_nicknames.pop(idx)


def remove_client(client):
    """Удаляет клиента из системы"""
    if client in clients:
        index = clients.index(client)
        nickname = nicknames[index]
        clients.remove(client)
        nicknames.remove(nickname)
        client.close()
        broadcast_text(f"[Сервер] {nickname} покинул чат")
        send_userlist()
        print(f"{nickname} отключился")


def handle_text_client(client):
    """Обрабатывает текстовые сообщения от клиента"""
    buffer = ""
    while True:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                remove_client(client)
                break

            buffer += data
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                message = message.strip()
                if not message:
                    continue

                if client not in clients:
                    return
                index = clients.index(client)
                nickname = nicknames[index]

                if message == 'TYPING':
                    broadcast_text(f"TYPING:{nickname}", exclude_client=client)
                elif message.startswith('/'):
                    if message == '/users':
                        users_list = ', '.join(nicknames)
                        send_msg(client, f"[Сервер] Онлайн: {users_list}")
                    elif message == '/help':
                        send_msg(client, "[Сервер] Команды: /users - список, /help - справка")
                    else:
                        send_msg(client, "[Сервер] Неизвестная команда. /help")
                else:
                    formatted_message = f"[{nickname}]: {message}"
                    broadcast_text(formatted_message, exclude_client=client)
                    print(f"  {formatted_message}")

        except:
            remove_client(client)
            break


def handle_voice_client(voice_client):
    """Обрабатывает голосовые данные от клиента"""
    while True:
        try:
            voice_data = voice_client.recv(4096)
            if voice_data:
                broadcast_voice(voice_data, voice_client)
            else:
                break
        except:
            if voice_client in voice_clients:
                idx = voice_clients.index(voice_client)
                voice_clients.remove(voice_client)
                if idx < len(voice_nicknames):
                    voice_nicknames.pop(idx)
            break


def accept_text_clients():
    """Принимает новые текстовые подключения"""
    while True:
        client, address = text_server.accept()
        print(f"Новое подключение от {address}")

        send_msg(client, "NICK")
        nickname = client.recv(1024).decode('utf-8').strip()

        if nickname in nicknames:
            send_msg(client, "NICK_TAKEN")
            client.close()
            print(f"Никнейм '{nickname}' уже занят")
            continue

        nicknames.append(nickname)
        clients.append(client)

        print(f"{nickname} присоединился к чату")
        broadcast_text(f"[Сервер] {nickname} присоединился к чату!", exclude_client=client)
        send_msg(client, "[Сервер] Подключено!")
        send_userlist()

        thread = threading.Thread(target=handle_text_client, args=(client,))
        thread.daemon = True
        thread.start()


def accept_voice_clients():
    """Принимает голосовые подключения"""
    while True:
        voice_client, address = voice_server.accept()
        try:
            nick_data = voice_client.recv(1024).decode('utf-8').strip()
        except:
            nick_data = ""

        voice_clients.append(voice_client)
        voice_nicknames.append(nick_data)
        print(f"Голосовое подключение от {address} ({nick_data})")

        thread = threading.Thread(target=handle_voice_client, args=(voice_client,))
        thread.daemon = True
        thread.start()


text_thread = threading.Thread(target=accept_text_clients)
voice_thread = threading.Thread(target=accept_voice_clients)
text_thread.start()
voice_thread.start()
text_thread.join()
voice_thread.join()
