import whisper

TOKEN = "7704364728:AAF2kaefczrvMtwbK2sC9PvEKGFkIt8yV3Q"
MODEL_PATH = r"C:\Users\denis\PycharmProjects\transcriptions_bot\model"
FFMPEG_PATH = r"C:\ffmpeg-7.1.1\tools\ffmpeg\bin\ffmpeg.exe"
GENIUS_API_TOKEN = "4wQygJZ_0sfgtukAWZTUDYbSS0991sTX0ldsFLXG_-mbPiG2YVoKjwsGZmcF0M_S"
model = whisper.load_model("large")