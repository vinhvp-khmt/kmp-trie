"""Test cho phần MỞ RỘNG Aho-Corasick.

Điểm kiểm chứng quan trọng nhất: khi tập mẫu chỉ có MỘT phần tử, dãy failure
link của Aho-Corasick phải TRÙNG ĐÚNG với mảng LPS của KMP. Đây là bằng chứng
thực nghiệm cho khẳng định "Aho-Corasick tổng quát hóa hàm tiền tố của KMP" mà
báo cáo đưa ra — không chỉ nói bằng lời.
"""

from __future__ import annotations

import pytest

from src.kmp import AhoCorasick, build_lps, kmp_search
from tests.baseline import naive_multi_pattern_search


class TestAhoCorasickBasic:
    def test_classic_example(self):
        ac = AhoCorasick(["he", "she", "his", "hers"])
        got = [(m.start, m.pattern) for m in ac.search("ushers")]
        assert got == [(1, "she"), (2, "he"), (2, "hers")]

    def test_count_all_includes_zero_for_absent(self):
        ac = AhoCorasick(["he", "she", "his", "hers"])
        assert ac.count_all("ushers") == {
            "he": 1,
            "hers": 1,
            "his": 0,
            "she": 1,
        }

    def test_overlapping_patterns(self):
        ac = AhoCorasick(["aa", "aaa"])
        counts = ac.count_all("aaaa")
        assert counts["aa"] == 3
        assert counts["aaa"] == 2

    def test_one_pattern_contains_another(self):
        ac = AhoCorasick(["ab", "abab"])
        got = sorted((m.start, m.pattern) for m in ac.search("ababab"))
        assert got == [(0, "ab"), (0, "abab"), (2, "ab"), (2, "abab"), (4, "ab")]

    def test_duplicate_patterns(self):
        ac = AhoCorasick(["ab", "ab"])
        # Mẫu trùng: giữ chỉ số đầu tiên, không nhân đôi kết quả.
        assert len(ac.search("abab")) == 2

    def test_empty_pattern_list_rejected(self):
        with pytest.raises(ValueError):
            AhoCorasick([])

    def test_empty_pattern_rejected(self):
        with pytest.raises(ValueError):
            AhoCorasick(["ab", ""])

    def test_no_match(self):
        ac = AhoCorasick(["xyz"])
        assert ac.search("aaaa") == []

    def test_empty_text(self):
        ac = AhoCorasick(["a"])
        assert ac.search("") == []

    def test_pattern_longer_than_text(self):
        ac = AhoCorasick(["abcdef"])
        assert ac.search("abc") == []


class TestEquivalenceWithKMP:
    """Aho-Corasick với 1 mẫu ≡ KMP. Đây là mối liên hệ giữa 2 mô-đun."""

    @pytest.mark.parametrize(
        "pattern",
        ["a", "aa", "aba", "ababaca", "aabaabaaa", "abcabcabc", "mississippi"],
    )
    def test_failure_links_equal_lps(self, pattern):
        """fail(u).depth theo BFS ≡ mảng LPS.

        Với một mẫu, Trie là một đường thẳng nên thứ tự BFS chính là thứ tự
        chỉ số 0,1,...,m-1 của mẫu.
        """
        ac = AhoCorasick([pattern])
        assert ac.failure_array() == build_lps(pattern)

    @pytest.mark.parametrize(
        "text,pattern",
        [
            ("aaaa", "aa"),
            ("mississippi", "issi"),
            ("ababcabab", "abab"),
            ("abababab", "abab"),
            ("a" * 100, "a" * 7),
        ],
    )
    def test_single_pattern_positions_equal_kmp(self, text, pattern):
        ac = AhoCorasick([pattern])
        assert [m.start for m in ac.search(text)] == kmp_search(text, pattern)


class TestAgainstNaiveBaseline:
    CASES = [
        ("ushers", ["he", "she", "his", "hers"]),
        ("aaaa", ["a", "aa", "aaa"]),
        ("abcabcabc", ["abc", "bca", "cab", "zzz"]),
        ("mississippi", ["is", "si", "ssi", "ppi", "mi"]),
        ("banana", ["an", "na", "ana", "banana", "b"]),
    ]

    @pytest.mark.parametrize("text,patterns", CASES)
    def test_agrees_with_naive_per_pattern(self, text, patterns):
        ac = AhoCorasick(patterns)
        got = sorted((m.start, m.pattern) for m in ac.search(text))
        exp = sorted((s, p) for s, _, p in naive_multi_pattern_search(text, patterns))
        assert got == exp


class TestComplexity:
    def test_node_count_bounded_by_total_pattern_length(self):
        patterns = ["abc", "abd", "xyz"]
        ac = AhoCorasick(patterns)
        assert ac.num_nodes <= sum(len(p) for p in patterns) + 1

    def test_shared_prefixes_reduce_nodes(self):
        """Đây chính là lợi ích Trie mang lại cho Aho-Corasick."""
        shared = AhoCorasick(["abcd", "abce", "abcf"])
        distinct = AhoCorasick(["abcd", "wxyz", "mnop"])
        assert shared.num_nodes < distinct.num_nodes

    def test_beats_repeated_kmp_on_many_patterns(self):
        """Một lượt duyệt thay vì k lượt: so sánh số phép so sánh ký tự."""
        from src.common.metrics import OpCounter

        text = "abcabdabe" * 200
        patterns = [f"ab{c}" for c in "cdefghij"]

        c_ac = OpCounter()
        AhoCorasick(patterns).search(text, c_ac)

        c_kmp = OpCounter()
        for p in patterns:
            kmp_search(text, p, c_kmp)

        assert c_ac.char_comparisons < c_kmp.char_comparisons, (
            f"Aho-Corasick: {c_ac.char_comparisons}, "
            f"KMP lặp {len(patterns)} lần: {c_kmp.char_comparisons}"
        )
