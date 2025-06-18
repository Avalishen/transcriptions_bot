from aiogram.fsm.state import State, StatesGroup

class VoiceState(StatesGroup):
    waiting_for_voice = State()

class AudioState(StatesGroup):
    waiting_for_audio = State()

class VideoState(StatesGroup):
    waiting_for_video = State()