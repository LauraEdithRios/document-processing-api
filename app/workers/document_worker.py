import re
from collections import Counter
from pathlib import Path
from typing import Dict, List


# Cantidad de archivos que se procesan por lote.
DEFAULT_BATCH_SIZE = 2

# Carpeta desde donde el worker va a leer los archivos .txt.
DEFAULT_TEXTS_FOLDER = "data/texts"


def get_text_files(folder_path: str = DEFAULT_TEXTS_FOLDER) -> List[Path]:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"La carpeta {folder_path} no existe")
    return sorted(folder.glob("*.txt"))


def split_into_batches(files: List[Path], batch_size: int = DEFAULT_BATCH_SIZE) -> List[List[Path]]:
    """
    Divide la lista de archivos en grupos más chicos.
    """
    return [
        files[index:index + batch_size]
        for index in range(0, len(files), batch_size)
    ]


def normalize_words(text: str) -> List[str]:
    """
    Limpia el texto y extrae palabras. Todo a minuscula, sin números ni caracteres especiales, y con al menos 2 letras.
    """
    words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    return words


def analyze_text(text: str) -> Dict:
    """
    Analiza un texto y calcula cantidad de palabras, líneas, caracteres y frecuencia de palabras.
    """
    lines = text.splitlines()
    words = normalize_words(text)

    return {
        "total_words": len(words),
        "total_lines": len(lines),
        "total_characters": len(text),
        "word_frequencies": Counter(words),
    }


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Genera un resumen básico tomando las 3 primeras frases del texto.
    """
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
) -> Dict:
    """
    Procesa todos los archivos .txt de la carpeta indicada.

    La función:
    - busca archivos
    - los divide en batches
    - calcula estadísticas por archivo
    - acumula resultados generales
    - devuelve un resumen final del proceso
    """
    if folder_path is None:
        folder_path = DEFAULT_TEXTS_FOLDER

    files = get_text_files(folder_path)

    if not files:
        raise FileNotFoundError("No se encontraron archivos para procesar")

    batches = split_into_batches(files, batch_size)
    total_words = 0
    total_lines = 0
    total_characters = 0
    global_word_frequencies = Counter()
    files_processed = []
    summaries = []

    for batch in batches:
        for file_path in batch:
            if file_path.suffix.lower() != ".txt":
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            try:
                analysis = analyze_text(text)
            except Exception:
                continue
            total_words += analysis["total_words"]
            total_lines += analysis["total_lines"]
            total_characters += analysis["total_characters"]
            global_word_frequencies.update(analysis["word_frequencies"])
            files_processed.append(file_path.name)
            summary = generate_summary(text)
            if summary:
                summaries.append(f"{file_path.name}: {summary}")

    most_frequent_words = [
        word
        for word, _ in global_word_frequencies.most_common(5)
    ]

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