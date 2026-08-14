"""Test cơ bản và test biên cho mô-đun B (Trie)."""

from __future__ import annotations

import pytest

from src.common.alphabet import (
    ASCII_LOWER,
    ASCII_LOWER_DIGITS,
    VIETNAMESE_LOWER,
    InvalidCharacterError,
)
from src.common.metrics import OpCounter
from src.trie import ArrayTrie, Trie
from tests.baseline import (
    linear_autocomplete,
    linear_search_word,
    linear_starts_with,
)

WORDS = ["tin", "tinh", "toan", "to", "a", "an", "and", "ant", "banana"]


@pytest.fixture
def trie() -> Trie:
    t = Trie(ASCII_LOWER)
    t.insert_many(WORDS)
    return t


# =========================================================================== #
# 1. Bốn thao tác bắt buộc
# =========================================================================== #
class TestRequiredOperations:
    def test_insert_and_exact_search(self, trie):
        for w in WORDS:
            assert trie.search(w) is True

    def test_exact_search_rejects_prefixes(self, trie):
        """Điểm khác nhau giữa exact search và prefix query."""
        assert trie.search("ti") is False   # là tiền tố, không phải từ
        assert trie.search("ban") is False
        assert trie.starts_with("ti") is True
        assert trie.starts_with("ban") is True

    def test_prefix_query(self, trie):
        assert trie.starts_with("t") is True
        assert trie.starts_with("tin") is True
        assert trie.starts_with("z") is False
        assert trie.starts_with("tinhx") is False

    def test_autocomplete_returns_lexicographic_order(self, trie):
        r = trie.autocomplete("t", 10)
        assert r.suggestions == ["tin", "tinh", "to", "toan"]
        assert r.truncated is False

    def test_autocomplete_respects_k(self, trie):
        r = trie.autocomplete("t", 2)
        assert r.suggestions == ["tin", "tinh"]
        assert r.truncated is True

    def test_autocomplete_json_shape(self, trie):
        d = trie.autocomplete("to", 10).to_dict()
        assert d == {
            "prefix": "to",
            "suggestions": ["to", "toan"],
            "truncated": False,
        }


# =========================================================================== #
# 2. TEST BIÊN (đề liệt kê tường minh từng ca dưới đây)
# =========================================================================== #
class TestTrieEdgeCases:
    def test_duplicate_words_do_not_duplicate_nodes(self):
        """Ca biên của đề: "từ trùng"."""
        t = Trie(ASCII_LOWER)
        t.insert("tin")
        nodes_after_first = t.num_nodes
        t.insert("tin")
        t.insert("tin")
        assert t.num_nodes == nodes_after_first, "insert lại không được tạo nút mới"
        assert t.num_words == 1, "số từ PHÂN BIỆT vẫn là 1"
        assert t.count("tin") == 3, "nhưng đếm được 3 lần insert"
        assert t.total_inserts == 3

    def test_word_is_prefix_of_another(self):
        """Ca biên của đề: "một từ là tiền tố của từ khác"."""
        t = Trie(ASCII_LOWER)
        t.insert("tin")
        t.insert("tinh")
        assert t.search("tin") is True, "từ ngắn không bị từ dài che mất"
        assert t.search("tinh") is True
        assert t.autocomplete("tin", 10).suggestions == ["tin", "tinh"]

    def test_insert_long_then_short(self):
        """Thứ tự insert ngược lại cũng phải đúng."""
        t = Trie(ASCII_LOWER)
        t.insert("tinh")
        t.insert("tin")
        assert t.search("tin") is True
        assert t.search("tinh") is True

    def test_empty_prefix_returns_first_k(self, trie):
        """Ca biên của đề: "tiền tố rỗng"."""
        r = trie.autocomplete("", 3)
        assert r.suggestions == ["a", "an", "and"]
        assert r.truncated is True
        assert trie.starts_with("") is True

    def test_empty_prefix_on_empty_trie(self):
        t = Trie(ASCII_LOWER)
        assert t.starts_with("") is False
        assert t.autocomplete("", 5).suggestions == []

    def test_character_outside_alphabet_rejected_on_insert(self):
        """Ca biên của đề: "ký tự ngoài bảng chữ cái" ⇒ TỪ CHỐI TƯỜNG MINH."""
        t = Trie(ASCII_LOWER)
        with pytest.raises(InvalidCharacterError) as exc:
            t.insert("tin1")
        assert exc.value.char == "1"
        assert exc.value.position == 3
        assert exc.value.alphabet_name == "ascii_lower"

    def test_character_outside_alphabet_on_query_returns_falsy(self, trie):
        """Truy vấn (khác insert) trả về rỗng/False, không ném lỗi."""
        assert trie.search("tin1") is False
        assert trie.starts_with("tin1") is False
        assert trie.autocomplete("tin1", 5).suggestions == []

    def test_insert_empty_word_rejected(self):
        t = Trie(ASCII_LOWER)
        with pytest.raises(ValueError, match="rỗng"):
            t.insert("")

    def test_search_empty_word(self, trie):
        assert trie.search("") is False

    def test_nonexistent_prefix(self, trie):
        r = trie.autocomplete("zzz", 5)
        assert r.suggestions == []
        assert r.truncated is False

    def test_k_zero(self, trie):
        r = trie.autocomplete("t", 0)
        assert r.suggestions == []
        assert r.truncated is True, "có kết quả nhưng bị cắt hết"

    def test_k_negative_rejected(self, trie):
        with pytest.raises(ValueError, match="k phải"):
            trie.autocomplete("t", -1)

    def test_k_larger_than_available(self, trie):
        r = trie.autocomplete("ban", 1000)
        assert r.suggestions == ["banana"]
        assert r.truncated is False

    def test_very_long_word_no_recursion_error(self):
        """DFS dùng stack tường minh ⇒ không vỡ với từ rất dài."""
        t = Trie(ASCII_LOWER)
        long_word = "a" * 5000
        t.insert(long_word)
        assert t.search(long_word) is True
        assert t.max_depth() == 5000
        assert t.autocomplete("a" * 4999, 5).suggestions == [long_word]


# =========================================================================== #
# 3. Bất biến cấu trúc
# =========================================================================== #
class TestInvariants:
    def test_prefix_count_equals_subtree_sum(self, trie):
        """I4: prefix_count = tổng word_count của cây con."""
        for prefix in ["", "t", "ti", "tin", "a", "an", "ban"]:
            expected = sum(
                trie.count(w) for w in trie.keys() if w.startswith(prefix)
            )
            assert trie.count_with_prefix(prefix) == expected, prefix

    def test_is_end_iff_word_count_positive(self, trie):
        """I2/I3."""
        for w in trie.keys():
            assert trie.count(w) > 0
            assert trie.search(w) is True

    def test_keys_are_sorted_and_complete(self, trie):
        keys = trie.keys()
        assert keys == sorted(set(WORDS))
        assert len(keys) == trie.num_words

    def test_num_nodes_bounded_by_total_chars_plus_root(self):
        """Số nút ≤ tổng ký tự + 1; nhỏ hơn khi có tiền tố chung."""
        t = Trie(ASCII_LOWER)
        words = ["abc", "abd", "abe"]
        t.insert_many(words)
        assert t.num_nodes <= sum(len(w) for w in words) + 1

    def test_shared_prefix_saves_nodes(self):
        t = Trie(ASCII_LOWER)
        t.insert_many(["abc", "abd", "abe"])
        # gốc + a + b + c + d + e = 6 nút, thay vì 1 + 9 = 10 nếu lưu rời.
        assert t.num_nodes == 6
        assert t.stats()["nodes_per_char"] < 1.0


# =========================================================================== #
# 4. Đối chiếu với baseline duyệt tuyến tính
# =========================================================================== #
class TestTrieAgainstBaseline:
    PREFIXES = ["", "a", "an", "b", "t", "ti", "tin", "to", "z", "banana", "ba"]

    @pytest.mark.parametrize("prefix", PREFIXES)
    @pytest.mark.parametrize("k", [1, 2, 3, 5, 100])
    def test_autocomplete_agrees_with_linear(self, trie, prefix, k):
        got = trie.autocomplete(prefix, k)
        exp_words, exp_trunc = linear_autocomplete(WORDS, prefix, k)
        assert got.suggestions == exp_words
        assert got.truncated == exp_trunc

    @pytest.mark.parametrize(
        "word", WORDS + ["ti", "zzz", "banan", "bananas", ""]
    )
    def test_search_agrees_with_linear(self, trie, word):
        assert trie.search(word) == linear_search_word(WORDS, word)

    @pytest.mark.parametrize("prefix", PREFIXES)
    def test_starts_with_agrees_with_linear(self, trie, prefix):
        assert trie.starts_with(prefix) == linear_starts_with(WORDS, prefix)


# =========================================================================== #
# 5. Dừng sớm của DFS — chứng thực bằng bộ đếm
# =========================================================================== #
class TestEarlyStop:
    def test_nodes_visited_scales_with_k_not_subtree_size(self):
        """k nhỏ ⇒ duyệt ít nút, dù cây con rất lớn."""
        t = Trie(ASCII_LOWER)
        # 5000 từ cùng tiền tố "x" ⇒ cây con khổng lồ.
        for i in range(5000):
            t.insert("x" + f"{i:05d}".translate(str.maketrans("0123456789", "abcdefghij")))

        c_small, c_large = OpCounter(), OpCounter()
        t.autocomplete("x", 5, c_small)
        t.autocomplete("x", 5000, c_large)
        assert c_small.nodes_visited < c_large.nodes_visited / 50, (
            f"dừng sớm không hiệu lực: {c_small.nodes_visited} vs "
            f"{c_large.nodes_visited}"
        )

    def test_search_cost_independent_of_dictionary_size(self):
        """Θ(L), không phụ thuộc N — điểm mạnh cốt lõi của Trie."""
        counts = []
        for n in (100, 1000, 10000):
            t = Trie(ASCII_LOWER)
            for i in range(n):
                t.insert("w" + f"{i:06d}".translate(str.maketrans("0123456789", "abcdefghij")))
            c = OpCounter()
            t.search("waaaaaa", c)
            counts.append(c.nodes_visited)
        assert len(set(counts)) == 1, f"chi phí phải bằng nhau: {counts}"


# =========================================================================== #
# 6. Unicode / tiếng Việt
# =========================================================================== #
class TestVietnamese:
    def test_vietnamese_autocomplete(self):
        t = Trie(VIETNAMESE_LOWER)
        for w in ["tính", "tình", "tin", "tiền", "toán", "tối"]:
            t.insert(w)
        r = t.autocomplete("tí", 10)
        assert r.suggestions == ["tính"]
        assert t.search("tình") is True
        assert t.search("tinh") is False, "dấu là ký tự khác ⇒ từ khác"

    def test_nfc_normalization_prevents_duplicate_branches(self):
        """Mở rộng Unicode: 'ê' dạng tổ hợp và dạng dựng sẵn phải là một."""
        from src.common.textio import normalize_word

        composed = "ê"          # ê dựng sẵn
        decomposed = "ê"       # e + dấu mũ
        assert normalize_word(composed) == normalize_word(decomposed)


# =========================================================================== #
# 7. Biến thể lưu cạnh bằng mảng — trade-off bộ nhớ
# =========================================================================== #
class TestArrayTrie:
    def test_same_results_as_dict_trie(self):
        d, a = Trie(ASCII_LOWER), ArrayTrie(ASCII_LOWER)
        for w in WORDS:
            d.insert(w)
            a.insert(w)
        assert d.num_nodes == a.num_nodes, "cùng cấu trúc cây"
        for prefix in ["", "t", "ti", "a", "z"]:
            assert (
                d.autocomplete(prefix, 10).suggestions
                == a.autocomplete(prefix, 10).suggestions
            )
        for w in WORDS + ["ti", "zz"]:
            assert d.search(w) == a.search(w)

    def test_array_variant_allocates_sigma_slots_per_node(self):
        """Số liệu cho phần trade-off trong báo cáo."""
        a = ArrayTrie(ASCII_LOWER)
        for w in WORDS:
            a.insert(w)
        assert a.num_slots == a.num_nodes * 26
        assert a.num_slots > a.num_nodes * 10, "phần lớn ô là None ⇒ thưa"

    def test_array_variant_rejects_negative_k(self):
        """Hai biến thể Trie phải có cùng hợp đồng cho k không hợp lệ."""
        a = ArrayTrie(ASCII_LOWER)
        a.insert("tin")
        with pytest.raises(ValueError, match="k phải"):
            a.autocomplete("t", -1)


# =========================================================================== #
# 8. Thống kê
# =========================================================================== #
def test_stats_reports_all_fields(trie):
    s = trie.stats()
    for key in (
        "alphabet",
        "alphabet_size",
        "num_words",
        "total_inserts",
        "num_nodes",
        "max_depth",
        "nodes_per_char",
    ):
        assert key in s
    assert s["alphabet"] == "ascii_lower"
    assert s["alphabet_size"] == 26
    assert s["max_depth"] == 6  # "banana"


def test_alphabet_default_is_explicit():
    """Đề yêu cầu quy định RÕ bảng chữ cái ⇒ mặc định của hệ thống phải có tên."""
    t = Trie(ASCII_LOWER_DIGITS)
    assert t.alphabet is not None
    assert len(t.alphabet) == 38
