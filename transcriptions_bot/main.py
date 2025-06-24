import asyncio
import logging
import sys
import os
import time
import moviepy as mp
import ffmpeg

from connect import TOKEN, model
from aioclass import VoiceState, AudioState, VideoState, VideoMessageState

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from pydub import AudioSegment


dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
MAX_FILE_SIZE = 2 * 1024 * 1024 # 2 МБ

@dp.message(Command("start"))
async def command_start(message: Message):
    user_name = message.from_user.username or "Без Имени"
    await message.answer(f"✅ Добро пожаловать!\n👤 {user_name}!\n📝 Напишите /list что бы увидеть команды!")


@dp.message(Command("list"))
async def list_command(message: Message):
    await message.answer(f"Список команд:\n"
                         f"🎤 /voice - Команда для извлечения текста из голосового сообщения!\n"
                         f"🎶 /audio - Команда для извлечения текста из музыки!\n"
                         f"🎬 /video - Команда для извлечения аудиодорожки из видео!\n"
                         f"🎥 /video_message - Команда для извлечения аудиодорожки из кружков Telegram!")


@dp.message(Command("voice"))
async def voice_command(message: Message, state: FSMContext):
    await message.answer("🎤 Пожалуйста, отправьте голосовое сообщение.")
    await state.set_state(VoiceState.waiting_for_voice)


@dp.message(VoiceState.waiting_for_voice, F.voice)
async def handle_voice(message: Message, state: FSMContext):
    if message.voice.file_size > MAX_FILE_SIZE:
        await message.answer("❌ Файл слишком большой! Максимальный размер: 5 МБ.")
        return

    progress_message = await message.answer("⏳ Начинаю обработку...")

    log_message = []

    try:
        # Скачивание файла
        log_download_file = await message.answer("⬇️ LOG: Скачивание файла...")
        log_message.append(log_download_file.message_id)
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        downloaded_file = await message.bot.download_file(file_path)

        # Сохраняем временный файл
        log_saving_file = await message.answer("💾 LOG: Сохраняем временный файл...")
        log_message.append(log_saving_file.message_id)
        temp_file = "temp_voice.mp3"
        with open(temp_file, "wb") as f:
            f.write(downloaded_file.read())

        # Конвертация аудио в WAV
        log_file_conversion = await message.answer("🔄 LOG: Конвертация файла...")
        log_message.append(log_file_conversion.message_id)
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
        log_text_recognition = await message.answer("🔍 LOG: Распознавание текста...")
        log_message.append(log_text_recognition.message_id)
        result = model.transcribe(wav_file)
        text = result["text"]

        # Удаление временных файлов
        log_deleting_files = await message.answer("🗑️ LOG: Удаление временных файлов...")
        log_message.append(log_deleting_files.message_id)
        os.remove(temp_file)
        os.remove(wav_file)

        # Редактируем сообщение с результатом
        total_time = int(time.time() - start_time)
        if text.strip():
            await progress_message.edit_text(f"✅ Распознанный текст:\n\n{text}\n\n⏱️ Затраченное время: {total_time} сек.")
        else:
            await progress_message.edit_text(f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек.")

    except Exception as e:
        await progress_message.edit_text(f"❌ Произошла ошибка: {str(e)}")

    finally:
        # Убедимся, что временные файлы удалены
        if os.path.exists("temp_voice.mp3"):
            os.remove("temp_voice.mp3")
        if os.path.exists("temp_voice.wav"):
            os.remove("temp_voice.wav")

        for msg_id in log_message:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except Exception:
                pass
    # Сбрасываем состояние
    await state.clear()


@dp.message(Command("audio"))
async def audio_command(message: Message, state: FSMContext):
    await message.answer("🎶 Пожалуйста, отправьте аудиофайл (не голосовое сообщение).")
    await state.set_state(AudioState.waiting_for_audio)


# Обработка аудиофайла
@dp.message(AudioState.waiting_for_audio, F.audio)
async def handle_audio(message: Message, state: FSMContext):
    if message.audio.file_size > MAX_FILE_SIZE:
        await message.answer("❌ Файл слишком большой! Максимальный размер: 5 МБ.")
        return

    progress_message = await message.answer("⏳ Начинаю обработку...")

    log_message = []

    # Скачивание аудиофайла
    try:
        log_download_file = await message.answer("⬇️ LOG: Скачивание файла...")
        log_message.append(log_download_file.message_id)
        file_id = message.audio.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        downloaded_file = await message.bot.download_file(file_path)

        # Сохраняем временный файл
        log_saving_file = await message.answer("💾 LOG: Сохраняем временный файл...")
        log_message.append(log_saving_file.message_id)
        temp_file = "temp_audio.mp3"
        with open(temp_file, "wb") as f:
            f.write(downloaded_file.read())

        # Конвертация аудио в WAV
        log_file_conversion = await message.answer("🔄 LOG: Конвертация файла...")
        log_message.append(log_file_conversion.message_id)
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
        log_text_recognition = await message.answer("🔍 LOG: Распознавание текста...")
        log_message.append(log_text_recognition.message_id)
        result = model.transcribe(wav_file)
        text = result["text"]

        # Удаление временных файлов
        log_deleting_files = await message.answer("🗑️ LOG: Удаление временных файлов...")
        log_message.append(log_deleting_files.message_id)
        os.remove(temp_file)
        os.remove(wav_file)

        # Редактируем сообщение с результатом
        total_time = int(time.time() - start_time)
        if text.strip():
            await progress_message.edit_text(f"✅ Распознанный текст:\n\n{text}\n\n⏱️ Затраченное время: {total_time} сек.")
        else:
            await progress_message.edit_text(f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек.")

    except Exception as e:
        await progress_message.edit_text(f"❌ Произошла ошибка: {str(e)}")

    finally:
        # Убедимся, что временные файлы удалены
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")

        for msg_id in log_message:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except Exception:
                pass
    # Сбрасываем состояние
    await state.clear()


@dp.message(Command("video"))
async def video_command(message: Message, state: FSMContext):
    await message.answer("🎬 Пожалуйста, отправьте видеофайл.")
    await state.set_state(VideoState.waiting_for_video)


@dp.message(VideoState.waiting_for_video, F.video)
async def handled_video(message: Message, state: FSMContext):
    if message.video.file_size > MAX_FILE_SIZE:
        await message.answer("❌ Файл слишком большой! Максимальный размер: 5 МБ.")
        return

    progress_message = await message.answer("⏳ Начинаю обработку видео...")

    log_message = []

    try:
        # Скачиваем видеофайл
        log_download_file = await message.answer("⬇️ LOG: Скачивание файла...")
        log_message.append(log_download_file.message_id)
        file_id = message.video.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        downloaded_file = await message.bot.download_file(file_path)

        # Сохраняем временный файл
        log_saving_file = await message.answer("💾 LOG: Сохраняем временный файл...")
        log_message.append(log_saving_file.message_id)
        temp_video = "temp_video.mp4"
        with open(temp_video, "wb") as f:
            f.write(downloaded_file.read())

        # Извлекаем аудиодорожку из видео
        audio_file = "temp_audio.mp3"
        try:
            video_clip = mp.VideoFileClip(temp_video)
            video_clip.audio.write_audiofile(audio_file)
        finally:
            video_clip.close()

        # Конвертируем аудио в WAV
        log_file_conversion = await message.answer("🔄 LOG: Конвертация файла...")
        log_message.append(log_file_conversion.message_id)
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

        # Распознаем текст с помощью Whisper
        log_text_recognition = await message.answer("🔍 LOG: Распознавание текста...")
        log_message.append(log_text_recognition.message_id)
        result = model.transcribe(wav_file)
        text = result["text"]

        # Удаление временных файлов
        log_deleting_files = await message.answer("🗑️ LOG: Удаление временных файлов...")
        log_message.append(log_deleting_files.message_id)
        os.remove(temp_video)
        os.remove(audio_file)
        os.remove(wav_file)

        # Редактируем сообщение с результатом
        total_time = int(time.time() - start_time)
        if text.strip():
            await progress_message.edit_text(
                f"✅ Распознанный текст:\n\n{text}\n\n⏱️ Затраченное время: {total_time} сек.")
        else:
            await progress_message.edit_text(
                f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек.")

    except Exception as e:
        await progress_message.edit_text(f"❌ Произошла ошибка: {str(e)}")

    finally:
        # Убедимся, что временные файлы удалены
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")

        for msg_id in log_message:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except Exception:
                pass
        # Сброс состояния
    await state.clear()


# Функция для извлечения аудио
def extract_audio(input_file, output_file):
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, format="mp3")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg._run.Error as e:  # Используем ffmpeg._run.Error
        logging.error(f"Ошибка FFmpeg: {e.stderr.decode()}")
        raise RuntimeError("Не удалось извлечь аудио из видео.")


@dp.message(Command("video_message"))
async def video_message_command(message: Message, state: FSMContext):
    await message.answer("🎥 Пожалуйста, отправьте кружок (видеозаметку).")
    await state.set_state("waiting_for_video_message")


@dp.message(StateFilter("waiting_for_video_message"), F.video_note)
async def handled_video_message(message: Message, state: FSMContext):
    # Проверка размера файла
    if message.video_note.file_size > MAX_FILE_SIZE:
        file_size_mb = message.video_note.file_size / (1024 * 1024)
        await message.answer(f"❌ Файл слишком большой! Размер: {file_size_mb:.2f} МБ. Максимальный размер: 5 МБ.")
        return

    # Уведомление о начале обработки
    progress_message = await message.answer("⏳ Начинаю обработку кружка...")

    # Список для хранения ID лог-сообщений
    log_message = []

    try:
        # Определяем абсолютные пути для файлов
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        temp_video = os.path.join(BASE_DIR, "temp_video_note.mp4")
        audio_file = os.path.join(BASE_DIR, "temp_audio.mp3")
        wav_file = os.path.join(BASE_DIR, "temp_audio.wav")

        # Скачивание кружка
        log_download_file = await message.answer("⬇️ LOG: Скачивание файла...")
        log_message.append(log_download_file.message_id)
        file_id = message.video_note.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        downloaded_file = await message.bot.download_file(file_path)

        # Сохранение временного файла
        log_saving_file = await message.answer("💾 LOG: Сохраняем временный файл...")
        log_message.append(log_saving_file.message_id)
        with open(temp_video, "wb") as f:
            f.write(downloaded_file.read())

        # Извлекаем аудиодорожку из видео
        log_extraction = await message.answer("🎵 LOG: Извлечение аудио...")
        log_message.append(log_extraction.message_id)
        extract_audio(temp_video, audio_file)

        # Проверяем, был ли создан файл
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Файл {audio_file} не был создан.")

        # Конвертируем аудио в WAV
        log_conversion = await message.answer("🔄 LOG: Конвертация файла...")
        log_message.append(log_conversion.message_id)
        audio = AudioSegment.from_file(audio_file)
        audio.export(wav_file, format="wav")

        # Запуск таймера
        start_time = time.time()

        # Распознаем текст с помощью Whisper
        log_recognition = await message.answer("🔍 LOG: Распознавание текста...")
        log_message.append(log_recognition.message_id)
        result = model.transcribe(wav_file)
        text = result["text"]

        # Удаление временных файлов
        log_deletion = await message.answer("🗑️ LOG: Удаление временных файлов...")
        log_message.append(log_deletion.message_id)

        # Редактируем сообщение с результатом
        total_time = int(time.time() - start_time)
        if text.strip():
            await progress_message.edit_text(
                f"✅ Распознанный текст:\n\n{text}\n\n⏱️ Затраченное время: {total_time} сек."
            )
        else:
            await progress_message.edit_text(
                f"❌ Не удалось распознать текст.\n\n⏱️ Затраченное время: {total_time} сек."
            )

    except Exception as e:
        logging.error(f"Произошла ошибка: {str(e)}")
        await progress_message.edit_text(f"❌ Произошла ошибка: {str(e)}")

    finally:
        # Убедимся, что временные файлы удалены
        for file in [temp_video, audio_file, wav_file]:
            if os.path.exists(file):
                os.remove(file)

        # Удаляем лог-сообщения
        for msg_id in log_message:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except Exception:
                pass

    # Сбрасываем состояние
    await state.clear()


# Обработка неизвестных сообщений
@dp.message()
async def unknown_message(message: Message):
    await message.answer("❌ Извините, я не понимаю это сообщение. Пожалуйста, используйте доступные команды.")


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
