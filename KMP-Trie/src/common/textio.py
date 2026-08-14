"""Đọc/ghi và chuẩn hóa dữ liệu.

Bước chuẩn hóa là một phần của **giả thiết G3** trong đề cương: từ điển được
chuẩn hóa trước khi insert, để tránh nhân bản nút Trie do khác biệt hình thức
("Tin", "tin ", "tin" phải là cùng một từ).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .alphabet import Alphabet, normalize_unicode

__all__ = [
    "normalize_text",
    "normalize_word",
    "read_text",
    "load_dictionary",
    "load_dictionary_with_freq",
    "tokenize",
    "write_json",
]


def normalize_text(text: str, *, lower: bool = True) -> str:
    """Chuẩn hóa văn bản: NFC + (tùy chọn) lowercase.

    KHÔNG loại ký tự lạ ở đây — KMP làm việc trên bảng chữ cái bất kỳ, việc
    lọc theo Σ là trách nhiệm của tầng Trie.
    """
    out = normalize_unicode(text)
    return out.lower() if lower else out


def normalize_word(word: str, *, lower: bool = True) -> str:
    """Chuẩn hóa một từ điển mục: NFC + strip + lowercase."""
    return normalize_text(word.strip(), lower=lower)


def read_text(path: str | Path, *, lower: bool = True) -> str:
    """Đọc toàn bộ tệp UTF-8 và chuẩn hóa."""
    raw = Path(path).read_text(encoding="utf-8")
    return normalize_text(raw, lower=lower)


def load_dictionary(
    path: str | Path,
    *,
    alphabet: Alphabet | None = None,
    lower: bool = True,
    skip_invalid: bool = False,
) -> list[str]:
    """Đọc từ điển: một từ mỗi dòng.

    Args:
        alphabet: nếu truyền, mọi từ được kiểm tra theo Σ.
        skip_invalid: False (mặc định) ⇒ ném lỗi ở từ vi phạm đầu tiên, đúng
            nguyên tắc "từ chối tường minh". True ⇒ bỏ qua và trả về, dùng khi
            làm sạch dữ liệu thô ở tầng script.

    Returns:
        Danh sách từ đã chuẩn hóa, giữ nguyên thứ tự xuất hiện, **giữ cả bản
        trùng** để tầng trên tự quyết định (Trie đếm được số lần insert).
    """
    words: list[str] = []
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            word = normalize_word(line, lower=lower)
            if not word:
                continue  # dòng trống bị loại (đã ghi trong README)
            if alphabet is not None:
                bad = alphabet.first_invalid(word)
                if bad is not None:
                    if skip_invalid:
                        continue
                    pos, ch = bad
                    raise ValueError(
                        f"{path}:{lineno}: từ {word!r} có ký tự {ch!r} tại vị trí "
                        f"{pos}, ngoài bảng chữ cái {alphabet.name!r}"
                    )
            words.append(word)
    return words


def load_dictionary_with_freq(
    path: str | Path, **kwargs
) -> list[tuple[str, int]]:
    """Như `load_dictionary` nhưng gộp trùng thành (từ, tần suất).

    Tần suất dùng cho phần mở rộng "xếp hạng gợi ý theo tần suất".
    """
    counts = Counter(load_dictionary(path, **kwargs))
    # Sắp xếp xác định: tần suất giảm, rồi từ tăng dần theo thứ tự từ điển.
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def tokenize(text: str, alphabet: Alphabet) -> list[str]:
    """Tách văn bản thành các token gồm ký tự thuộc Σ.

    Dùng để xây từ điển autocomplete trực tiếp từ một corpus.
    """
    tokens: list[str] = []
    current: list[str] = []
    for ch in text:
        if ch in alphabet:
            current.append(ch)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens


def write_json(path: str | Path, payload: object) -> None:
    """Ghi JSON UTF-8, thụt lề 2, giữ nguyên ký tự Unicode."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
