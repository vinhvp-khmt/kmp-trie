"""TEST ĐỐI KHÁNG — sản phẩm bắt buộc theo đề.

Khác biệt giữa test biên và test đối kháng:
  - Test biên: các ca ở rìa miền xác định (rỗng, một phần tử, quá dài...).
  - Test đối kháng: dữ liệu được THIẾT KẾ CÓ CHỦ Ý để đánh vào điểm yếu của
    thuật toán — làm bộc lộ hành vi tệ nhất, hoặc phá vỡ giả thiết ngầm.

Mỗi ca dưới đây có một mục tiêu tấn công cụ thể, ghi rõ trong docstring.
"""

from __future__ import annotations

import pytest

from src.common.alphabet import ASCII_LOWER, BINARY
from src.common.metrics import OpCounter
from src.kmp import build_lps, kmp_search
from src.trie import Trie
from tests.baseline import naive_build_lps, naive_search


# =========================================================================== #
# Đối kháng với KMP
# =========================================================================== #
class TestKMPAdversarial:
    def test_worst_case_for_naive_all_same_character(self):
        """TẤN CÔNG: T = a^n, P = a^m — naive phải so sánh Θ(n·m) lần.

        Đây là ca chứng minh giá trị của KMP bằng số liệu, không bằng lời.
        """
        n, m = 20_000, 500
        text, pattern = "a" * n, "a" * m
        expected = list(range(n - m + 1))

        ck, cn = OpCounter(), OpCounter()
        assert kmp_search(text, pattern, ck) == expected
        assert naive_search(text, pattern, cn) == expected

        # KMP: ≤ 2n. Naive: ~ (n-m+1)·m.
        assert ck.char_comparisons <= 2 * n
        assert cn.char_comparisons > 20 * ck.char_comparisons

    def test_worst_case_pattern_almost_all_same(self):
        """TẤN CÔNG: P = a^(m-1) + 'b' trên T = a^n.

        Naive thất bại ở ký tự CUỐI mỗi lần thử — ca xấu nhất kinh điển. KMP
        vẫn tuyến tính. Kết quả đúng là rỗng.
        """
        n, m = 20_000, 200
        text, pattern = "a" * n, "a" * (m - 1) + "b"

        ck, cn = OpCounter(), OpCounter()
        assert kmp_search(text, pattern, ck) == []
        assert naive_search(text, pattern, cn) == []
        assert ck.char_comparisons <= 2 * n
        assert cn.char_comparisons > 30 * ck.char_comparisons

    def test_fibonacci_string_maximizes_border_chain(self):
        """TẤN CÔNG vào vòng while của KMP.

        Chuỗi Fibonacci có dãy biên dài nhất trong các chuỗi cùng độ dài, nên
        vòng `while` lùi theo π phải quay nhiều lần nhất. Nếu lập luận khấu hao
        sai, ca này sẽ làm số so sánh vượt 2n.
        """
        a, b = "a", "ab"
        for _ in range(18):
            a, b = b, b + a
        fib = b  # độ dài ~ 6765

        c = OpCounter()
        pattern = fib[: len(fib) // 3]
        result = kmp_search(fib, pattern, c)

        assert result == naive_search(fib, pattern)
        assert c.char_comparisons <= 2 * len(fib), (
            f"khấu hao bị vỡ: {c.char_comparisons} > 2·{len(fib)}"
        )
        # Dãy biên của mẫu Fibonacci phải dài (nhiều tầng lùi).
        from src.kmp import KMPMatcher

        assert len(KMPMatcher(pattern).borders()) >= 5

    def test_periodic_pattern_with_long_border(self):
        """TẤN CÔNG: mẫu có chu kỳ ⇒ π gần bằng m ở cuối.

        Nếu code đặt i ← 0 sau khi khớp (lỗi kinh điển) thì ca này sẽ THIẾU
        vị trí. Vì vậy đây là test bảo vệ Bổ đề 3.
        """
        pattern = "abab"
        text = "abab" * 500
        got = kmp_search(text, pattern)
        assert got == naive_search(text, pattern)
        # 2000 ký tự, mẫu dài 4, xuất hiện tại mọi vị trí chẵn.
        assert got == list(range(0, len(text) - 3, 2))
        assert len(got) == 999

    def test_lps_of_highly_repetitive_pattern(self):
        """TẤN CÔNG vào BUILD_LPS: mẫu lặp nhiều tầng."""
        for pattern in ["a" * 200, "ab" * 100, "aab" * 60, "aabaab" * 30]:
            assert build_lps(pattern) == naive_build_lps(pattern)

    def test_binary_alphabet_maximizes_partial_matches(self):
        """TẤN CÔNG: |Σ| = 2 ⇒ mật độ khớp một phần cao nhất."""
        import random

        rng = random.Random(20260728)
        text = "".join(rng.choice("ab") for _ in range(30_000))
        pattern = "".join(rng.choice("ab") for _ in range(12))

        c = OpCounter()
        assert kmp_search(text, pattern, c) == naive_search(text, pattern)
        assert c.char_comparisons <= 2 * len(text)

    def test_match_density_one_hundred_percent(self):
        """TẤN CÔNG: mọi vị trí đều khớp ⇒ nhánh `i == m` chạy mỗi bước."""
        text = "a" * 5000
        got = kmp_search(text, "a")
        assert got == list(range(5000))

    def test_pattern_is_entire_text_repeated(self):
        """Mẫu = văn bản ⇒ đúng một lần khớp tại 0, i = m ở bước cuối."""
        text = "abcdefghij" * 100
        assert kmp_search(text, text) == [0]

    def test_very_long_pattern_near_text_length(self):
        """m = n - 1: biên giữa 'có nghiệm' và 'quá dài'."""
        text = "a" * 1000 + "b"
        assert kmp_search(text, "a" * 1000) == [0]
        assert kmp_search(text, "a" * 1001) == []
        assert kmp_search(text, "a" * 1002) == []


# =========================================================================== #
# Đối kháng với Trie
# =========================================================================== #
class TestTrieAdversarial:
    def test_all_words_share_one_long_prefix(self):
        """TẤN CÔNG: mọi từ cùng tiền tố dài ⇒ cây suy biến thành 'cây chổi'.

        Mục tiêu: kiểm tra `_descend` không tuyến tính theo N, và autocomplete
        vẫn dừng sớm dù cây con chứa toàn bộ từ điển.
        """
        t = Trie(ASCII_LOWER)
        prefix = "a" * 100
        for i in range(2000):
            suffix = f"{i:04d}".translate(str.maketrans("0123456789", "abcdefghij"))
            t.insert(prefix + suffix)

        c_small = OpCounter()
        r = t.autocomplete(prefix, 5, c_small)
        assert len(r.suggestions) == 5
        assert r.truncated is True
        # Định vị tiền tố tốn 100 bước; phần thu kết quả phải rất nhỏ.
        assert c_small.nodes_visited < 100 + 200

    def test_single_chain_no_branching(self):
        """TẤN CÔNG: từ điển là dãy tiền tố lồng nhau a, aa, aaa, ...

        Cây là một đường thẳng, mọi nút đều is_end ⇒ autocomplete("") với k nhỏ
        phải dừng ngay, không đi hết chiều sâu.
        """
        t = Trie(ASCII_LOWER)
        for i in range(1, 2001):
            t.insert("a" * i)

        assert t.num_words == 2000
        assert t.num_nodes == 2001  # gốc + 2000

        c = OpCounter()
        r = t.autocomplete("", 3, c)
        assert r.suggestions == ["a", "aa", "aaa"]
        assert r.truncated is True
        assert c.nodes_visited <= 10, f"không dừng sớm: {c.nodes_visited}"

    def test_maximum_branching_at_root(self):
        """TẤN CÔNG: |Σ| nhánh ở gốc ⇒ chi phí sắp xếp con mỗi bước DFS."""
        t = Trie(ASCII_LOWER)
        for ch in ASCII_LOWER.chars:
            for i in range(20):
                t.insert(ch + "abcdefghijklmnopqrst"[i])
        r = t.autocomplete("", 5)
        # Thứ tự từ điển phải đúng dù có 26 nhánh.
        assert r.suggestions == sorted(r.suggestions)
        assert r.suggestions[0].startswith("a")

    def test_binary_alphabet_deep_dense_tree(self):
        """TẤN CÔNG: |Σ| = 2, mọi chuỗi độ dài 12 ⇒ cây nhị phân đầy 4096 lá."""
        t = Trie(BINARY)
        for i in range(4096):
            t.insert(format(i, "012b").translate(str.maketrans("01", "ab")))
        assert t.num_words == 4096
        # Cây đầy: 2^13 - 1 nút.
        assert t.num_nodes == 2 ** 13 - 1

        c = OpCounter()
        r = t.autocomplete("a", 3, c)
        assert r.suggestions == ["aaaaaaaaaaaa", "aaaaaaaaaaab", "aaaaaaaaaaba"]
        assert c.nodes_visited < 60

    def test_repeated_insert_of_same_word_many_times(self):
        """TẤN CÔNG vào bất biến I3/I4: insert 10 000 lần cùng một từ."""
        t = Trie(ASCII_LOWER)
        for _ in range(10_000):
            t.insert("stress")
        assert t.num_words == 1
        assert t.num_nodes == 7  # gốc + 6 ký tự
        assert t.count("stress") == 10_000
        assert t.count_with_prefix("str") == 10_000
        assert t.count_with_prefix("") == 10_000

    def test_pathologically_long_single_word(self):
        """TẤN CÔNG vào giới hạn đệ quy: từ dài 50 000 ký tự."""
        t = Trie(ASCII_LOWER)
        word = "z" * 50_000
        t.insert(word)
        assert t.search(word) is True
        assert t.max_depth() == 50_000
        # Nếu DFS dùng đệ quy Python, dòng dưới sẽ RecursionError.
        assert t.autocomplete("z", 1).suggestions == [word]

    def test_words_differing_only_at_last_character(self):
        """TẤN CÔNG: chia sẻ tối đa tiền tố ⇒ nodes_per_char rất nhỏ."""
        t = Trie(ASCII_LOWER)
        base = "abcdefghijklmnopqrst"
        for ch in ASCII_LOWER.chars:
            t.insert(base + ch)
        assert t.num_words == 26
        # gốc + 20 nút chung + 26 lá
        assert t.num_nodes == 1 + 20 + 26
        assert t.stats()["nodes_per_char"] < 0.15

    def test_invalid_character_deep_inside_long_word(self):
        """TẤN CÔNG: ký tự lạ ở vị trí cuối cùng của từ dài.

        Kiểm tra rằng việc từ chối xảy ra TRƯỚC khi tạo nút — nếu code kiểm tra
        từng ký tự trong lúc insert, cây sẽ bị bẩn khi lỗi xảy ra giữa đường.
        """
        t = Trie(ASCII_LOWER)
        nodes_before = t.num_nodes
        with pytest.raises(Exception):
            t.insert("a" * 999 + "1")
        assert t.num_nodes == nodes_before, "cây bị bẩn sau khi insert thất bại"
        assert t.num_words == 0


# =========================================================================== #
# Đối kháng chung: hai mô-đun cùng làm việc
# =========================================================================== #
class TestIntegrationAdversarial:
    def test_autocomplete_then_search_pipeline_on_pathological_data(self):
        """Luồng thật của hệ thống: gợi ý từ Trie ⇒ tìm bằng KMP.

        Dữ liệu bệnh lý: văn bản toàn 'a', từ điển toàn tiền tố của 'a'*k.
        """
        text = "a" * 10_000
        t = Trie(ASCII_LOWER)
        for i in range(1, 51):
            t.insert("a" * i)

        suggestion = t.autocomplete("aaa", 1).suggestions[0]
        assert suggestion == "aaa"

        c = OpCounter()
        positions = kmp_search(text, suggestion, c)
        assert len(positions) == 10_000 - 3 + 1
        assert c.char_comparisons <= 2 * len(text)
