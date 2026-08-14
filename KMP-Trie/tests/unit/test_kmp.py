"""Test cơ bản và test biên cho mô-đun A (KMP)."""

from __future__ import annotations

import pytest

from src.common.metrics import OpCounter
from src.kmp import KMPMatcher, build_lps, kmp_count, kmp_find_first, kmp_search
from tests.baseline import builtin_search, naive_build_lps, naive_search


# =========================================================================== #
# 1. LPS — test cơ bản
# =========================================================================== #
class TestBuildLPS:
    @pytest.mark.parametrize(
        "pattern,expected",
        [
            ("", []),
            ("a", [0]),
            ("ab", [0, 0]),
            ("aa", [0, 1]),
            ("aaaa", [0, 1, 2, 3]),
            ("abcd", [0, 0, 0, 0]),
            ("ababaca", [0, 0, 1, 2, 3, 0, 1]),
            ("aabaabaaa", [0, 1, 0, 1, 2, 3, 4, 5, 2]),
            ("abcabcabc", [0, 0, 0, 1, 2, 3, 4, 5, 6]),
            ("aabaaab", [0, 1, 0, 1, 2, 2, 3]),
        ],
        ids=lambda v: repr(v)[:24],
    )
    def test_known_values(self, pattern, expected):
        """Các giá trị tính tay, có trong đề cương và báo cáo."""
        assert build_lps(pattern) == expected

    @pytest.mark.parametrize(
        "pattern",
        ["a", "aa", "ab", "aab", "abab", "ababaca", "aabaabaaa", "mississippi"],
    )
    def test_matches_definition_baseline(self, pattern):
        """Đối chiếu với bản O(m^3) dịch trực tiếp từ định nghĩa."""
        assert build_lps(pattern) == naive_build_lps(pattern)

    def test_lps_invariant_is_proper_border(self):
        """Bất biến: π[i] < i+1 và P[:π[i]] == P[i+1-π[i]:i+1]."""
        pattern = "abababcabababcab"
        lps = build_lps(pattern)
        for i, length in enumerate(lps):
            assert length < i + 1, "biên phải THẬT SỰ (ngắn hơn chuỗi)"
            if length:
                s = pattern[: i + 1]
                assert s[:length] == s[-length:]

    def test_lps_grows_by_at_most_one(self):
        """π[i] ≤ π[i-1] + 1 — cơ sở của lập luận khấu hao."""
        lps = build_lps("aabaabaaabaab")
        for i in range(1, len(lps)):
            assert lps[i] <= lps[i - 1] + 1


# =========================================================================== #
# 2. KMP — test cơ bản
# =========================================================================== #
class TestKMPBasic:
    @pytest.mark.parametrize(
        "text,pattern,expected",
        [
            ("abc", "a", [0]),
            ("abc", "b", [1]),
            ("abc", "c", [2]),
            ("abc", "abc", [0]),
            ("abcabc", "abc", [0, 3]),
            ("ababcabab", "abab", [0, 5]),
            ("mississippi", "issi", [1, 4]),
            ("mississippi", "ss", [2, 5]),
            ("aaaaa", "aaa", [0, 1, 2]),
            ("abababab", "abab", [0, 2, 4]),
        ],
    )
    def test_known_positions(self, text, pattern, expected):
        assert kmp_search(text, pattern) == expected

    def test_finds_overlapping_occurrences(self):
        """Yêu cầu tường minh của đề: PHẢI bắt được xuất hiện chồng lấn."""
        assert kmp_search("aaaa", "aa") == [0, 1, 2]
        assert kmp_search("aaaaaa", "aaa") == [0, 1, 2, 3]
        assert kmp_search("abababa", "aba") == [0, 2, 4]

    def test_non_overlapping_mode(self):
        """Chế độ không chồng lấn, để so với str.find bước m."""
        assert kmp_search("aaaa", "aa", overlapping=False) == [0, 2]
        assert kmp_search("aaaaa", "aa", overlapping=False) == [0, 2]
        assert kmp_search("abababa", "aba", overlapping=False) == [0, 4]

    def test_count_and_find_first(self):
        assert kmp_count("aaaa", "aa") == 3
        assert kmp_find_first("aaaa", "aa") == 0
        assert kmp_find_first("abc", "zz") == -1
        assert kmp_find_first("hello world", "world") == 6


# =========================================================================== #
# 3. KMP — TEST BIÊN (đề yêu cầu tường minh từng ca dưới đây)
# =========================================================================== #
class TestKMPEdgeCases:
    def test_pattern_longer_than_text(self):
        """Ca biên của đề: "mẫu dài hơn văn bản" ⇒ rỗng, KHÔNG lỗi."""
        assert kmp_search("abc", "abcd") == []
        assert kmp_search("a", "aa") == []
        assert kmp_search("", "a") == []

    def test_empty_pattern_rejected_explicitly(self):
        """Quy ước hệ thống: mẫu rỗng bị từ chối tường minh, không im lặng."""
        with pytest.raises(ValueError, match="Mẫu rỗng"):
            kmp_search("abc", "")
        with pytest.raises(ValueError, match="Mẫu rỗng"):
            kmp_count("abc", "")
        with pytest.raises(ValueError):
            KMPMatcher("")

    def test_empty_text(self):
        assert kmp_search("", "abc") == []

    def test_pattern_equals_text(self):
        assert kmp_search("abc", "abc") == [0]
        assert kmp_search("a", "a") == [0]

    def test_pattern_not_present(self):
        """Ca biên của đề: "không xuất hiện"."""
        assert kmp_search("abcabcabc", "abd") == []
        assert kmp_search("a" * 100, "b") == []
        assert kmp_search("a" * 100, "ab") == []

    def test_single_character_alphabet(self):
        assert kmp_search("a" * 10, "a") == list(range(10))

    def test_match_at_very_end(self):
        assert kmp_search("xxxabc", "abc") == [3]

    def test_match_at_very_start(self):
        assert kmp_search("abcxxx", "abc") == [0]

    def test_unicode_vietnamese(self):
        """KMP không phụ thuộc bảng chữ cái ⇒ phải chạy đúng trên Unicode."""
        text = "tính toán tối ưu và tính khả thi"
        assert kmp_search(text, "tính") == [0, 20]
        assert kmp_search(text, "tối") == [10]


# =========================================================================== #
# 4. Đối chiếu với hai baseline độc lập
# =========================================================================== #
class TestKMPAgainstBaselines:
    CASES = [
        ("aaaa", "aa"),
        ("mississippi", "issi"),
        ("ababcabab", "abab"),
        ("abcdefghij", "def"),
        ("a" * 50, "a" * 10),
        ("ab" * 30, "aba"),
        ("aab" * 20, "aabaab"),
        ("xyz" * 10, "zxy"),
    ]

    @pytest.mark.parametrize("text,pattern", CASES)
    def test_agrees_with_naive(self, text, pattern):
        assert kmp_search(text, pattern) == naive_search(text, pattern)

    @pytest.mark.parametrize("text,pattern", CASES)
    def test_agrees_with_builtin_nonoverlapping(self, text, pattern):
        """str.find dùng thuật toán khác hoàn toàn ⇒ đối chiếu độc lập thứ hai."""
        assert kmp_search(text, pattern, overlapping=False) == builtin_search(
            text, pattern, overlapping=False
        )

    @pytest.mark.parametrize("text,pattern", CASES)
    def test_agrees_with_builtin_overlapping(self, text, pattern):
        assert kmp_search(text, pattern) == builtin_search(text, pattern)


# =========================================================================== #
# 5. KMPMatcher — tái sử dụng π
# =========================================================================== #
class TestKMPMatcher:
    def test_reuse_across_texts(self):
        m = KMPMatcher("aba")
        assert m.search("abababa") == [0, 2, 4]
        assert m.search("xyz") == []
        assert m.search("aba") == [0]

    def test_lps_exposed(self):
        """Đề yêu cầu mô-đun KMP phải SINH RA LPS, không ẩn nó đi."""
        assert KMPMatcher("ababaca").lps == [0, 0, 1, 2, 3, 0, 1]

    def test_result_json_shape(self):
        d = KMPMatcher("aa").result("aaaa").to_dict()
        assert d == {"pattern": "aa", "positions": [0, 1, 2], "count": 3}

    def test_borders_chain(self):
        """Dãy biên giảm dần — dùng để minh họa trong slide."""
        # "abaaba" có các biên "aba" (3), "a" (1), "" (0).
        assert KMPMatcher("abaaba").borders() == [3, 1, 0]
        assert KMPMatcher("aaaa").borders() == [3, 2, 1, 0]
        assert KMPMatcher("abcd").borders() == [0]


# =========================================================================== #
# 6. Bộ đếm thao tác — chứng thực phân tích độ phức tạp
# =========================================================================== #
class TestOperationCounts:
    def test_kmp_comparisons_bounded_by_2n(self):
        """Hệ quả của lập luận khấu hao: số so sánh ≤ 2n (và ≤ 2m khi xây π)."""
        for text, pattern in [
            ("a" * 1000, "a" * 10),
            ("ab" * 500, "aab"),
            ("abc" * 300, "cab"),
        ]:
            c = OpCounter()
            kmp_search(text, pattern, c)
            assert c.char_comparisons <= 2 * len(text)
            assert c.lps_comparisons <= 2 * len(pattern)

    def test_kmp_beats_naive_on_adversarial_input(self):
        """Trên ca xấu nhất của naive, KMP phải ít so sánh hơn HẲN."""
        text = "a" * 2000
        pattern = "a" * 100
        ck, cn = OpCounter(), OpCounter()
        kmp_search(text, pattern, ck)
        naive_search(text, pattern, cn)
        assert ck.char_comparisons < cn.char_comparisons / 10

    def test_comparison_ratio_stays_constant(self):
        """comparisons/n bị chặn bởi hằng số khi n tăng ⇒ tuyến tính."""
        ratios = []
        for size in (1000, 2000, 4000, 8000):
            c = OpCounter()
            kmp_search("ab" * (size // 2), "aab", c)
            ratios.append(c.char_comparisons / size)
        assert max(ratios) / min(ratios) < 1.2, f"tỉ số trôi: {ratios}"
