"""文本/文件通用工具：字数统计、哈希、安全文件名。"""

import hashlib
import re


def count_words(text: str) -> int:
    return len(re.findall(r"\S", text))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_filename(name: str, fallback: str = "file") -> str:
    cleaned = "".join(c for c in name if c not in '<>:"/\\|?*').strip()
    return cleaned or fallback
