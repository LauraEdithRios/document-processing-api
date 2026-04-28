import logging
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 2
DEFAULT_TEXTS_FOLDER = "data/texts"


def _file_delay() -> float:
    return float(os.getenv("WORKER_FILE_DELAY", "0"))


def get_text_files(folder_path: str = DEFAULT_TEXTS_FOLDER) -> List[Path]:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"La carpeta {folder_path} no existe")
    return sorted(folder.glob("*.txt"))


def split_into_batches(files: List[Path], batch_size: int = DEFAULT_BATCH_SIZE) -> List[List[Path]]:
    return [
        files[index:index + batch_size]
        for index in range(0, len(files), batch_size)
    ]


def normalize_words(text: str) -> List[str]:
    words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    return words


def analyze_text(text: str) -> Dict:
    lines = text.splitlines()
    words = normalize_words(text)

    return {
        "total_words": len(words),
        "total_lines": len(lines),
        "total_characters": len(text),
        "word_frequencies": Counter(words),
    }


def generate_summary(text: str, max_sentences: int = 3) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    clean_sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    return " ".join(clean_sentences[:max_sentences])


def process_documents(
    folder_path: str = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    pause_check=None,
    process_id: Optional[str] = None,
    progress_callback=None,
) -> Dict:
    if folder_path is None:
        folder_path = DEFAULT_TEXTS_FOLDER

    files = get_text_files(folder_path)

    if not files:
        raise FileNotFoundError("No se encontraron archivos para procesar")

    logger.info(
        "worker started",
        extra={"process_id": process_id, "file": f"{len(files)} files found"},
    )

    batches = split_into_batches(files, batch_size)
    total_words = 0
    total_lines = 0
    total_characters = 0
    global_word_frequencies = Counter()
    files_processed = []
    summaries = []

    for batch in batches:
        for file_path in batch:
            if pause_check:
                pause_check()
            if file_path.suffix.lower() != ".txt":
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.error(
                    "file read failed",
                    extra={"process_id": process_id, "file": file_path.name, "error": str(exc)},
                )
                continue
            try:
                analysis = analyze_text(text)
            except Exception as exc:
                logger.error(
                    "file analysis failed",
                    extra={"process_id": process_id, "file": file_path.name, "error": str(exc)},
                )
                continue

            total_words += analysis["total_words"]
            total_lines += analysis["total_lines"]
            total_characters += analysis["total_characters"]
            global_word_frequencies.update(analysis["word_frequencies"])
            files_processed.append(file_path.name)
            summary = generate_summary(text)
            if summary:
                summaries.append(f"{file_path.name}: {summary}")

            if progress_callback:
                progress_callback(len(files_processed), len(files))

            delay = _file_delay()
            if delay > 0:
                time.sleep(delay)

            logger.info(
                "file processed",
                extra={
                    "process_id": process_id,
                    "file": file_path.name,
                    "words": analysis["total_words"],
                    "lines": analysis["total_lines"],
                },
            )

    most_frequent_words = [
        word
        for word, _ in global_word_frequencies.most_common(5)
    ]

    logger.info(
        "worker completed",
        extra={"process_id": process_id, "file": f"{len(files_processed)}/{len(files)} files processed"},
    )

    return {
        "total_files": len(files),
        "processed_files": len(files_processed),
        "total_words": total_words,
        "total_lines": total_lines,
        "total_characters": total_characters,
        "most_frequent_words": most_frequent_words,
        "files_processed": files_processed,
        "summary": "\n".join(summaries),
    }
