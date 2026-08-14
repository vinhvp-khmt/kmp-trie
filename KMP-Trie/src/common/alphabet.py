"""Quản lý bảng chữ cái (Σ) một cách tường minh.

Đề bài yêu cầu: "Mô-đun Trie phải ... quy định rõ bảng chữ cái."
Ký tự ngoài bảng chữ cái phải bị **từ chối tường minh**, không âm thầm bỏ qua.

Lưu ý về phạm vi áp dụng:
  - Trie PHỤ THUỘC bảng chữ cái: kích thước |Σ| quyết định cách lưu cạnh,
    hằng số bộ nhớ và chi phí duyệt cây con.
  - KMP KHÔNG phụ thuộc bảng chữ cái: thuật toán chỉ cần phép so sánh bằng
    giữa hai ký tự. Đây là một khác biệt bản chất giữa hai mô-đun và phải
    được nêu rõ trong báo cáo.
"""

from __future__ import annotations

import unicodedata

__all__ = [
    "Alphabet",
    "InvalidCharacterError",
    "ASCII_LOWER",
    "ASCII_LOWER_DIGITS",
    "VIETNAMESE_LOWER",
    "BINARY",
    "PRINTABLE_ASCII",
    "get_alphabet",
    "ALPHABETS",
]


class InvalidCharacterError(ValueError):
    """Ký tự không thuộc bảng chữ cái đã khai báo."""

    def __init__(self, char: str, position: int, alphabet_name: str) -> None:
        self.char = char
        self.position = position
        self.alphabet_name = alphabet_name
        super().__init__(
            f"Ký tự {char!r} (U+{ord(char):04X}) tại vị trí {position} "
            f"không thuộc bảng chữ cái {alphabet_name!r}"
        )


class Alphabet:
    """Một bảng chữ cái hữu hạn, được khai báo tường minh.

    Attributes:
        name: tên để ghi vào báo cáo và kết quả thực nghiệm.
        chars: tuple các ký tự hợp lệ, đã sắp xếp và loại trùng.
        index: ánh xạ ký tự -> chỉ số 0..|Σ|-1 (dùng cho biến thể lưu cạnh
            bằng mảng, và cho phần mở rộng hỗ trợ Unicode qua ánh xạ ký tự).
    """

    __slots__ = ("name", "chars", "index", "_charset")

    def __init__(self, name: str, chars: str) -> None:
        if not chars:
            raise ValueError("Bảng chữ cái không được rỗng")
        unique = sorted(set(chars))
        self.name = name
        self.chars: tuple[str, ...] = tuple(unique)
        self.index: dict[str, int] = {c: i for i, c in enumerate(unique)}
        self._charset = frozenset(unique)

    # ------------------------------------------------------------------ #
    # Truy vấn
    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        return len(self.chars)

    def __contains__(self, char: str) -> bool:
        return char in self._charset

    def __repr__(self) -> str:
        return f"Alphabet(name={self.name!r}, size={len(self.chars)})"

    def accepts(self, text: str) -> bool:
        """True nếu mọi ký tự của `text` đều thuộc Σ."""
        return all(c in self._charset for c in text)

    def validate(self, text: str) -> None:
        """Từ chối tường minh nếu có ký tự ngoài Σ.

        Raises:
            InvalidCharacterError: kèm ký tự và vị trí đầu tiên vi phạm.
        """
        for i, c in enumerate(text):
            if c not in self._charset:
                raise InvalidCharacterError(c, i, self.name)

    def first_invalid(self, text: str) -> tuple[int, str] | None:
        """Trả về (vị trí, ký tự) vi phạm đầu tiên, hoặc None nếu hợp lệ."""
        for i, c in enumerate(text):
            if c not in self._charset:
                return i, c
        return None

    def filter(self, text: str, replacement: str = "") -> str:
        """Loại/thay các ký tự ngoài Σ.

        CHỈ dùng ở tầng tiền xử lý dữ liệu thô (ví dụ làm sạch corpus tải về),
        KHÔNG dùng bên trong Trie: bên trong Trie phải từ chối tường minh.
        """
        return "".join(c if c in self._charset else replacement for c in text)


# ---------------------------------------------------------------------- #
# Các bảng chữ cái dùng trong đồ án
# ---------------------------------------------------------------------- #

#: |Σ| = 2 — dùng cho test đối kháng và test ngẫu nhiên: bảng chữ cái nhỏ làm
#: tần suất xuất hiện chồng lấn cao nhất, là ca xấu nhất cho baseline naive.
BINARY = Alphabet("binary", "ab")

#: |Σ| = 26 — bảng chữ cái Latin thường, dùng làm cấu hình chuẩn.
ASCII_LOWER = Alphabet("ascii_lower", "abcdefghijklmnopqrstuvwxyz")

#: |Σ| = 38 — mặc định của hệ thống: Latin thường + chữ số + dấu nối + dấu nháy.
ASCII_LOWER_DIGITS = Alphabet(
    "ascii_lower_digits", "abcdefghijklmnopqrstuvwxyz0123456789-'"
)

#: |Σ| = 105 — tiếng Việt thường có dấu, dùng cho demo trên dữ liệu tiếng Việt.
#: Đây là hiện thực của phần mở rộng "hỗ trợ Unicode bằng ánh xạ ký tự":
#: ta không giả thiết 1 byte = 1 ký tự, mà làm việc trên chuỗi Unicode đã
#: chuẩn hóa NFC, và Trie lưu cạnh theo code point.
VIETNAMESE_LOWER = Alphabet(
    "vietnamese_lower",
    "aàáảãạăằắẳẵặâầấẩẫậ"
    "bcdđ"
    "eèéẻẽẹêềếểễệ"
    "fgh"
    "iìíỉĩị"
    "jklmn"
    "oòóỏõọôồốổỗộơờớởỡợ"
    "pqrst"
    "uùúủũụưừứửữự"
    "vwx"
    "yỳýỷỹỵ"
    "z"
    "0123456789-'",
)

#: |Σ| = 95 — toàn bộ ASCII in được; dùng khi đo ảnh hưởng của |Σ| lớn.
PRINTABLE_ASCII = Alphabet(
    "printable_ascii", "".join(chr(c) for c in range(32, 127))
)

ALPHABETS: dict[str, Alphabet] = {
    a.name: a
    for a in (
        BINARY,
        ASCII_LOWER,
        ASCII_LOWER_DIGITS,
        VIETNAMESE_LOWER,
        PRINTABLE_ASCII,
    )
}


def get_alphabet(name: str) -> Alphabet:
    """Lấy bảng chữ cái theo tên; báo lỗi rõ ràng nếu không có."""
    try:
        return ALPHABETS[name]
    except KeyError:
        raise KeyError(
            f"Không có bảng chữ cái {name!r}. Các lựa chọn: "
            + ", ".join(sorted(ALPHABETS))
        ) from None


def normalize_unicode(text: str) -> str:
    """Chuẩn hóa NFC.

    Cần thiết vì "ê" có thể được biểu diễn bằng 1 code point (U+00EA) hoặc 2
    code point (e + U+0302). Nếu không chuẩn hóa, hai chuỗi "trông giống nhau"
    sẽ đi vào hai nhánh khác nhau của Trie — một lỗi khó phát hiện.
    """
    return unicodedata.normalize("NFC", text)
