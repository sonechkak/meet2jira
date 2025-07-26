def split_audio_chunks(audio_segment, max_duration_seconds=50):
    """Разделить аудио на части по времени"""
    max_duration_ms = max_duration_seconds * 1000
    chunks = []

    for start_ms in range(0, len(audio_segment), max_duration_ms):
        end_ms = min(start_ms + max_duration_ms, len(audio_segment))
        chunk = audio_segment[start_ms:end_ms]
        chunks.append(chunk)

    return chunks
