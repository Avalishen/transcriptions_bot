import asyncio
import logging
import sys
import os
import time
import moviepy as mp

from connect import TOKEN, model
from aioclass import VoiceState, AudioState, VideoState

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from pydub import AudioSegment


dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
MAX_FILE_SIZE = 500 * 1024 * 1024

@dp.message(Command("start"))
async def command_start(message: Message):
    user_name = message.from_user.username or "Без Имени"
    await message.answer(f"✅ Добро пожаловать!\n👤 {user_name}!\n📝 Напишите /list что бы увидеть команды!")


@dp.message(Command("list"))
async def list_command(message: Message):
    await message.answer(f"Список команд:\n"
                         f"🎤 /voice - Команда для извлечения текста из голосового сообщения!\n"
                         f"🎶 /audio - Команда для извлечения текста из музыки!\n"
                         f"🎬 /video - Команда для извлечения аудиодорожки из видео!")


@dp.message(Command("voice"))
async def voice_command(message: Message, state: FSMContext):
    await message.answer("🎤 Пожалуйста, отправьте голосовое сообщение.")
    await state.set_state(VoiceState.waiting_for_voice)


@dp.message(VoiceState.waiting_for_voice, F.voice)
async def handle_voice(message: Message, state: FSMContext):

    progress_message = await message.answer("⏳ Начинаю обработку...")

    file_id = message.voice.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await message.bot.download_file(file_path)

    # Сохраняем временный файл
    await message.answer("💾 LOG: Сохраняем временный файл...")

    temp_file = "temp_voice.mp3"
    with open(temp_file, "wb") as f:
        f.write(downloaded_file.read())

    # Конвертация аудио в WAV
    await message.answer("🔄 LOG: Конвертация файла...")
    audio = AudioSegment.from_file(temp_file)
    wav_file = "temp_voice.wav"
    audio.export(wav_file, format="wav")

    # Запуск таймера
    start_time = time.time()

    # Показываем реальное время выполнения
    while True:
        elapsed_time = int(time.time() - start_time)
        await progress_message.edit_text(f"⏳ Обработка... {elapsed_time} сек.")
        time.sleep(1)  # Обновляем каждую секунду

        # Проверяем, завершилась ли обработка
        if elapsed_time > 1:  # Пример: эмуляция завершения
            break


    # Распознавание текста
    await message.answer("🔍 LOG: Распознавание текста...")
    result = model.transcribe(wav_file)
    text = result["text"]

    # Удаление временных файлов
    await message.answer("🗑️ LOG: Удаление временных файлов...")
    os.remove(temp_file)
    os.remove(wav_file)

    # Редактируем сообщение с результатом
    total_time = int(time.time() - start_time)
    if text.strip():
        await progress_message.edit_text(
            f"✅ Распознанный текст:\n{text}\n\n⏱️ Затраченное время: {total_time} сек."
        )
    else:
        await progress_message.edit_text(
            f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек."
        )
    # Сбрасываем состояние
    await state.clear()


@dp.message(Command("audio"))
async def audio_command(message: Message, state: FSMContext):
    await message.answer("🎶 Пожалуйста, отправьте аудиофайл (не голосовое сообщение).")
    await state.set_state(AudioState.waiting_for_audio)


# Обработка аудиофайла
@dp.message(AudioState.waiting_for_audio, F.audio)
async def handle_audio(message: Message, state: FSMContext):

    progress_message = await message.answer("⏳ Начинаю обработку...")

    # Скачивание аудиофайла
    file_id = message.audio.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await message.bot.download_file(file_path)

    # Сохраняем временный файл
    await message.answer("💾 LOG: Сохраняем временный файл...")
    temp_file = "temp_audio.mp3"
    with open(temp_file, "wb") as f:
        f.write(downloaded_file.read())

    # Конвертация аудио в WAV
    await message.answer("🔄 LOG: Конвертация файла...")
    audio = AudioSegment.from_file(temp_file)
    wav_file = "temp_audio.wav"
    audio.export(wav_file, format="wav")

    # Запуск таймера
    start_time = time.time()

    # Показываем реальное время выполнения
    while True:
        elapsed_time = int(time.time() - start_time)
        await progress_message.edit_text(f"⏳ Обработка... {elapsed_time} сек.")
        time.sleep(1)  # Обновляем каждую секунду

        # Проверяем, завершилась ли обработка
        if elapsed_time > 1:  # Пример: эмуляция завершения
            break

    # Распознавание текста
    await message.answer("🔍 LOG: Распознавание текста...")
    result = model.transcribe(wav_file)
    text = result["text"]

    # Удаление временных файлов
    await message.answer("🗑️ LOG: Удаление временных файлов...")
    os.remove(temp_file)
    os.remove(wav_file)

    # Редактируем сообщение с результатом
    total_time = int(time.time() - start_time)
    if text.strip():
        await progress_message.edit_text(
            f"✅ Распознанный текст:\n{text}\n\n⏱️ Затраченное время: {total_time} сек."
        )
    else:
        await progress_message.edit_text(
            f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек."
        )
    # Сбрасываем состояние
    await state.clear()


@dp.message(Command("video"))
async def video_command(message: Message, state: FSMContext):
    await message.answer("🎬 Пожалуйста, отправьте видеофайл.")
    await state.set_state(VideoState.waiting_for_video)


@dp.message(VideoState.waiting_for_video, F.video)
async def handled_video(message: Message, state: FSMContext):

    progress_message = await message.answer("⏳ Начинаю обработку видео...")

    # Скачиваем видеофайл
    file_id = message.video.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await message.bot.download_file(file_path)

    # Сохраняем временный файл
    await message.answer("💾 LOG: Сохраняем временный файл...")
    temp_video = "temp_video.mp4"
    with open(temp_video, "wb") as f:
        f.write(downloaded_file.read())

    # Извлекаем аудиодорожку из видео
    audio_file = "temp_audio.mp3"
    try:
        video_clip = mp.VideoFileClip(temp_video)  # Открываем видео
        video_clip.audio.write_audiofile(audio_file)  # Извлекаем аудио
    finally:
        video_clip.close()  # Явно закрываем объект VideoFileClip

    # Конвертация аудио в WAV
    await message.answer("🔄 LOG: Конвертация файла...")
    audio = AudioSegment.from_file(audio_file)
    wav_file = "temp_audio.wav"
    audio.export(wav_file, format="wav")

    # Запуск таймера
    start_time = time.time()

    # Показываем реальное время выполнения
    while True:
        elapsed_time = int(time.time() - start_time)
        await progress_message.edit_text(f"⏳ Обработка... {elapsed_time} сек.")
        time.sleep(1)  # Обновляем каждую секунду

        # Проверяем, завершилась ли обработка
        if elapsed_time > 1:  # Пример: эмуляция завершения
            break

    # Распознавание текста
    await message.answer("🔍 LOG: Распознавание текста...")
    result = model.transcribe(wav_file)
    text = result["text"]

    # Удаление временных файлов
    await message.answer("🗑️ LOG: Удаление временных файлов...")
    os.remove(temp_video)
    os.remove(audio_file)
    os.remove(wav_file)

    # Редактируем сообщение с результатом
    total_time = int(time.time() - start_time)
    if text.strip():
        await progress_message.edit_text(
            f"✅ Распознанный текст:\n{text}\n\n⏱️ Затраченное время: {total_time} сек."
        )
    else:
        await progress_message.edit_text(
            f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек."
        )
    # Сбрасываем состояние
    await state.clear()


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
