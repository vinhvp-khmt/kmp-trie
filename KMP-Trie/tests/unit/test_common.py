"""Test cho tầng tiện ích: bảng chữ cái, chuẩn hóa, đo lường."""

from __future__ import annotations

import pytest

from src.common.alphabet import (
    ASCII_LOWER,
    BINARY,
    VIETNAMESE_LOWER,
    Alphabet,
    InvalidCharacterError,
    get_alphabet,
    normalize_unicode,
)
from src.common.metrics import OpCounter, environment_info, measure
from src.common.textio import normalize_word, tokenize


class TestAlphabet:
    def test_size_and_membership(self):
        assert len(BINARY) == 2
        assert len(ASCII_LOWER) == 26
        assert "a" in ASCII_LOWER
        assert "A" not in ASCII_LOWER
        assert "1" not in ASCII_LOWER

    def test_deduplicates_and_sorts(self):
        a = Alphabet("test", "cbaabc")
        assert a.chars == ("a", "b", "c")
        assert a.index == {"a": 0, "b": 1, "c": 2}

    def test_empty_alphabet_rejected(self):
        with pytest.raises(ValueError):
            Alphabet("empty", "")

    def test_validate_reports_char_and_position(self):
        with pytest.raises(InvalidCharacterError) as exc:
            ASCII_LOWER.validate("abc1de")
        assert exc.value.char == "1"
        assert exc.value.position == 3
        assert "ascii_lower" in str(exc.value)

    def test_accepts_and_first_invalid(self):
        assert ASCII_LOWER.accepts("abc") is True
        assert ASCII_LOWER.accepts("ab3") is False
        assert ASCII_LOWER.first_invalid("abc") is None
        assert ASCII_LOWER.first_invalid("ab3") == (2, "3")

    def test_filter_only_for_preprocessing(self):
        assert ASCII_LOWER.filter("a1b2c3") == "abc"
        assert ASCII_LOWER.filter("a1b", replacement="_") == "a_b"

    def test_vietnamese_alphabet_covers_diacritics(self):
        for ch in "àáảãạăâđêôơưứ":
            assert ch in VIETNAMESE_LOWER, ch

    def test_get_alphabet_error_lists_options(self):
        with pytest.raises(KeyError) as exc:
            get_alphabet("nonexistent")
        assert "ascii_lower" in str(exc.value)


class TestNormalization:
    def test_nfc_makes_composed_and_decomposed_equal(self):
        composed = "ê"            # ê
        decomposed = "ê"        # e + combining circumflex
        assert composed != decomposed
        assert normalize_unicode(composed) == normalize_unicode(decomposed)

    def test_normalize_word_strips_and_lowers(self):
        assert normalize_word("  TIN \n") == "tin"
        assert normalize_word("Tính") == "tính"

    def test_normalize_can_preserve_case(self):
        assert normalize_word("TIN", lower=False) == "TIN"


class TestTokenize:
    def test_splits_on_chars_outside_alphabet(self):
        assert tokenize("abc def,ghi", ASCII_LOWER) == ["abc", "def", "ghi"]

    def test_empty_and_all_invalid(self):
        assert tokenize("", ASCII_LOWER) == []
        assert tokenize("123 456", ASCII_LOWER) == []

    def test_trailing_token_captured(self):
        assert tokenize("a1b", ASCII_LOWER) == ["a", "b"]


class TestMetrics:
    def test_counter_accumulates_and_resets(self):
        c = OpCounter()
        c.char_comparisons += 5
        c.nodes_visited += 3
        assert c.as_dict()["char_comparisons"] == 5
        c.reset()
        assert c.char_comparisons == 0
        assert c.nodes_visited == 0

    def test_measure_repeats_and_reports_median(self):
        calls = []
        r = measure(lambda: calls.append(1), repeat=5, warmup=1)
        assert len(calls) == 6, "1 warmup + 5 lần đo"
        assert len(r.times_ns) == 5
        assert r.min_ns <= r.median_ns <= max(r.times_ns)
        assert r.repeat == 5

    def test_measure_rejects_zero_repeat(self):
        with pytest.raises(ValueError):
            measure(lambda: None, repeat=0)

    def test_measure_tracks_memory_when_asked(self):
        r = measure(lambda: [0] * 200_000, repeat=2, track_memory=True)
        assert r.peak_mem_bytes > 0

    def test_environment_info_has_required_fields(self):
        """Checklist của đề: kết quả phải có thông tin môi trường chạy."""
        info = environment_info()
        for key in ("python_version", "platform", "machine", "timer"):
            assert key in info and info[key]
