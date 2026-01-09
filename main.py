import telebot
import os
import json
import time
import shutil
from shutil import rmtree
from pytube import YouTube
import yt_dlp


# ===================== НАСТРОЙКИ =====================

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data', 'user')
CONFIG_PATH = os.path.join(BASE_DIR, 'configbot.json')

AUDIO_OPTIONS = {
    'format': 'mp3/bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }]
}


# ===================== ПРОВЕРКИ =====================

if not shutil.which('ffmpeg'):
    print('⚠ FFmpeg не установлен! Конвертация в MP3 может не работать.')


# ===================== ЗАГРУЗКА ТОКЕНА =====================

def load_token(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data['TOKEN']


TOKEN = load_token(CONFIG_PATH)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')


# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def get_user_dir(chat_id: int) -> str:
    """Возвращает путь к папке пользователя"""
    path = os.path.join(DATA_DIR, str(chat_id))
    os.makedirs(path, exist_ok=True)
    return path


def clear_user_dir(path: str) -> None:
    """Удаляет папку пользователя"""
    if os.path.exists(path):
        rmtree(path)


def download_audio(url: str, output_dir: str) -> str:
    """
    Скачивает аудио с YouTube.
    Возвращает путь к MP3-файлу.
    """
    yt = YouTube(url)  # для получения названия
    os.chdir(output_dir)

    with yt_dlp.YoutubeDL(AUDIO_OPTIONS) as ydl:
        ydl.download([url])

    files = [f for f in os.scandir(output_dir) if f.is_file()]
    if not files:
        raise FileNotFoundError('Аудиофайл не найден')

    return yt.title, files[0].path


# ===================== HANDLERS =====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        '<i>Добро пожаловать в Bot_YouTube!</i>\n'
        'Отправь ссылку на YouTube — я пришлю аудио 🎵'
    )


@bot.message_handler(content_types=['text'])
def youtube_handler(message):
    chat_id = message.chat.id
    url = message.text.strip()

    status_msg = bot.send_message(chat_id, '<i>🎧 Загрузка аудио...</i>')
    user_dir = None

    try:
        user_dir = get_user_dir(chat_id)

        title, audio_path = download_audio(url, user_dir)

        bot.send_chat_action(chat_id, 'upload_audio')
        bot.edit_message_text(
            f'😎 <i>Отправка <b>{title}</b></i>',
            chat_id=chat_id,
            message_id=status_msg.message_id
        )

        with open(audio_path, 'rb') as audio:
            bot.send_audio(chat_id, audio)

        bot.edit_message_text(
            '🎸 <i>Музыка отправлена!</i>',
            chat_id=chat_id,
            message_id=status_msg.message_id
        )

    except Exception as e:
        bot.edit_message_text(
            '<i>❌ Ошибка загрузки. Проверь ссылку или попробуй позже.</i>',
            chat_id=chat_id,
            message_id=status_msg.message_id
        )
        print(f'Ошибка: {e}')

    finally:
        time.sleep(3)
        if user_dir:
            clear_user_dir(user_dir)


# ===================== ЗАПУСК =====================

if __name__ == '__main__':
    print('🤖 Bot is listening...')
    bot.infinity_polling()
