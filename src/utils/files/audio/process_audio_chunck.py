import os
import tempfile

import speech_recognition as sr


def process_audio_chunk(audio_chunk, chunk_number, total_chunks):
    """Обработка одного фрагмента аудио"""
    r = sr.Recognizer()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_path = temp_wav.name

    try:
        # Экспортируем фрагмент в WAV
        audio_chunk.export(temp_wav_path, format="wav")

        with sr.AudioFile(temp_wav_path) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.record(source)

            try:
                text = r.recognize_google(audio, language="ru-RU")
                print(f"Обработан фрагмент {chunk_number}/{total_chunks}")
                return text
            except sr.UnknownValueError:
                print(f"Фрагмент {chunk_number}/{total_chunks}: речь не распознана")
                return ""
            except sr.RequestError as e:
                print(f"Ошибка API для фрагмента {chunk_number}: {e}")
                return ""

    finally:
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
