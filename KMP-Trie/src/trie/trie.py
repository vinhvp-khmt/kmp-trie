"""Mô-đun B — Cấu trúc Trie cho lưu và truy vấn theo tiền tố.

===============================================================================
PHÁT BIỂU BÀI TOÁN
===============================================================================
Vào : từ điển D = {w_1,...,w_N} trên bảng chữ cái Σ ĐƯỢC QUY ĐỊNH RÕ;
      tiền tố truy vấn q; số kết quả tối đa k.
Ra  : bốn thao tác bắt buộc theo đề —
        insert(w)              : thêm từ
        search(w) -> bool      : exact search
        starts_with(q) -> bool : prefix query
        autocomplete(q, k)     : ≤ k từ có tiền tố q
Ràng buộc: ký tự ngoài Σ bị TỪ CHỐI TƯỜNG MINH (không âm thầm bỏ qua).

Khác biệt bản chất so với KMP: Trie PHỤ THUỘC bảng chữ cái. |Σ| quyết định
cách lưu cạnh, hằng số bộ nhớ và chi phí duyệt. KMP thì không.

===============================================================================
BẤT BIẾN CẤU TRÚC
===============================================================================
I1. Mỗi nút biểu diễn ĐÚNG MỘT tiền tố: chuỗi nhãn trên đường đi từ gốc tới
    nút đó. Gốc biểu diễn tiền tố rỗng.
I2. node.is_end = True  ⟺  tiền tố mà node biểu diễn là một từ thuộc D.
I3. node.word_count = số lần từ đó đã được insert (≥ 0). is_end ⟺ word_count>0.
I4. node.prefix_count = tổng word_count của toàn bộ cây con gốc tại node
    = số lần insert của mọi từ có tiền tố này.
I5. Với mọi nút u và mọi ký tự c: u.children[c].parent_prefix = u_prefix + c.
    (Không lưu tường minh, nhưng được bảo toàn bởi cách duyệt.)

Mọi thao tác insert bảo toàn I1-I5: đường đi được tạo/đi lại đúng một lần,
prefix_count tăng 1 tại từng nút trên đường đi, word_count tăng 1 tại nút cuối.

===============================================================================
ĐỘ PHỨC TẠP
===============================================================================
Gọi L = |w| độ dài chuỗi, |Σ| kích thước bảng chữ cái, L_max độ dài từ dài nhất.

  insert(w)          : Θ(L) thời gian; tạo ≤ L nút mới
  search(w)          : Θ(L) — không phụ thuộc N (số từ)!
  starts_with(q)     : Θ(|q|)
  autocomplete(q,k)  : O(|q|) định vị + O(V·|Σ|log|Σ| + k·L_max), với V là
                       số nút thực sự duyệt. DFS DỪNG SỚM cho V = O(k·L_max)
                       khi cây con đủ dày; chặn trên là kích thước cây con.
  bộ nhớ             : O(tổng số ký tự phân biệt theo tiền tố) nút

So sánh với baseline duyệt tuyến tính: O(N · |q|). Trie thắng khi N lớn, vì
chi phí không phụ thuộc N. Đây là điểm sẽ được kiểm chứng bằng thực nghiệm.

Trade-off lưu cạnh (phải giải thích trong báo cáo):
  - dict (LỰA CHỌN CỦA NHÓM — đã chốt): bộ nhớ theo số con THỰC TẾ, truy cập O(1) khấu
    hao với hằng số hash. Phù hợp khi |Σ| lớn (tiếng Việt: |Σ| = 105) và cây
    thưa — đúng đặc tính của từ điển ngôn ngữ tự nhiên.
  - mảng |Σ| phần tử: truy cập O(1) hằng số nhỏ, nhưng mỗi nút tốn |Σ| ô ⇒
    với |Σ| = 105 và từ điển 10^5 từ thì lãng phí bộ nhớ rất lớn.
  Lớp `ArrayTrie` ở cuối tệp hiện thực biến thể mảng để so sánh thực nghiệm.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..common.alphabet import Alphabet, InvalidCharacterError
from ..common.metrics import OpCounter

__all__ = ["Trie", "TrieNode", "ArrayTrie", "AutocompleteResult"]


# --------------------------------------------------------------------------- #
# Kết quả
# --------------------------------------------------------------------------- #
@dataclass
class AutocompleteResult:
    """Kết quả autocomplete, khớp định dạng JSON đã khai báo trong README."""

    prefix: str
    suggestions: list[str] = field(default_factory=list)
    truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "prefix": self.prefix,
            "suggestions": self.suggestions,
            "truncated": self.truncated,
        }

    def __len__(self) -> int:
        return len(self.suggestions)


# --------------------------------------------------------------------------- #
# Nút
# --------------------------------------------------------------------------- #
class TrieNode:
    """Một nút Trie. `__slots__` để giảm bộ nhớ — quan trọng ở quy mô 10^6 nút."""

    __slots__ = ("children", "word_count", "prefix_count")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.word_count: int = 0    # I3
        self.prefix_count: int = 0  # I4

    @property
    def is_end(self) -> bool:
        """I2/I3: là cuối một từ ⟺ đã được insert ít nhất một lần."""
        return self.word_count > 0

    def __repr__(self) -> str:
        return (
            f"TrieNode(children={len(self.children)}, "
            f"word_count={self.word_count}, prefix_count={self.prefix_count})"
        )


# --------------------------------------------------------------------------- #
# Trie (lưu cạnh bằng dict)
# --------------------------------------------------------------------------- #
class Trie:
    """Trie hỗ trợ insert / exact search / prefix query / autocomplete.

    Args:
        alphabet: bảng chữ cái Σ. Nếu None, Trie nhận mọi ký tự — chế độ này
            CHỈ dùng cho thử nghiệm nội bộ; đề yêu cầu quy định rõ Σ nên mọi
            đường dùng chính thức đều truyền alphabet tường minh.

    >>> from src.common.alphabet import ASCII_LOWER
    >>> t = Trie(ASCII_LOWER)
    >>> for w in ["tin", "tinh", "toan", "to", "a"]: t.insert(w)
    >>> t.search("tin"), t.search("ti")
    (True, False)
    >>> t.starts_with("ti")
    True
    >>> t.autocomplete("t", 10).suggestions
    ['tin', 'tinh', 'to', 'toan']
    >>> r = t.autocomplete("t", 2)
    >>> r.suggestions, r.truncated
    (['tin', 'tinh'], True)
    """

    __slots__ = ("_root", "alphabet", "_num_nodes", "_num_words", "_total_inserts")

    def __init__(self, alphabet: Alphabet | None = None) -> None:
        self._root = TrieNode()
        self.alphabet = alphabet
        self._num_nodes = 1  # đếm cả gốc
        self._num_words = 0  # số từ PHÂN BIỆT
        self._total_inserts = 0

    # ------------------------------------------------------------------ #
    # Kiểm tra bảng chữ cái
    # ------------------------------------------------------------------ #
    def _validate(self, s: str) -> None:
        """Từ chối tường minh ký tự ngoài Σ (yêu cầu của đề)."""
        if self.alphabet is not None:
            self.alphabet.validate(s)

    # ------------------------------------------------------------------ #
    # Thao tác 1: insert
    # ------------------------------------------------------------------ #
    def insert(self, word: str, counter: OpCounter | None = None) -> None:
        """Thêm `word` vào từ điển.

        Bảo toàn I1-I4. Insert lại cùng một từ KHÔNG tạo nút mới, chỉ tăng
        word_count và prefix_count — đây là ca kiểm thử "từ trùng" của đề.

        Raises:
            ValueError: nếu `word` rỗng.
            InvalidCharacterError: nếu có ký tự ngoài Σ.

        Độ phức tạp: Θ(|word|).
        """
        if not word:
            raise ValueError("Không insert được từ rỗng vào từ điển")
        self._validate(word)

        node = self._root
        node.prefix_count += 1  # gốc = tiền tố rỗng, mọi từ đều có
        for ch in word:
            if counter is not None:
                counter.nodes_visited += 1
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = TrieNode()
                node.children[ch] = nxt
                self._num_nodes += 1
                if counter is not None:
                    counter.nodes_created += 1
            node = nxt
            node.prefix_count += 1  # I4

        if node.word_count == 0:
            self._num_words += 1
        node.word_count += 1  # I3
        self._total_inserts += 1

    def insert_many(self, words, counter: OpCounter | None = None) -> None:
        """Insert nhiều từ; bỏ qua dòng rỗng, KHÔNG bỏ qua ký tự lạ."""
        for w in words:
            if w:
                self.insert(w, counter)

    # ------------------------------------------------------------------ #
    # Định vị nút của một tiền tố
    # ------------------------------------------------------------------ #
    def _descend(
        self, prefix: str, counter: OpCounter | None = None
    ) -> TrieNode | None:
        """Đi từ gốc theo `prefix`; None nếu đường đi không tồn tại.

        Độ phức tạp: Θ(|prefix|).
        """
        node = self._root
        for ch in prefix:
            if counter is not None:
                counter.nodes_visited += 1
            nxt = node.children.get(ch)
            if nxt is None:
                return None
            node = nxt
        return node

    # ------------------------------------------------------------------ #
    # Thao tác 2: exact search
    # ------------------------------------------------------------------ #
    def search(self, word: str, counter: OpCounter | None = None) -> bool:
        """True ⟺ `word` là một từ trong D (không chỉ là tiền tố).

        Ký tự ngoài Σ ⇒ False (chứ không phải lỗi): truy vấn một từ không thể
        có trong từ điển là hợp lệ về mặt ngữ nghĩa, khác với INSERT.
        Quy ước này được ghi trong README và kiểm thử tường minh.

        Độ phức tạp: Θ(|word|) — KHÔNG phụ thuộc N.
        """
        if not word:
            return False
        if self.alphabet is not None and not self.alphabet.accepts(word):
            return False
        node = self._descend(word, counter)
        return node is not None and node.is_end

    def count(self, word: str) -> int:
        """Số lần `word` đã được insert (0 nếu không có)."""
        if not word:
            return 0
        node = self._descend(word)
        return node.word_count if node else 0

    # ------------------------------------------------------------------ #
    # Thao tác 3: prefix query
    # ------------------------------------------------------------------ #
    def starts_with(self, prefix: str, counter: OpCounter | None = None) -> bool:
        """True ⟺ có ít nhất một từ trong D bắt đầu bằng `prefix`.

        Tiền tố rỗng ⇒ True nếu từ điển không rỗng (quy ước tường minh).
        Độ phức tạp: Θ(|prefix|).
        """
        if self.alphabet is not None and not self.alphabet.accepts(prefix):
            return False
        if prefix == "":
            return self._num_words > 0
        return self._descend(prefix, counter) is not None

    def count_with_prefix(self, prefix: str) -> int:
        """Số lần insert của mọi từ có tiền tố `prefix` (dùng I4, O(|prefix|)).

        Nhờ prefix_count, đây là O(|prefix|) thay vì phải duyệt cả cây con.
        """
        if self.alphabet is not None and not self.alphabet.accepts(prefix):
            return 0
        node = self._descend(prefix)
        return node.prefix_count if node else 0

    # ------------------------------------------------------------------ #
    # Thao tác 4: autocomplete giới hạn số kết quả
    # ------------------------------------------------------------------ #
    def autocomplete(
        self, prefix: str, k: int = 10, counter: OpCounter | None = None
    ) -> AutocompleteResult:
        """Trả về tối đa `k` từ có tiền tố `prefix`.

        Thứ tự XÁC ĐỊNH: thứ tự từ điển (lexicographic) theo code point. Điều
        này quan trọng để test đối chiếu với baseline có kết quả so sánh được.

        DFS DỪNG SỚM: dừng ngay khi đã thu đủ k+1 kết quả, nên chi phí không
        phụ thuộc kích thước cây con khi cây con lớn — cờ `truncated` cho biết
        còn kết quả chưa trả về.

        Args:
            prefix: tiền tố; rỗng ⇒ trả k từ đầu tiên theo thứ tự từ điển.
            k: số kết quả tối đa; k = 0 ⇒ trả rỗng, truncated theo thực tế;
               k < 0 ⇒ ValueError.

        Gọi V là số nút thực sự duyệt. Thời gian là
        O(|prefix| + V·|Σ|log|Σ| + k·L_max): mỗi nút sắp tối đa |Σ| cạnh,
        và mỗi kết quả cần ghép tối đa L_max ký tự. Với bảng chữ cái cố định,
        phần duyệt là O(V + k·L_max). Bộ nhớ làm việc O(|Σ|·L_max) cho các
        frame DFS và đường đi, không tính danh sách kết quả.
        """
        if k < 0:
            raise ValueError("k phải ≥ 0")

        # Ký tự ngoài Σ ⇒ không thể có gợi ý; trả rỗng thay vì lỗi (như search).
        if self.alphabet is not None and not self.alphabet.accepts(prefix):
            return AutocompleteResult(prefix, [], False)

        node = self._descend(prefix, counter)
        if node is None:
            return AutocompleteResult(prefix, [], False)

        if k == 0:
            return AutocompleteResult(prefix, [], node.prefix_count > 0)

        out: list[str] = []
        # DFS tiền thứ tự bằng stack frame tường minh. `path` dùng chung cho
        # toàn bộ đường đi hiện tại nên không tạo một bản sao chuỗi ở mỗi cạnh.
        # Mỗi frame giữ iterator trên danh sách cạnh đã sắp tăng.
        path = list(prefix)
        stack: list[tuple[TrieNode, bool, object]] = [
            (node, False, iter(sorted(node.children)))
        ]
        truncated = False

        while stack:
            cur, entered, child_iter = stack[-1]

            if not entered:
                stack[-1] = (cur, True, child_iter)
                if counter is not None:
                    counter.nodes_visited += 1
                if cur.is_end:
                    if len(out) == k:
                        truncated = True  # còn ít nhất một kết quả nữa
                        break
                    out.append("".join(path))

            try:
                ch = next(child_iter)
            except StopIteration:
                stack.pop()
                if stack:
                    path.pop()
                continue

            child = cur.children[ch]
            path.append(ch)
            stack.append((child, False, iter(sorted(child.children))))

        return AutocompleteResult(prefix, out, truncated)

    def autocomplete_ranked(
        self, prefix: str, k: int = 10
    ) -> list[tuple[str, int]]:
        """MỞ RỘNG — xếp hạng gợi ý theo tần suất giảm dần.

        Không dừng sớm được (phải xem hết cây con để biết top-k), nên chi phí
        là O(|prefix| + |cây con|). Đây là ví dụ cho thấy yêu cầu "xếp hạng"
        làm mất tính chất dừng sớm — cần nêu trong báo cáo, không phóng đại.
        """
        node = self._descend(prefix)
        if node is None:
            return []
        found: list[tuple[str, int]] = []
        stack: list[tuple[TrieNode, str]] = [(node, prefix)]
        while stack:
            cur, word = stack.pop()
            if cur.is_end:
                found.append((word, cur.word_count))
            for ch in cur.children:
                stack.append((cur.children[ch], word + ch))
        found.sort(key=lambda kv: (-kv[1], kv[0]))
        return found[:k]

    # ------------------------------------------------------------------ #
    # Thống kê (cho phần thực nghiệm)
    # ------------------------------------------------------------------ #
    @property
    def num_nodes(self) -> int:
        """Số nút, kể cả gốc. Chỉ số bộ nhớ chính của Trie."""
        return self._num_nodes

    @property
    def num_words(self) -> int:
        """Số từ PHÂN BIỆT."""
        return self._num_words

    @property
    def total_inserts(self) -> int:
        return self._total_inserts

    def max_depth(self) -> int:
        """Độ sâu lớn nhất = độ dài từ dài nhất."""
        best = 0
        stack = [(self._root, 0)]
        while stack:
            node, d = stack.pop()
            if d > best:
                best = d
            for child in node.children.values():
                stack.append((child, d + 1))
        return best

    def stats(self) -> dict[str, int | float | str]:
        """Bảng thống kê để ghi vào kết quả thực nghiệm."""
        total_chars = sum(len(w) for w in self.keys())
        return {
            "alphabet": self.alphabet.name if self.alphabet else "unrestricted",
            "alphabet_size": len(self.alphabet) if self.alphabet else -1,
            "num_words": self._num_words,
            "total_inserts": self._total_inserts,
            "num_nodes": self._num_nodes,
            "max_depth": self.max_depth(),
            "total_chars_in_words": total_chars,
            # < 1.0 ⇒ Trie đang chia sẻ tiền tố, tiết kiệm so với lưu rời.
            "nodes_per_char": (
                self._num_nodes / total_chars if total_chars else 0.0
            ),
        }

    def keys(self) -> list[str]:
        """Toàn bộ từ trong D, theo thứ tự từ điển. O(tổng số ký tự)."""
        return self.autocomplete("", k=self._num_words or 1).suggestions

    def __len__(self) -> int:
        return self._num_words

    def __contains__(self, word: str) -> bool:
        return self.search(word)

    def __repr__(self) -> str:
        return (
            f"Trie(alphabet={self.alphabet.name if self.alphabet else None!r}, "
            f"num_words={self._num_words}, num_nodes={self._num_nodes})"
        )


# --------------------------------------------------------------------------- #
# Biến thể lưu cạnh bằng mảng — để SO SÁNH THỰC NGHIỆM
# --------------------------------------------------------------------------- #
class _ArrayNode:
    __slots__ = ("children", "word_count")

    def __init__(self, sigma: int) -> None:
        self.children: list[_ArrayNode | None] = [None] * sigma
        self.word_count = 0


class ArrayTrie:
    """Trie lưu cạnh bằng mảng |Σ| phần tử.

    Tồn tại để trả lời câu hỏi trade-off trong báo cáo bằng SỐ LIỆU chứ không
    bằng lời: cùng một từ điển, biến thể mảng dùng bao nhiêu ô so với dict?

    Truy cập cạnh là O(1) hằng số nhỏ (index vào list), nhưng mỗi nút cấp phát
    |Σ| ô ⇒ tổng ô = num_nodes × |Σ|, phần lớn là None (thưa).
    """

    __slots__ = ("_root", "alphabet", "_num_nodes", "_num_words")

    def __init__(self, alphabet: Alphabet) -> None:
        self.alphabet = alphabet
        self._root = _ArrayNode(len(alphabet))
        self._num_nodes = 1
        self._num_words = 0

    def insert(self, word: str) -> None:
        if not word:
            raise ValueError("Không insert được từ rỗng")
        self.alphabet.validate(word)
        sigma = len(self.alphabet)
        node = self._root
        for ch in word:
            i = self.alphabet.index[ch]
            nxt = node.children[i]
            if nxt is None:
                nxt = _ArrayNode(sigma)
                node.children[i] = nxt
                self._num_nodes += 1
            node = nxt
        if node.word_count == 0:
            self._num_words += 1
        node.word_count += 1

    def search(self, word: str) -> bool:
        if not word or not self.alphabet.accepts(word):
            return False
        node = self._root
        for ch in word:
            nxt = node.children[self.alphabet.index[ch]]
            if nxt is None:
                return False
            node = nxt
        return node.word_count > 0

    def autocomplete(self, prefix: str, k: int = 10) -> AutocompleteResult:
        if k < 0:
            raise ValueError("k phải ≥ 0")
        if not self.alphabet.accepts(prefix):
            return AutocompleteResult(prefix, [], False)
        node = self._root
        for ch in prefix:
            nxt = node.children[self.alphabet.index[ch]]
            if nxt is None:
                return AutocompleteResult(prefix, [], False)
            node = nxt
        out: list[str] = []
        truncated = False
        chars = self.alphabet.chars
        stack: list[tuple[_ArrayNode, str]] = [(node, prefix)]
        while stack:
            cur, word = stack.pop()
            if cur.word_count > 0:
                if len(out) == k:
                    truncated = True
                    break
                out.append(word)
            for i in range(len(chars) - 1, -1, -1):
                child = cur.children[i]
                if child is not None:
                    stack.append((child, word + chars[i]))
        return AutocompleteResult(prefix, out, truncated)

    @property
    def num_nodes(self) -> int:
        return self._num_nodes

    @property
    def num_slots(self) -> int:
        """Tổng số ô mảng đã cấp phát = num_nodes × |Σ|.

        Đây là con số cho thấy chi phí bộ nhớ thật của biến thể mảng.
        """
        return self._num_nodes * len(self.alphabet)

    def __len__(self) -> int:
        return self._num_words

    def __repr__(self) -> str:
        return (
            f"ArrayTrie(|Σ|={len(self.alphabet)}, num_words={self._num_words}, "
            f"num_nodes={self._num_nodes}, num_slots={self.num_slots})"
        )
