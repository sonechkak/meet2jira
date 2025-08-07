import logging
import os
import time
import wave

import pytesseract
import speech_recognition as sr
from PIL import Image
from docx import Document
from pydub import AudioSegment
from pypdf import PdfReader

from src.utils.files.audio.get_audio_duration import get_audio_duration
from src.utils.files.audio.process_audio_chunck import process_audio_chunk
from src.utils.files.audio.split_audio_chunks import split_audio_chunks

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str, content_type: str) -> str:
    """Extract text from various file types based on content type."""

    match content_type:

        # Text files
        case 'text/plain':
           with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

        # Image files
        case 'image/png' | 'image/jpeg' | 'image/jpg' | 'image/gif':
            image = Image.open(file_path)
            available_langs = pytesseract.get_languages(config='')

            if 'rus' in available_langs and 'eng' in available_langs:
                return pytesseract.image_to_string(image, lang='rus+eng')
            elif 'eng' in available_langs:
                return pytesseract.image_to_string(image, lang='eng')
            else:
                return pytesseract.image_to_string(image)

        # Markdown files
        case 'text/x-markdown' | 'text/markdown':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        # PDF files
        case 'application/pdf':
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text

        # Docx files
        case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc =  Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text

        case 'text/html':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Music files
        case 'audio/mpeg' | 'audio/wav' | 'audio/ogg' | 'audio/mp3' | 'audio/mp4' | 'audio/x-m4a' | 'audio/x-flac' | 'audio/flac':
            try:
                file_size = get_audio_duration(file_path)

                if file_size == 0:
                    raise ValueError("Файл аудио пуст или имеет нулевую длительность")
                if file_size > 1000:  # 1000MB лимит
                    raise Exception(f"Файл слишком большой ({file_size:.1f}MB). Максимальный размер: 1000MB")

                file_ext = os.path.splitext(file_path)[1].lower()

                if file_ext in ['.wav']:
                    # Если файл уже в формате WAV, просто читаем его
                    with wave.open(file_path, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        duration = frames / float(sample_rate)

                        logger.debug(f"WAV файл: {duration:.1f}сек, {sample_rate}Hz")

                        if duration > 50:
                            # Загружаем через pydub для разбивки
                            audio_segment = AudioSegment.from_wav(file_path)
                        else:
                            # Короткий файл - обрабатываем целиком
                            r = sr.Recognizer()
                            with sr.AudioFile(file_path) as source:
                                r.adjust_for_ambient_noise(source, duration=0.5)
                                audio = r.record(source)
                                text = r.recognize_google(audio, language='ru-RU')
                                return text
                else:
                    # Конвертируем в WAV для обработки
                    audio_segment = AudioSegment.from_file(file_path, format=file_ext[1:])
                    duration = len(audio_segment) / 1000.0
                    logger.debug(f"Длинный аудиофайл: {duration:.1f}сек. Разбиваем на части...")
                    # Оптимизируем параметры
                    audio_segment = audio_segment.set_frame_rate(16000)
                    audio_segment = audio_segment.set_channels(1)
                    audio_segment = audio_segment.set_sample_width(2)
                    audio_segment = audio_segment.normalize()

                    # Разбиваем на части
                    chunks = split_audio_chunks(audio_segment, max_duration_seconds=50)
                    total_chunks = len(chunks)

                    logger.debug(f"Файл разбит на {total_chunks} частей")

                    # Обрабатываем каждую часть
                    all_text = []
                    processed_chunks = 0

                    for i, chunk in enumerate(chunks, 1):
                        try:
                            chunk_text = process_audio_chunk(chunk, i, total_chunks)
                            if chunk_text.strip():
                                all_text.append(f"[Часть {i}] {chunk_text}")
                            processed_chunks += 1

                            # Пауза между запросами к API (чтобы не превысить лимиты)
                            if i < total_chunks:
                                time.sleep(1)

                        except Exception as e:
                            print(f"Ошибка при обработке части {i}: {e}")
                            all_text.append(f"[Часть {i}] Ошибка обработки")

                    if not all_text:
                        raise Exception("Не удалось распознать речь ни в одной части файла")

                    # Объединяем весь текст
                    final_text = "\n\n".join(all_text)

                    # Добавляем информацию об обработке
                    summary = f"\n\n--- ИНФОРМАЦИЯ ОБ ОБРАБОТКЕ ---\n"
                    summary += f"Длительность файла: {duration:.1f} секунд\n"
                    summary += f"Обработано частей: {processed_chunks}/{total_chunks}\n"
                    summary += f"Общий объем текста: {len(final_text)} символов"

                    return final_text + summary


            except Exception as e:
                if "Bad Request" in str(e):
                    raise Exception(
                        "Ошибка обработки аудио. Возможные причины:\n"
                        "• Плохое качество записи\n"
                        "• Нет речи в файле\n"
                        "• Слишком тихая запись\n"
                        "• Неподдерживаемый формат"
                    )
                raise e

        # Unsupported file type
        case _:
            logger.error(f"Unsupported file type: {content_type}")
