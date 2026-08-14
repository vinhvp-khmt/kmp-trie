"""Mô-đun A — KMP và mở rộng Aho-Corasick."""

from .aho_corasick import AhoCorasick, Match
from .kmp import (
    KMPMatcher,
    SearchResult,
    build_lps,
    kmp_count,
    kmp_find_first,
    kmp_search,
    kmp_search_iter,
)

__all__ = [
    "AhoCorasick",
    "KMPMatcher",
    "Match",
    "SearchResult",
    "build_lps",
    "kmp_count",
    "kmp_find_first",
    "kmp_search",
    "kmp_search_iter",
]
