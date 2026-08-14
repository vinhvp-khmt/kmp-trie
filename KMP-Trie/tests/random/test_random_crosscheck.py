"""TEST NGẪU NHIÊN ĐỐI CHIẾU — sản phẩm bắt buộc theo đề.

Nguyên tắc: sinh hàng nghìn ca ngẫu nhiên, chạy cả cài đặt tối ưu và baseline
ngây thơ, yêu cầu kết quả TRÙNG KHỚP TUYỆT ĐỐI.

SEED CỐ ĐỊNH (SEED = 20260728) — checklist của đề yêu cầu "số liệu tái lập
được". Nếu một ca thất bại, có thể tái tạo chính xác ca đó.

Bảng chữ cái nhỏ (|Σ| = 2, 3) được ưu tiên vì chúng làm tăng mạnh tần suất
khớp một phần và khớp chồng lấn — đúng những chỗ dễ sai nhất.
"""

from __future__ import annotations

import random

import pytest

from src.common.alphabet import ASCII_LOWER, BINARY, Alphabet
from src.common.metrics import OpCounter
from src.kmp import AhoCorasick, build_lps, kmp_search
from src.trie import ArrayTrie, Trie
from tests.baseline import (
    builtin_search,
    linear_autocomplete,
    linear_search_word,
    linear_starts_with,
    naive_build_lps,
    naive_multi_pattern_search,
    naive_search,
)

SEED = 20260728
TERNARY = Alphabet("ternary", "abc")


def _rand_string(rng: random.Random, alphabet: str, length: int) -> str:
    return "".join(rng.choice(alphabet) for _ in range(length))


# =========================================================================== #
# 1. KMP đối chiếu naive — số lượng lớn
# =========================================================================== #
@pytest.mark.parametrize("sigma", ["ab", "abc", "abcdefghij"], ids=["S2", "S3", "S10"])
def test_kmp_matches_naive_random(sigma):
    """3 000 ca / bảng chữ cái. Bảng nhỏ ⇒ nhiều chồng lấn ⇒ test khắt khe hơn."""
    rng = random.Random(SEED + len(sigma))
    for case in range(3000):
        n = rng.randint(0, 60)
        m = rng.randint(1, 12)
        text = _rand_string(rng, sigma, n)
        pattern = _rand_string(rng, sigma, m)

        got = kmp_search(text, pattern)
        exp = naive_search(text, pattern)
        assert got == exp, (
            f"seed={SEED + len(sigma)} case={case} "
            f"text={text!r} pattern={pattern!r}: {got} != {exp}"
        )


def test_kmp_matches_naive_with_planted_occurrences():
    """Cấy sẵn mẫu vào văn bản để bảo đảm tỉ lệ ca CÓ nghiệm đủ cao.

    Sinh hoàn toàn ngẫu nhiên trên bảng chữ cái lớn thì phần lớn ca là rỗng,
    khiến test yếu. Ở đây ta chủ động cấy 1-5 lần xuất hiện, có thể chồng lấn.
    """
    rng = random.Random(SEED + 99)
    for case in range(2000):
        pattern = _rand_string(rng, "abc", rng.randint(1, 8))
        parts = [_rand_string(rng, "abc", rng.randint(0, 6))]
        for _ in range(rng.randint(1, 5)):
            parts.append(pattern)
            parts.append(_rand_string(rng, "abc", rng.randint(0, 4)))
        text = "".join(parts)

        got = kmp_search(text, pattern)
        exp = naive_search(text, pattern)
        assert got == exp, f"case={case} text={text!r} pattern={pattern!r}"
        assert len(got) >= 1, "đã cấy nên phải tìm được"


def test_kmp_matches_builtin_random():
    """Đối chiếu độc lập THỨ HAI: str.find của CPython (thuật toán khác hẳn)."""
    rng = random.Random(SEED + 7)
    for _ in range(2000):
        text = _rand_string(rng, "abc", rng.randint(0, 50))
        pattern = _rand_string(rng, "abc", rng.randint(1, 8))
        assert kmp_search(text, pattern) == builtin_search(text, pattern)
        assert kmp_search(text, pattern, overlapping=False) == builtin_search(
            text, pattern, overlapping=False
        )


def test_build_lps_matches_definition_random():
    """π đối chiếu với bản O(m^3) dịch trực tiếp từ định nghĩa biên."""
    rng = random.Random(SEED + 3)
    for _ in range(3000):
        pattern = _rand_string(rng, "ab", rng.randint(1, 30))
        assert build_lps(pattern) == naive_build_lps(pattern), pattern


def test_kmp_comparison_bound_holds_on_random_inputs():
    """Lập luận khấu hao ≤ 2n phải đúng trên MỌI đầu vào, không chỉ ca đẹp."""
    rng = random.Random(SEED + 11)
    for _ in range(1000):
        text = _rand_string(rng, "ab", rng.randint(1, 500))
        pattern = _rand_string(rng, "ab", rng.randint(1, 20))
        c = OpCounter()
        kmp_search(text, pattern, c)
        assert c.char_comparisons <= 2 * len(text)
        assert c.lps_comparisons <= 2 * len(pattern)


# =========================================================================== #
# 2. Trie đối chiếu duyệt tuyến tính
# =========================================================================== #
def _random_dictionary(rng: random.Random, size: int, sigma: str, max_len: int):
    return [
        _rand_string(rng, sigma, rng.randint(1, max_len)) for _ in range(size)
    ]


@pytest.mark.parametrize("sigma", ["ab", "abc", "abcdefghij"], ids=["S2", "S3", "S10"])
def test_trie_autocomplete_matches_linear_random(sigma):
    """500 từ điển ngẫu nhiên × nhiều truy vấn × nhiều k."""
    rng = random.Random(SEED + 20 + len(sigma))
    alphabet = Alphabet(f"sigma{len(sigma)}", sigma)

    for case in range(500):
        words = _random_dictionary(rng, rng.randint(1, 40), sigma, 6)
        t = Trie(alphabet)
        t.insert_many(words)

        for _ in range(5):
            prefix = _rand_string(rng, sigma, rng.randint(0, 4))
            k = rng.choice([1, 2, 3, 5, 10, 100])

            got = t.autocomplete(prefix, k)
            exp_words, exp_trunc = linear_autocomplete(words, prefix, k)
            assert got.suggestions == exp_words, (
                f"case={case} words={words} prefix={prefix!r} k={k}"
            )
            assert got.truncated == exp_trunc, (
                f"case={case} prefix={prefix!r} k={k}: truncated sai"
            )


def test_trie_search_and_starts_with_match_linear_random():
    rng = random.Random(SEED + 31)
    for _ in range(1000):
        words = _random_dictionary(rng, rng.randint(1, 30), "abc", 5)
        t = Trie(TERNARY)
        t.insert_many(words)

        for _ in range(6):
            q = _rand_string(rng, "abc", rng.randint(0, 6))
            assert t.search(q) == linear_search_word(words, q), q
            assert t.starts_with(q) == linear_starts_with(words, q), q


def test_trie_prefix_count_matches_bruteforce_random():
    """Bất biến I4 (prefix_count) đối chiếu với đếm vét cạn."""
    rng = random.Random(SEED + 41)
    for _ in range(500):
        words = _random_dictionary(rng, rng.randint(1, 25), "abc", 5)
        t = Trie(TERNARY)
        t.insert_many(words)

        for _ in range(5):
            prefix = _rand_string(rng, "abc", rng.randint(0, 4))
            expected = sum(1 for w in words if w.startswith(prefix))
            assert t.count_with_prefix(prefix) == expected, prefix


def test_trie_keys_equal_distinct_words_random():
    rng = random.Random(SEED + 51)
    for _ in range(300):
        words = _random_dictionary(rng, rng.randint(1, 40), "abc", 5)
        t = Trie(TERNARY)
        t.insert_many(words)
        assert t.keys() == sorted(set(words))
        assert t.num_words == len(set(words))
        assert t.total_inserts == len(words)


def test_dict_trie_and_array_trie_agree_random():
    """Hai biến thể lưu cạnh phải cho kết quả y hệt nhau."""
    rng = random.Random(SEED + 61)
    for _ in range(300):
        words = _random_dictionary(rng, rng.randint(1, 30), "abcde", 5)
        alphabet = Alphabet("s5", "abcde")
        d, a = Trie(alphabet), ArrayTrie(alphabet)
        for w in words:
            d.insert(w)
            a.insert(w)
        assert d.num_nodes == a.num_nodes

        for _ in range(4):
            prefix = _rand_string(rng, "abcde", rng.randint(0, 3))
            k = rng.choice([1, 3, 10])
            assert (
                d.autocomplete(prefix, k).suggestions
                == a.autocomplete(prefix, k).suggestions
            )


# =========================================================================== #
# 3. Aho-Corasick đối chiếu naive nhiều mẫu
# =========================================================================== #
def test_aho_corasick_matches_naive_random():
    rng = random.Random(SEED + 71)
    for case in range(800):
        patterns = list(
            {_rand_string(rng, "abc", rng.randint(1, 5)) for _ in range(rng.randint(1, 6))}
        )
        text = _rand_string(rng, "abc", rng.randint(0, 60))

        ac = AhoCorasick(patterns)
        got = sorted((m.start, m.pattern) for m in ac.search(text))
        exp = sorted((s, p) for s, _, p in naive_multi_pattern_search(text, patterns))
        assert got == exp, f"case={case} text={text!r} patterns={patterns}"


def test_aho_corasick_single_pattern_equals_kmp_random():
    """Kiểm chứng mối liên hệ π ⟷ failure link trên dữ liệu ngẫu nhiên."""
    rng = random.Random(SEED + 81)
    for _ in range(1000):
        pattern = _rand_string(rng, "ab", rng.randint(1, 15))
        text = _rand_string(rng, "ab", rng.randint(0, 60))
        ac = AhoCorasick([pattern])
        assert [m.start for m in ac.search(text)] == kmp_search(text, pattern)
        assert ac.failure_array() == build_lps(pattern)


# =========================================================================== #
# 4. Kiểm thử tính chất (property-based, viết tay không cần hypothesis)
# =========================================================================== #
class TestProperties:
    def test_every_reported_position_really_matches(self):
        """Tính chất 1 (soundness): mọi vị trí trả về đều thực sự khớp."""
        rng = random.Random(SEED + 91)
        for _ in range(2000):
            text = _rand_string(rng, "abc", rng.randint(1, 80))
            pattern = _rand_string(rng, "abc", rng.randint(1, 6))
            for pos in kmp_search(text, pattern):
                assert text[pos : pos + len(pattern)] == pattern

    def test_no_matching_position_is_missed(self):
        """Tính chất 2 (completeness): không bỏ sót vị trí nào."""
        rng = random.Random(SEED + 92)
        for _ in range(1500):
            text = _rand_string(rng, "ab", rng.randint(1, 60))
            pattern = _rand_string(rng, "ab", rng.randint(1, 5))
            found = set(kmp_search(text, pattern))
            for i in range(len(text) - len(pattern) + 1):
                if text[i : i + len(pattern)] == pattern:
                    assert i in found, f"bỏ sót {i} trong {text!r}/{pattern!r}"

    def test_positions_strictly_increasing(self):
        """Tính chất 3: kết quả luôn tăng ngặt."""
        rng = random.Random(SEED + 93)
        for _ in range(1000):
            text = _rand_string(rng, "ab", rng.randint(1, 60))
            pattern = _rand_string(rng, "ab", rng.randint(1, 4))
            pos = kmp_search(text, pattern)
            assert all(pos[i] < pos[i + 1] for i in range(len(pos) - 1))

    def test_autocomplete_results_all_have_prefix(self):
        """Tính chất 4: mọi gợi ý đều có đúng tiền tố và là từ trong D."""
        rng = random.Random(SEED + 94)
        for _ in range(500):
            words = _random_dictionary(rng, rng.randint(1, 30), "abc", 5)
            t = Trie(TERNARY)
            t.insert_many(words)
            prefix = _rand_string(rng, "abc", rng.randint(0, 3))
            for s in t.autocomplete(prefix, 10).suggestions:
                assert s.startswith(prefix)
                assert t.search(s) is True
                assert s in words

    def test_autocomplete_truncated_flag_is_accurate(self):
        """Tính chất 5: truncated=False ⇒ đã trả về TẤT CẢ kết quả."""
        rng = random.Random(SEED + 95)
        for _ in range(500):
            words = _random_dictionary(rng, rng.randint(1, 25), "abc", 4)
            t = Trie(TERNARY)
            t.insert_many(words)
            prefix = _rand_string(rng, "abc", rng.randint(0, 3))
            k = rng.choice([1, 2, 5, 10, 50])
            r = t.autocomplete(prefix, k)
            all_hits = sorted({w for w in words if w.startswith(prefix)})
            if not r.truncated:
                assert r.suggestions == all_hits
            else:
                assert len(r.suggestions) == k
                assert len(all_hits) > k

    def test_search_implies_starts_with(self):
        """Tính chất 6: w ∈ D ⇒ starts_with(w) là True."""
        rng = random.Random(SEED + 96)
        for _ in range(500):
            words = _random_dictionary(rng, rng.randint(1, 20), "abc", 5)
            t = Trie(TERNARY)
            t.insert_many(words)
            for w in set(words):
                assert t.search(w) is True
                assert t.starts_with(w) is True
