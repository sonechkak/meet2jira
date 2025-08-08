from pydub import AudioSegment


def get_audio_duration(file_path):
    """Получить длительность аудиофайла"""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # в секундах
    except Exception:
        return 0
