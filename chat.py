import flet as ft
from transformers import pipeline
from hashing import hash_password, verify_password
import secrets

# Инициализация пайплайнов для модерации
moderation_pipe = pipeline("text2text-generation", model="abhiai/ModerationGPT")
toxicity_pipe = pipeline("text2text-generation", model="Vaibhav9401/toxic_mt5_test")

# Секретный фактор для хеширования паролей (используется в hashing.py)
SECRET_FACTOR = "bmstu"

# Пример базы пользователей с хешированными паролями, аватарками и альтернативными никами.
users = {
    "admin": {
        "salt": "static_salt_admin",
        "hash": hash_password("admin123", "static_salt_admin", SECRET_FACTOR),
        "avatar": "https://i.pravatar.cc/150?img=1",
        "nickname": "Администратор"
    },
    "user1": {
        "salt": "static_salt_user1",
        "hash": hash_password("password1", "static_salt_user1", SECRET_FACTOR),
        "avatar": "https://i.pravatar.cc/150?img=2",
        "nickname": "Пользователь1"
    }
}

# Класс сообщения теперь включает поле avatar_url (по умолчанию None)
class Message():
    def __init__(self, user_name: str, text: str, message_type: str, avatar_url: str = None):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.avatar_url = avatar_url

# Обновлённый класс для отображения сообщения с аватаркой.
class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = "start"
        # Если для пользователя задан URL аватарки — показываем изображение, иначе используем инициалы.
        if message.avatar_url:
            avatar = ft.CircleAvatar(
                src=message.avatar_url,
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name)
            )
        else:
            avatar = ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name), color=ft.colors.BLACK),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name)
            )
        self.controls = [
            avatar,
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold", color=ft.colors.BLACK),
                    ft.Text(message.text, selectable=True, color=ft.colors.BLACK),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str):
        return user_name[0].upper() if user_name else "?"

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

def main(page: ft.Page):
    page.title = "Красивая чат-комната"
    page.bgcolor = ft.colors.WHITE
    page.horizontal_alignment = "center"
    
    # Область для отображения сообщений чата
    chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    # Поле ввода нового сообщения с черным текстом на светлом фоне
    new_message = ft.TextField(
        hint_text="Напишите сообщение...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=lambda e: send_message_click(e),
        color=ft.colors.BLACK,
        bgcolor=ft.colors.GREY_100
    )

    def send_message_click(e):
        if new_message.value.strip() != "":
            moderated = moderation_pipe(new_message.value)[0]['generated_text']
            toxic_check = toxicity_pipe(new_message.value)[0]['generated_text']
            if "*" in moderated:
                new_message.value = moderated
            elif "non-toxic" not in toxic_check:
                new_message.value += f"\n[Сообщение будет проверено модератором]"
            page.pubsub.send_all(
                Message(
                    page.session.get("user_name"),
                    new_message.value,
                    message_type="chat_message",
                    avatar_url=page.session.get("user_avatar")
                )
            )
            new_message.value = ""
            new_message.focus()
            page.update()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK, size=12)
        chat_list.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

    # --- Окно авторизации ---
    username_field = ft.TextField(label="Имя пользователя", autofocus=True, color=ft.colors.BLACK)
    password_field = ft.TextField(label="Пароль", password=True, can_reveal_password=True, color=ft.colors.BLACK)

    def login_click(e):
        username = username_field.value.strip()
        password = password_field.value.strip()
        if not username or not password:
            username_field.error_text = "Поля не должны быть пустыми!"
            username_field.update()
            password_field.error_text = "Поля не должны быть пустыми!"
            password_field.update()
        elif username not in users:
            username_field.error_text = "Пользователь не найден!"
            username_field.update()
        else:
            user_data = users[username]
            if not verify_password(user_data["hash"], password, user_data["salt"], SECRET_FACTOR):
                password_field.error_text = "Неверный пароль!"
                password_field.update()
            else:
                user_display_name = user_data.get("nickname", username)
                page.session.set("user_name", user_display_name)
                page.session.set("user_avatar", user_data["avatar"])
                # Закрываем диалог авторизации
                login_dialog.open = False
                page.pubsub.send_all(
                    Message(
                        user_display_name,
                        f"{user_display_name} вошёл в чат.",
                        message_type="login_message",
                        avatar_url=user_data["avatar"]
                    )
                )
                page.update()

    login_dialog = ft.AlertDialog(
        open=False,  # Окно авторизации будет открываться после представления
        modal=True,
        title=ft.Text("Авторизация", color=ft.colors.BLACK),
        content=ft.Column([username_field, password_field], tight=True),
        actions=[ft.ElevatedButton(text="Войти", on_click=login_click)],
        actions_alignment="end",
    )

    # --- Окно представления (презентации) ---
    def on_welcome_dismiss(e):
        welcome_dialog.open = False
        page.dialog = login_dialog
        login_dialog.open = True
        page.update()

    welcome_dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("Добро пожаловать!", color=ft.colors.BLACK),
        content=ft.Column(
            [
                ft.Text(
                    "Это чат-комната для общения и обмена сообщениями.\n"
                    "Перед началом работы ознакомьтесь с правилами и нажмите 'Начать'.",
                    color=ft.colors.BLACK
                )
            ],
            tight=True
        ),
        actions=[ft.ElevatedButton(text="Начать", on_click=on_welcome_dismiss)],
        actions_alignment="end",
    )
    # Сначала показываем окно представления
    page.dialog = welcome_dialog

    # Размещение элементов страницы: область сообщений и панель ввода нового сообщения
    page.add(
        ft.Container(
            content=chat_list,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                new_message,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Отправить сообщение",
                    on_click=send_message_click,
                ),
            ]
        ),
    )

ft.app(port=8550, target=main, view=ft.WEB_BROWSER)
