import flet as ft
from transformers import pipeline

# Инициализация пайплайнов для модерации
pipe = pipeline("text2text-generation", model="abhiai/ModerationGPT")
pipe_toxic = pipeline("text2text-generation", model="Vaibhav9401/toxic_mt5_test")

class Message():
    def __init__(self, user_name: str, text: str, message_type: str):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = "start"
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name)),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
            ),
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold"),
                    ft.Text(message.text, selectable=True),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"

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
    page.horizontal_alignment = "stretch"
    page.title = "ЪУЪ чат"

    def join_chat_click(e):
        if not join_user_name.value:
            join_user_name.error_text = "Имя не может быть пустым!"
            join_user_name.update()
        else:
            page.session.set("user_name", join_user_name.value)
            page.dialog.open = False
            new_message.prefix = ft.Text(f"{join_user_name.value}: ")
            page.pubsub.send_all(Message(user_name=join_user_name.value, text=f"{join_user_name.value} вошёл в чат.", message_type="login_message"))
            page.update()

    def send_message_click(e):
        if new_message.value != "":
            # Проверка модерации: если вывод содержит символы '*', значит сообщение было модифицировано
            if "*" in pipe(new_message.value)[0]['generated_text']:
                new_message.value = pipe(new_message.value)[0]['generated_text']
            # Если модель токсичности не возвращает "non-toxic" – добавляем уведомление о проверке модератором
            elif not ("non-toxic" in pipe_toxic(new_message.value)[0]['generated_text']):
                new_message.value += f"\n сообщение от {page.session.get('user_name')} будет рассмотрено модератором"
            page.pubsub.send_all(Message(page.session.get("user_name"), new_message.value, message_type="chat_message"))
            new_message.value = ""
            new_message.focus()
            page.update()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

    # Диалог для ввода никнейма
    join_user_name = ft.TextField(
        label="Введите никнейм:",
        autofocus=True,
        on_submit=join_chat_click,
    )
    page.dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("Добро пожаловать!"),
        content=ft.Column([join_user_name], width=300, height=70, tight=True),
        actions=[ft.ElevatedButton(text="Войти", on_click=join_chat_click)],
        actions_alignment="end",
    )

    # Область сообщений чата
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # Форма ввода нового сообщения
    new_message = ft.TextField(
        hint_text="Напишите сообщение...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    # Добавление элементов на страницу
    page.add(
        ft.Container(
            content=chat,
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
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
            ]
        ),
    )

# Запуск приложения. Приложение откроется в веб-браузере на порту 8550.
ft.app(port=8550, target=main, view=ft.WEB_BROWSER)