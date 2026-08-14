"""Streamlit report dashboard and demo for the KMP & Trie project."""
from __future__ import annotations

import json
import os
import sys
import html
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from PIL import Image


APP_DIR = Path(__file__).resolve().parent
DEFAULT_KMP_REPO = Path("/Users/Vinh/Documents/ChatGPT/Thuật toán-KMP & Trie/KMP-Trie")
KMP_REPO_CANDIDATES = [
    Path(os.environ["KMP_TRIE_REPO"]).expanduser()
    if os.environ.get("KMP_TRIE_REPO")
    else None,
    APP_DIR / "KMP-Trie",
    APP_DIR.parent / "KMP-Trie",
    DEFAULT_KMP_REPO,
]
KMP_REPO = next(
    (
        candidate.resolve()
        for candidate in KMP_REPO_CANDIDATES
        if candidate is not None and (candidate / "src").is_dir()
    ),
    DEFAULT_KMP_REPO.resolve(),
)
if (KMP_REPO / "src").is_dir() and str(KMP_REPO) not in sys.path:
    sys.path.insert(0, str(KMP_REPO))

try:
    from src.common.alphabet import ALPHABETS, get_alphabet, normalize_unicode
    from src.common.metrics import OpCounter
    from src.kmp.aho_corasick import AhoCorasick
    from src.kmp.kmp import build_lps, kmp_search
    from src.trie.trie import Trie

    IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - displayed in Streamlit UI.
    ALPHABETS = {}
    IMPORT_ERROR = exc


MAIN_TAB_LABELS = [
    "Giới thiệu",
    "Cơ sở lý thuyết",
    "Thuật toán & chứng minh",
    "Kiểm thử & thực nghiệm",
    "Kết luận",
    "Demo",
]
MAIN_TAB_ROUTES = {
    "Giới thiệu": "gioi-thieu",
    "Cơ sở lý thuyết": "ly-thuyet",
    "Thuật toán & chứng minh": "thuat-toan",
    "Kiểm thử & thực nghiệm": "thuc-nghiem",
    "Kết luận": "ket-luan",
    "Demo": "demo",
}
MAIN_ROUTE_TABS = {route: label for label, route in MAIN_TAB_ROUTES.items()}
MAIN_ROUTE_TABS["mo-phong-search"] = "Giới thiệu"

DEMO_TAB_LABELS = ["KMP", "Trie", "Aho-Corasick"]
DEMO_TAB_ROUTES = {"KMP": "kmp", "Trie": "trie", "Aho-Corasick": "aho-corasick"}
DEMO_ROUTE_TABS = {route: label for label, route in DEMO_TAB_ROUTES.items()}


def query_param(name: str, default: str) -> str:
    value = st.query_params.get(name, default)
    if isinstance(value, list):
        return value[-1] if value else default
    return value or default


def set_default_tab_from_route(
    key: str,
    labels: list[str],
    route_tabs: dict[str, str],
    param: str,
    default_route: str,
) -> str:
    route = query_param(param, default_route).strip().rstrip(".,;)")
    label = route_tabs.get(route, route_tabs[default_route])
    if st.session_state.get(f"{key}_route") != route:
        st.session_state.pop(key, None)
        st.session_state[f"{key}_route"] = route
    return label if label in labels else labels[0]


def sync_main_tab_route() -> None:
    label = st.session_state.get("main_tab", MAIN_TAB_LABELS[0])
    route = MAIN_TAB_ROUTES.get(label, MAIN_TAB_ROUTES[MAIN_TAB_LABELS[0]])
    st.query_params["tab"] = route
    st.session_state["main_tab_route"] = route


def sync_demo_tab_route() -> None:
    label = st.session_state.get("demo_tab", DEMO_TAB_LABELS[0])
    route = DEMO_TAB_ROUTES.get(label, DEMO_TAB_ROUTES[DEMO_TAB_LABELS[0]])
    st.query_params["tab"] = MAIN_TAB_ROUTES["Demo"]
    st.query_params["demo"] = route
    st.session_state["demo_tab_route"] = route


def inject_responsive_styles() -> None:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"],
        div[data-testid="collapsedControl"] {
            display: none;
        }

        .block-container {
            padding-top: 1.25rem;
            max-width: 1180px;
        }

        div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            transition: transform 160ms ease-out, width 160ms ease-out;
        }

        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.4rem;
            overflow-x: auto;
            overflow-y: hidden;
            white-space: nowrap;
            scrollbar-width: thin;
            padding-bottom: 0.2rem;
            scroll-behavior: smooth;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"] {
            flex: 0 0 auto;
            border-radius: 999px;
            padding: 0.45rem 0.8rem;
            min-height: 2.25rem;
            transition: background-color 140ms ease-out, color 140ms ease-out, box-shadow 140ms ease-out;
            -webkit-tap-highlight-color: transparent;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"] p {
            font-size: 0.95rem;
            white-space: nowrap;
        }

        div[data-testid="stDataFrame"] {
            overflow-x: auto;
        }

        @media (max-width: 760px) {
            .block-container {
                padding: 0.75rem 0.65rem 1.5rem;
                max-width: 100%;
            }

            h1 {
                font-size: 1.75rem;
                line-height: 1.15;
            }

            h2, h3 {
                font-size: 1.05rem;
                line-height: 1.25;
            }

            p, li, div[data-testid="stMarkdownContainer"] {
                font-size: 0.92rem;
            }

            div[data-testid="stTabs"] [data-baseweb="tab-list"] {
                margin-left: -0.15rem;
                margin-right: -0.15rem;
                padding-left: 0.15rem;
                padding-right: 0.15rem;
            }

            div[data-testid="stTabs"] [data-baseweb="tab"] {
                padding: 0.35rem 0.6rem;
                min-height: 2rem;
            }

            div[data-testid="stTabs"] [data-baseweb="tab"] p {
                font-size: 0.82rem;
            }

            div[data-testid="stMetric"] {
                padding: 0.35rem 0;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
            div[data-testid="stTabs"] [data-baseweb="tab"] {
                transition: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def require_source() -> bool:
    if IMPORT_ERROR is None:
        return True
    st.error(f"Không import được source KMP-Trie từ {KMP_REPO}: {IMPORT_ERROR}")
    st.info("Đặt biến môi trường KMP_TRIE_REPO tới thư mục repo KMP-Trie nếu repo nằm ở chỗ khác.")
    return False


def repo_path(*parts: str) -> Path:
    return KMP_REPO.joinpath(*parts)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(KMP_REPO))
    except ValueError:
        return str(path)


def figure_path(name: str) -> Path:
    return repo_path("results", "figures", name)


@st.cache_data(show_spinner=False)
def read_csv(name: str) -> pd.DataFrame:
    path = repo_path("results", "benchmarks", name)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def read_environment() -> dict[str, Any]:
    path = repo_path("results", "benchmarks", "environment.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def read_demo_words() -> str:
    path = repo_path("data", "dictionaries", "demo_words.txt")
    if not path.exists():
        return "tin\ntinh\nto\ntoan\ntrie\nkmp\nalgorithm\nautomation"
    return path.read_text(encoding="utf-8")


def render_plot_grid(paths: list[Path], captions: list[str]) -> None:
    existing = [(p, c) for p, c in zip(paths, captions) if p.exists()]
    if not existing:
        st.info("Chưa tìm thấy biểu đồ trong results/figures.")
        return

    for i in range(0, len(existing), 2):
        cols = st.columns(2)
        for col, (path, caption) in zip(cols, existing[i : i + 2]):
            col.image(str(path), caption=caption, width="stretch")


def render_flex_figure_grid(paths: list[Path], captions: list[str], height: int = 300) -> None:
    existing = [(p, c) for p, c in zip(paths, captions) if p.exists()]
    if not existing:
        st.info("Chưa tìm thấy biểu đồ trong results/figures.")
        return

    for i in range(0, len(existing), 2):
        cols = st.columns(2)
        for col, (path, caption) in zip(cols, existing[i : i + 2]):
            col.image(normalized_figure_png(str(path), canvas_height=height * 2), caption=caption, width="stretch")


@st.cache_data(show_spinner=False)
def normalized_figure_png(path: str, canvas_width: int = 1200, canvas_height: int = 720) -> bytes:
    image = Image.open(path).convert("RGBA")
    scale = min(canvas_width / image.width, canvas_height / image.height)
    resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))

    canvas = Image.new("RGBA", (canvas_width, canvas_height), "WHITE")
    x = (canvas_width - resized.width) // 2
    y = (canvas_height - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))

    out = BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


def render_e1_analysis(df: pd.DataFrame) -> None:
    if df.empty:
        return

    summary = (
        df.groupby("text_kind", as_index=False)
        .agg(
            n_min=("n", "min"),
            n_max=("n", "max"),
            kmp_cmp_min=("kmp_cmp_per_n", "min"),
            kmp_cmp_max=("kmp_cmp_per_n", "max"),
            naive_cmp_max=("naive_cmp_per_n", "max"),
            speedup_cmp_max=("speedup_cmp", "max"),
        )
        .sort_values("text_kind")
    )
    for col in ("kmp_cmp_min", "kmp_cmp_max", "naive_cmp_max", "speedup_cmp_max"):
        summary[col] = summary[col].round(2)

    st.subheader("Phân tích ngắn E1")
    st.dataframe(summary, hide_index=True, width="stretch")
    st.markdown(
        """
- `kmp_cmp_per_n` luôn nằm quanh `1.00-2.00`, đúng với chặn lý thuyết không quá `2n`.
- `uniform` là ca gần xấu nhất của KMP: tại `n=1,000,000`, KMP dùng `1,999,937` phép so sánh, xấp xỉ `1.9999n`.
- `repetitive` có rất nhiều match nhưng KMP vẫn chỉ `1.0` phép so sánh trên mỗi ký tự; naive tăng lên khoảng `32x`.
- `naive` bị bỏ qua ở các cấu hình lớn vì `n·m > 8,000,000`, tránh chạy quá lâu.
- Thời gian `kmp_median_ns` tăng gần tuyến tính theo `n`; chi phí xây LPS chỉ vài nghìn ns nên phần duyệt văn bản là chính.
"""
    )
    st.success("Kết luận: E1 xác nhận KMP mở rộng tuyến tính theo độ dài văn bản và ổn định hơn naive, đặc biệt ở dữ liệu lặp hoặc gần trường hợp xấu.")


def render_report_outline() -> None:
    st.dataframe(
        pd.DataFrame(
            [
                {"Tab": "Giới thiệu", "Nội dung báo cáo": "Chương 1 + Chương 5", "Vai trò": "Bài toán, module, kiến trúc source"},
                {"Tab": "Cơ sở lý thuyết", "Nội dung báo cáo": "Chương 2", "Vai trò": "Chuỗi, border, LPS, bất biến KMP và Trie"},
                {"Tab": "Thuật toán & chứng minh", "Nội dung báo cáo": "Chương 3 + Chương 4", "Vai trò": "Mã giả, chứng minh, độ phức tạp"},
                {"Tab": "Kiểm thử & thực nghiệm", "Nội dung báo cáo": "Chương 6", "Vai trò": "Baseline, bộ dữ liệu, E1-E5"},
                {"Tab": "Kết luận", "Nội dung báo cáo": "Chương 7 + Chương 8", "Vai trò": "Ứng dụng, giới hạn, mở rộng, bài học"},
                {"Tab": "Demo", "Nội dung báo cáo": "Giao diện minh họa", "Vai trò": "Chạy thử KMP, Trie, Aho-Corasick"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )


def render_overview_tab() -> None:
    st.subheader("Tên đề tài")
    st.markdown(
        """
**KMP và Trie: cài đặt, kiểm thử và thực nghiệm.**  
Đề tài tập trung vào hai kỹ thuật xử lý chuỗi phổ biến: tìm mẫu tuyến tính bằng KMP và lưu/truy vấn từ theo tiền tố bằng Trie.
"""
    )

    st.subheader("Module chính")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Module": "KMP",
                    "Bài toán": "Tìm mọi vị trí xuất hiện của một mẫu trong văn bản",
                    "Đầu ra": "Danh sách vị trí 0-based, có hỗ trợ khớp chồng lấn",
                    "Điểm nhấn": "Sinh mảng LPS và không lùi con trỏ văn bản",
                },
                {
                    "Module": "Trie",
                    "Bài toán": "Lưu từ điển và truy vấn theo tiền tố",
                    "Đầu ra": "search, starts_with, autocomplete k kết quả",
                    "Điểm nhấn": "Bảng chữ cái khai báo tường minh, ký tự lạ bị từ chối",
                },
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Câu hỏi nghiên cứu")
    st.markdown(
        """
- Khi loại văn bản và độ dài mẫu thay đổi, số phép so sánh của KMP có còn tăng tuyến tính theo kích thước đầu vào không?
- Thời gian tìm chính xác và tìm theo tiền tố của Trie có phụ thuộc vào số từ `N` không?
- Autocomplete dừng sớm sau khi đủ `k` kết quả bớt duyệt bao nhiêu nút?
- Khi nào Aho-Corasick có lợi hơn việc chạy KMP cho từng mẫu?
"""
    )

    st.subheader("Kiến trúc source code")
    st.code(
        """KMP-Trie/
├── src/
│   ├── kmp/
│   │   ├── kmp.py              # build_lps, kmp_search, matcher
│   │   └── aho_corasick.py     # mở rộng tìm nhiều mẫu
│   ├── trie/
│   │   └── trie.py             # Trie, ArrayTrie, autocomplete
│   └── common/
│       ├── alphabet.py         # bảng chữ cái, kiểm tra ký tự
│       └── metrics.py          # OpCounter, đo thời gian
├── tests/                      # unit, adversarial, random, doctest
├── data/                       # corpus, dictionaries, MANIFEST
├── scripts/                    # sinh dữ liệu, benchmark, vẽ biểu đồ
├── results/
│   ├── benchmarks/             # CSV số liệu E1-E5
│   └── figures/                # hình từ benchmark""",
        language="text",
    )

    render_search_visualizer_tab("Mô phỏng lý thuyết KMP")

def render_theory_tab() -> None:
    st.subheader("Ký hiệu và khái niệm chuỗi")
    st.write(
        "Chương 2 bắt đầu bằng quy ước đánh số chuỗi từ `0`, ký hiệu độ dài `|S|`, "
        "đoạn con `S[i..j]`, tiền tố, hậu tố và border."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"Ký hiệu": "S", "Ý nghĩa": "Một chuỗi bất kỳ dùng khi trình bày khái niệm chung"},
                {"Ký hiệu": "T", "Ý nghĩa": "Văn bản cần tìm kiếm bằng KMP"},
                {"Ký hiệu": "P", "Ý nghĩa": "Mẫu cần tìm trong văn bản"},
                {"Ký hiệu": "n = |T|", "Ý nghĩa": "Độ dài văn bản"},
                {"Ký hiệu": "m = |P|", "Ý nghĩa": "Độ dài mẫu"},
                {"Ký hiệu": "D", "Ý nghĩa": "Tập các từ được lưu trong Trie"},
                {"Ký hiệu": "N", "Ý nghĩa": "Số từ phân biệt trong từ điển"},
                {"Ký hiệu": "q", "Ý nghĩa": "Tiền tố dùng để truy vấn Trie"},
                {"Ký hiệu": "k", "Ý nghĩa": "Số lượng gợi ý tối đa cần trả về"},
                {"Ký hiệu": "Σ / Σ'", "Ý nghĩa": "Tập ký tự của KMP / tập ký tự cấu hình cho Trie"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.dataframe(
        pd.DataFrame(
            [
                {"Ví dụ": "S = abcde", "Kết luận": "S[1..3] = bcd"},
                {"Ví dụ": "S = ababa", "Kết luận": "`ab`, `aba` là tiền tố; `ba`, `aba` là hậu tố"},
                {"Ví dụ": "S = ababa", "Kết luận": "Các border khác rỗng là `a` và `aba`; border dài nhất có độ dài 3"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Hàm tiền tố và mảng LPS")
    st.write(
        "Với mẫu `P`, giá trị `π[i]` là độ dài border dài nhất của đoạn `P[0..i]`. "
        "Trong source, mảng này là `lps` và được tạo bởi `build_lps`."
    )
    pattern = st.text_input("Mẫu minh họa LPS", value="ababaca", key="theory-pattern")
    if require_source():
        lps = build_lps(pattern)
        st.dataframe(
            pd.DataFrame({"i": list(range(len(pattern))), "P[i]": list(pattern), "π[i] / LPS[i]": lps}),
            hide_index=True,
            width="stretch",
        )
    st.info("Với `P = ababaca`, tại `i = 4` ta có `P[0..4] = ababa`; border dài nhất là `aba`, nên `π[4] = 3`.")

    st.subheader("Hai tính chất LPS dùng cho KMP")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Tính chất": "Tìm border ngắn hơn",
                    "Nội dung": "Nếu border hiện tại dài L không dùng tiếp được, border tiếp theo có độ dài π[L-1].",
                    "Ví dụ": "`abaaba`: 3 → 1 → 0, tức `aba → a → chuỗi rỗng`",
                },
                {
                    "Tính chất": "LPS tăng tối đa một đơn vị",
                    "Nội dung": "Với mọi i ≥ 1, π[i] ≤ π[i-1] + 1.",
                    "Ví dụ": "1 → 2 hoặc 2 → 3 có thể xảy ra; 1 → 4 thì không.",
                },
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Bất biến của KMP")
    st.write(
        "Trước khi xử lý `T[j]`, biến `i` là độ dài lớn nhất nhỏ hơn `m` sao cho "
        "`P[0..i-1]` trùng với phần cuối của `T[0..j-1]`."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"Trường hợp": "T[j] = P[i]", "Cập nhật": "Khớp thêm một ký tự, tăng i lên 1"},
                {"Trường hợp": "T[j] ≠ P[i] và i > 0", "Cập nhật": "Đặt i ← π[i-1], giữ lại border dài nhất còn khả năng khớp"},
                {"Trường hợp": "i = m", "Cập nhật": "Ghi nhận vị trí j-m+1, rồi đặt i ← π[m-1] để bắt khớp chồng lấn"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    if require_source():
        overlap_text, overlap_pattern = "aaaa", "aa"
        st.dataframe(
            pd.DataFrame(
                {
                    "T": [overlap_text],
                    "P": [overlap_pattern],
                    "LPS": [build_lps(overlap_pattern)],
                    "Kết quả KMP": [kmp_search(overlap_text, overlap_pattern)],
                }
            ),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Cấu trúc Trie và các bất biến")
    st.write(
        "Trie lưu chuỗi theo từng ký tự; các từ có cùng tiền tố dùng chung đường đi từ gốc. "
        "Ví dụ `tin`, `tinh`, `to`, `toan` cùng chia sẻ nút `t`; `tin` và `tinh` chia sẻ đường `t → i → n`."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"Bất biến": "I1", "Ý nghĩa": "Mỗi nút u biểu diễn đúng một tiền tố str(u); gốc biểu diễn tiền tố rỗng"},
                {"Bất biến": "I2", "Ý nghĩa": "is_end đúng khi và chỉ khi str(u) là một từ đã lưu trong Trie"},
                {"Bất biến": "I3", "Ý nghĩa": "word_count là số lần từ str(u) được thêm; is_end đúng khi word_count > 0"},
                {"Bất biến": "I4", "Ý nghĩa": "prefix_count là tổng số lần thêm các từ bắt đầu bằng str(u)"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    if require_source():
        trie = Trie(get_alphabet("ascii_lower"))
        for word in ["tin", "tin", "tinh", "to", "toan"]:
            trie.insert(word)
        st.dataframe(
            pd.DataFrame(
                [
                    {"Tiền tố/từ": "tin", "search": trie.search("tin"), "word_count": trie.count("tin"), "prefix_count": trie.count_with_prefix("tin")},
                    {"Tiền tố/từ": "ti", "search": trie.search("ti"), "word_count": trie.count("ti"), "prefix_count": trie.count_with_prefix("ti")},
                    {"Tiền tố/từ": "to", "search": trie.search("to"), "word_count": trie.count("to"), "prefix_count": trie.count_with_prefix("to")},
                ]
            ),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Giả thiết và quy ước sử dụng")
    st.dataframe(
        pd.DataFrame(
            [
                {"Nội dung": "Hai ký tự có thể kiểm tra bằng phép bằng", "Phạm vi": "KMP", "Ý nghĩa": "KMP không yêu cầu ký tự có thứ tự"},
                {"Nội dung": "Mỗi phép so sánh ký tự là O(1)", "Phạm vi": "Phân tích KMP", "Ý nghĩa": "Dùng để suy ra thời gian O(n+m)"},
                {"Nội dung": "Σ hữu hạn", "Phạm vi": "Không bắt buộc với KMP", "Ý nghĩa": "KMP không tạo bảng chuyển theo toàn bộ tập ký tự"},
                {"Nội dung": "Mẫu rỗng bị từ chối", "Phạm vi": "Quy ước chương trình", "Ý nghĩa": "`kmp_search` yêu cầu m ≥ 1"},
                {"Nội dung": "Trie dùng Alphabet cấu hình trước", "Phạm vi": "Quy ước hệ thống", "Ý nghĩa": "`insert` kiểm tra ký tự trước khi thêm vào cây"},
                {"Nội dung": "Từ điển chuẩn hóa Unicode trước khi thêm", "Phạm vi": "Tiền xử lý dữ liệu", "Ý nghĩa": "Tránh tách nhánh do khác biểu diễn ký tự"},
                {"Nội dung": "Không có delete trong Trie chính", "Phạm vi": "Phạm vi chuyên đề", "Ý nghĩa": "Nếu thêm delete phải cập nhật word_count và prefix_count"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )


def render_algorithm_tab() -> None:
    kmp_tab, trie_tab, complexity_tab = st.tabs(["KMP", "Trie", "Độ phức tạp"])

    with kmp_tab:
        st.subheader("BUILD_LPS")
        st.write(
            "Hàm `build_lps` nhận mẫu `P` và trả về mảng LPS cùng độ dài. "
            "Nếu `P` rỗng, hàm trả về `[]`; với mẫu khác rỗng luôn có `lps[0] = 0`."
        )
        st.code(
            """BUILD_LPS(P):
    m <- độ dài của P
    lps <- mảng gồm m phần tử bằng 0

    if m = 0:
        return lps

    length = 0

    for i <- 1 to m - 1:
        while True:
            if P[i] = P[length]:
                length <- length + 1
                break

            if length = 0:
                break

            length <- lps[length - 1]

        lps[i] = length
    return lps""",
            language="text",
        )

        st.subheader("Các trường hợp khi xây LPS")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Trường hợp": "P[i] = P[length]", "Xử lý": "Mở rộng border hiện tại, length <- length + 1"},
                    {"Trường hợp": "P[i] != P[length] và length = 0", "Xử lý": "Không còn border ngắn hơn, lps[i] = 0"},
                    {"Trường hợp": "P[i] != P[length] và length > 0", "Xử lý": "Thử border ngắn hơn: length <- lps[length-1]"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.info("Ví dụ trong báo cáo: với `P = ababaca`, tại `i = 4`, `lps[3] = 2`; so sánh `P[4] = a` với `P[2] = a`, nên `lps[4] = 3`.")

        st.subheader("KMP_SEARCH")
        st.code(
            """KMP_SEARCH(T, P):
    if P rỗng:
        báo lỗi

    n <- độ dài của T
    m <- độ dài của P

    if m > n:
        return []

    lps <- BUILD_LPS(P)
    result <- []
    i <- 0

    for j <- 0 to n - 1:
        while True:
            if T[j] = P[i]:
                i <- i + 1
                break

            if i = 0:
                break

            i <- lps[i - 1]

        if i = m:
            result.append(j - m + 1)
            i <- lps[m - 1]

    return result""",
            language="text",
        )
        st.subheader("Các trường hợp khi tìm kiếm")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Trường hợp": "T[j] = P[i]", "Xử lý": "Khớp thêm một ký tự, i <- i + 1"},
                    {"Trường hợp": "T[j] != P[i] và i > 0", "Xử lý": "Không lùi j; đặt i <- lps[i-1] rồi thử lại T[j]"},
                    {"Trường hợp": "T[j] != P[i] và i = 0", "Xử lý": "Chuyển sang ký tự tiếp theo của văn bản"},
                    {"Trường hợp": "i = m", "Xử lý": "Ghi nhận vị trí j-m+1, rồi i <- lps[m-1] để bắt chồng lấn"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        if require_source():
            text, pattern = "aaaa", "aa"
            st.dataframe(
                pd.DataFrame(
                    {
                        "T": [text],
                        "P": [pattern],
                        "LPS": [build_lps(pattern)],
                        "Kết quả mặc định": [kmp_search(text, pattern)],
                    }
                ),
                hide_index=True,
                width="stretch",
            )

        st.subheader("Các định lý trong chứng minh KMP")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Định lý": "3.1", "Nội dung": "BUILD_LPS tính đúng giá trị LPS tại mọi vị trí của mẫu P."},
                    {"Định lý": "3.2", "Nội dung": "Trước khi xử lý T[j], i là độ dài phần đầu mẫu đang trùng với phần cuối văn bản đã xử lý."},
                    {"Định lý": "3.3", "Nội dung": "KMP không trả về vị trí sai: khi i = m thì T[j-m+1..j] = P."},
                    {"Định lý": "3.4", "Nội dung": "KMP không bỏ sót kết quả vì các lần lùi bằng LPS chỉ bỏ qua trường hợp chắc chắn không thể khớp."},
                    {"Định lý": "3.5", "Nội dung": "Phép gán i <- lps[m-1] giúp phát hiện các lần xuất hiện chồng lấn."},
                ]
            ),
            hide_index=True,
            width="stretch",
        )

    with trie_tab:
        st.subheader("TRIE_INSERT")
        st.write(
            "Báo cáo tập trung chứng minh hai thao tác chính: `insert` và `autocomplete`. "
            "Với `insert`, điểm quan trọng là `VALIDATE(word)` chạy trước khi cây bị thay đổi."
        )
        st.code(
            """TRIE_INSERT(root, word):
    if word rỗng:
        báo lỗi

    VALIDATE(word)

    node <- root
    node.prefix_count <- node.prefix_count + 1

    for c in word:
        next <- node.children.get(c)

        if next = null:
            next <- Node mới
            node.children[c] <- next

        node <- next
        node.prefix_count <- node.prefix_count + 1

    node.word_count <- node.word_count + 1""",
            language="text",
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {"Điểm kiểm soát": "word rỗng", "Ý nghĩa": "Không tạo một từ không có ký tự trong Trie"},
                    {"Điểm kiểm soát": "VALIDATE(word)", "Ý nghĩa": "Nếu có ký tự ngoài alphabet, Trie giữ nguyên trạng thái cũ"},
                    {"Điểm kiểm soát": "prefix_count", "Ý nghĩa": "Tăng tại gốc và mọi nút trên đường đi của từ"},
                    {"Điểm kiểm soát": "word_count", "Ý nghĩa": "Tăng tại nút cuối, từ đó xác định is_end"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )

        st.subheader("TRIE_AUTOCOMPLETE")
        st.code(
            """TRIE_AUTOCOMPLETE(root, q, k):
    if k < 0:
        báo lỗi

    if q chứa ký tự không hợp lệ:
        return AutocompleteResult(q, [], false)

    node <- nút đạt được khi đi từ root theo q

    if node = null:
        return AutocompleteResult(q, [], false)

    if k = 0:
        return AutocompleteResult(q, [], node.prefix_count > 0)

    out <- []
    path <- danh sách ký tự của q
    stack <- [FRAME(node)]
    truncated <- false

    while stack không rỗng:
        cur <- frame hiện tại

        if cur chưa được thăm:
            đánh dấu cur đã được thăm

            if cur.is_end:
                if số phần tử của out = k:
                    truncated <- true
                    break

                out.append(join(path))

        lấy cạnh tiếp theo theo thứ tự tăng dần

        if không còn cạnh:
            quay lại nút cha
        else:
            thêm ký tự vào path
            đưa nút con vào stack

    return AutocompleteResult(q, out, truncated)""",
            language="text",
        )
        st.subheader("DFS, thứ tự từ điển và truncated")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Cơ chế": "Duyệt cây", "Ý nghĩa": "Dùng DFS với stack tường minh, bắt đầu từ nút của prefix q"},
                    {"Cơ chế": "Thứ tự kết quả", "Ý nghĩa": "Kiểm tra nút hiện tại trước, các cạnh con lấy bằng sorted(node.children)"},
                    {"Cơ chế": "Ví dụ", "Ý nghĩa": "Nếu Trie chứa a, an, and thì kết quả là [a, an, and]"},
                    {"Cơ chế": "truncated=False", "Ý nghĩa": "Không còn kết quả hợp lệ bị bỏ lại"},
                    {"Cơ chế": "truncated=True", "Ý nghĩa": "Đã gặp kết quả thứ k+1 nên biết chắc còn kết quả chưa trả về"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        if require_source():
            trie = Trie(get_alphabet("ascii_lower"))
            for word in ["a", "an", "and"]:
                trie.insert(word)
            result = trie.autocomplete("a", 10)
            limited = trie.autocomplete("a", 2)
            zero = trie.autocomplete("a", 0)
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Truy vấn": "autocomplete('a', 10)", "suggestions": result.suggestions, "truncated": result.truncated},
                        {"Truy vấn": "autocomplete('a', 2)", "suggestions": limited.suggestions, "truncated": limited.truncated},
                        {"Truy vấn": "autocomplete('a', 0)", "suggestions": zero.suggestions, "truncated": zero.truncated},
                    ]
                ),
                hide_index=True,
                width="stretch",
            )

        st.subheader("Các định lý trong chứng minh Trie")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Định lý": "3.6", "Nội dung": "Sau mỗi lần TRIE_INSERT, các bất biến I1-I4 vẫn được bảo toàn."},
                    {"Định lý": "3.7", "Nội dung": "TRIE_AUTOCOMPLETE trả về tối đa k từ có prefix q theo thứ tự từ điển; truncated phản ánh còn kết quả hay không."},
                ]
            ),
            hide_index=True,
            width="stretch",
        )

    with complexity_tab:
        st.subheader("KMP")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Kết quả": "Thời gian", "Chặn": "O(n + m)", "Giải thích": "BUILD_LPS mất O(m), duyệt văn bản mất O(n)"},
                    {"Kết quả": "So sánh trong tìm kiếm", "Chặn": "≤ 2n", "Giải thích": "j chỉ tăng; mỗi lần lùi bằng LPS làm i giảm thực sự"},
                    {"Kết quả": "So sánh khi xây LPS", "Chặn": "≤ 2m", "Giải thích": "length chỉ tăng từng đơn vị và giảm theo lps[length-1]"},
                    {"Kết quả": "Bộ nhớ phụ", "Chặn": "O(m)", "Giải thích": "Mảng LPS có m phần tử, biến còn lại là hằng số"},
                    {"Kết quả": "Nếu tính danh sách kết quả", "Chặn": "O(m + R)", "Giải thích": "R là số lần xuất hiện của mẫu"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.info("Trường hợp gần đạt `2n`: `T = aaaa...a`, `P = aaaa...ab`. Báo cáo ghi E1 đo được `1,999,937` phép so sánh khi `n = 1,000,000`, xấp xỉ `1.9999n`.")

        st.subheader("Trie")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Thao tác": "insert(w)", "Thời gian": "Θ(L)", "Bộ nhớ thêm / làm việc": "Tạo tối đa L nút mới"},
                    {"Thao tác": "search(w)", "Thời gian": "Θ(L)", "Bộ nhớ thêm / làm việc": "O(1)"},
                    {"Thao tác": "starts_with(q)", "Thời gian": "Θ(|q|)", "Bộ nhớ thêm / làm việc": "O(1)"},
                    {"Thao tác": "count_with_prefix(q)", "Thời gian": "Θ(|q|)", "Bộ nhớ thêm / làm việc": "O(1)"},
                    {"Thao tác": "autocomplete(q,k)", "Thời gian": "O(|q| + V|Σ'|log|Σ'| + kLmax)", "Bộ nhớ thêm / làm việc": "O(|Σ'|Lmax), chưa tính kết quả"},
                    {"Thao tác": "keys()", "Thời gian": "O(S) khi alphabet cố định", "Bộ nhớ thêm / làm việc": "O(S) cho danh sách kết quả"},
                    {"Thao tác": "Bộ nhớ cấu trúc Trie", "Thời gian": "-", "Bộ nhớ thêm / làm việc": "Θ(M) nút"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {"Ý chính": "Định lý 4.2", "Nội dung": "`search` và `starts_with` chỉ đi theo chuỗi truy vấn, nên không phụ thuộc trực tiếp vào số từ N."},
                    {"Ý chính": "Autocomplete", "Nội dung": "Chi phí gồm đi tới prefix O(|q|), DFS trên V nút và tạo tối đa k chuỗi kết quả."},
                    {"Ý chính": "Dừng sớm", "Nội dung": "Sau khi đủ k kết quả, chỉ duyệt tiếp đến khi biết chắc có kết quả thứ k+1 để đặt truncated=True."},
                    {"Ý chính": "Bộ nhớ autocomplete", "Nội dung": "Dùng `path` chung và stack DFS, không tạo chuỗi mới ở mỗi cạnh."},
                ]
            ),
            hide_index=True,
            width="stretch",
        )

        st.subheader("Trade-off lưu cạnh")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Cách lưu": "dict[str, TrieNode]", "Ưu điểm": "Chỉ lưu cạnh thực sự tồn tại; hợp với cây thưa và alphabet lớn", "Chi phí": "Tra cứu trung bình khấu hao O(1)"},
                    {"Cách lưu": "mảng |Σ'| phần tử", "Ưu điểm": "Tìm cạnh bằng chỉ số, O(1)", "Chi phí": "Mỗi nút cấp phát |Σ'| ô; nếu Trie có M nút thì có M|Σ'| ô"},
                    {"Cách lưu": "Ghi chú thực nghiệm", "Ưu điểm": "Với |Σ'| = 26, ArrayTrie dùng khoảng 1.50-1.53 lần bộ nhớ", "Chi phí": "Báo cáo không suy rộng con số này sang alphabet tiếng Việt |Σ'| = 105"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )

        st.subheader("Bảng tổng hợp")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Tiêu chí": "Tiền xử lý", "KMP": "O(m)", "Naive": "Không", "Trie": "Θ(Σ|w|) để xây từ điển", "Duyệt tuyến tính": "Không"},
                    {"Tiêu chí": "Một truy vấn", "KMP": "O(n) nếu đã có LPS", "Naive": "O(nm)", "Trie": "O(|q|+V+kLmax) với alphabet cố định", "Duyệt tuyến tính": "O(N|q|)"},
                    {"Tiêu chí": "Bộ nhớ cấu trúc / phụ", "KMP": "O(m)", "Naive": "O(1)", "Trie": "Θ(M) nút", "Duyệt tuyến tính": "O(Σ|w|) để lưu danh sách"},
                    {"Tiêu chí": "Yếu tố quyết định chính", "KMP": "n,m", "Naive": "n,m", "Trie": "|q|,V,k,Lmax", "Duyệt tuyến tính": "N,|q|"},
                    {"Tiêu chí": "Ảnh hưởng alphabet", "KMP": "Không trực tiếp", "Naive": "Không trực tiếp", "Trie": "Có trong cách lưu cạnh và duyệt cây con", "Duyệt tuyến tính": "Không trực tiếp"},
                ]
            ),
            hide_index=True,
            width="stretch",
        )


def render_experiments_tab() -> None:
    st.subheader("Chiến lược kiểm thử")
    st.dataframe(
        pd.DataFrame(
            [
                {"Nhóm test": "unit", "Vai trò": "Ca cơ bản và trường hợp biên"},
                {"Nhóm test": "adversarial", "Vai trò": "Dữ liệu tấn công giả thiết/cận"},
                {"Nhóm test": "random", "Vai trò": "Đối chiếu ngẫu nhiên với seed cố định"},
                {"Nhóm test": "doctest", "Vai trò": "Ví dụ trong docstring phải chạy được"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Năm thí nghiệm trong báo cáo")
    st.dataframe(
        pd.DataFrame(
            [
                {"Mã": "E1", "Câu hỏi": "KMP so với naive khi n tăng", "Tệp": "e1_scaling_n.csv"},
                {"Mã": "E2", "Câu hỏi": "Ảnh hưởng của độ dài mẫu m", "Tệp": "e2_scaling_m.csv"},
                {"Mã": "E3", "Câu hỏi": "Trie so với duyệt tuyến tính", "Tệp": "e3_trie_vs_linear.csv"},
                {"Mã": "E4", "Câu hỏi": "Early stop và trade-off lưu cạnh", "Tệp": "e4_early_stop.csv / e4_storage_tradeoff.csv"},
                {"Mã": "E5", "Câu hỏi": "Aho-Corasick so với KMP lặp lại", "Tệp": "e5_multipattern.csv"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    render_flex_figure_grid(
        [
            figure_path("fig1_time_vs_n.png"),
            figure_path("fig3_effect_of_m.png"),
            figure_path("fig4_trie_vs_linear.png"),
            figure_path("fig7_multipattern.png"),
        ],
        [
            "E1: thời gian theo n",
            "E2: ảnh hưởng của m",
            "E3: Trie so với linear scan",
            "E5: nhiều mẫu",
        ],
        height=300,
    )

    csv_name = st.selectbox(
        "Xem nhanh bảng số liệu",
        [
            "e1_scaling_n.csv",
            "e2_scaling_m.csv",
            "e3_trie_vs_linear.csv",
            "e4_early_stop.csv",
            "e4_storage_tradeoff.csv",
            "e5_multipattern.csv",
        ],
    )
    df = read_csv(csv_name)
    if df.empty:
        st.info(f"Chưa tìm thấy {csv_name}.")
    else:
        st.dataframe(df.head(30), hide_index=True, width="stretch")
        if csv_name == "e1_scaling_n.csv":
            render_e1_analysis(df)


def render_conclusion_tab() -> None:
    st.subheader("Kết quả đạt được")
    st.dataframe(
        pd.DataFrame(
            [
                {"Kết quả": "KMP", "Số đo/nhận xét": "Tìm mọi match, kể cả chồng lấn; số phép so sánh bị chặn tuyến tính"},
                {"Kết quả": "Trie", "Số đo/nhận xét": "search/starts_with phụ thuộc độ dài truy vấn, không phụ thuộc trực tiếp N"},
                {"Kết quả": "Autocomplete", "Số đo/nhận xét": "Early stop giúp chỉ duyệt phần cần thiết của cây con"},
                {"Kết quả": "Aho-Corasick", "Số đo/nhận xét": "Có lợi rõ khi số mẫu lớn, tránh chạy KMP lặp lại"},
                {"Kết quả": "Kiểm thử", "Số đo/nhận xét": "README ghi nhận 276 test và 10 doctest đạt"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Ứng dụng và giao diện")
    st.dataframe(
        pd.DataFrame(
            [
                {"Giao diện": "CLI", "Lệnh": "python -m demo.cli --text ... --search ... --json", "Mục đích": "Tái lập kết quả và tích hợp script"},
                {"Giao diện": "Web chuẩn", "Lệnh": "python -m demo.web", "Mục đích": "Minh họa KMP/Trie không cần framework ngoài"},
                {"Giao diện": "Streamlit", "Lệnh": "streamlit run app/streamlit_app.py", "Mục đích": "Trình bày báo cáo và demo tương tác"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Giới hạn và hướng mở rộng")
    st.markdown(
        """
- Trie chưa hỗ trợ `delete` hoặc Trie nén.
- So sánh lưu cạnh bằng mảng mới đo chính với `|Σ| = 26`.
- KMP không tối ưu khi cần tìm nhiều mẫu trên cùng một văn bản.
- Trie hiện chỉ hỗ trợ khớp tiền tố chính xác, chưa xử lý lỗi chính tả.
- Aho-Corasick là phần mở rộng đã cài để tìm nhiều mẫu đồng thời.
"""
    )

    st.subheader("Bài học chính")
    st.markdown(
        """
KMP cho thấy sức mạnh của việc tái sử dụng thông tin biên trong một mẫu.
Trie cho thấy cách chuyển chi phí từ số lượng từ sang độ dài truy vấn bằng cấu trúc tiền tố.
Hai ý tưởng gặp nhau tự nhiên ở Aho-Corasick khi bài toán chuyển từ một mẫu sang nhiều mẫu.
"""
    )


def kmp_trace(text: str, pattern: str) -> list[dict]:
    if not pattern:
        return []

    lps = build_lps(pattern)
    n, m = len(text), len(pattern)
    states: list[dict] = [
        {
            "phase": "start",
            "j": 0 if n else None,
            "i": 0,
            "shift": 0,
            "comparisons": 0,
            "matches": [],
            "message": f"Khởi tạo LPS = {lps}. Bắt đầu so sánh từ T[0] và P[0].",
        }
    ]

    if m > n:
        states.append(
            {
                "phase": "done",
                "j": None,
                "i": 0,
                "shift": 0,
                "comparisons": 0,
                "matches": [],
                "message": "Mẫu dài hơn văn bản nên kết quả rỗng.",
            }
        )
        return states

    i = 0
    comparisons = 0
    matches: list[int] = []

    for j in range(n):
        while True:
            comparisons += 1
            same = text[j] == pattern[i]
            states.append(
                {
                    "phase": "compare",
                    "j": j,
                    "i": i,
                    "shift": j - i,
                    "comparisons": comparisons,
                    "matches": list(matches),
                    "message": (
                        f"So sánh T[{j}] = {text[j]!r} với P[{i}] = {pattern[i]!r}: "
                        + ("khớp, tăng i." if same else "không khớp.")
                    ),
                    "same": same,
                }
            )
            if same:
                i += 1
                if i == m:
                    pos = j - m + 1
                    matches.append(pos)
                    states.append(
                        {
                            "phase": "found",
                            "j": j,
                            "i": m - 1,
                            "shift": pos,
                            "comparisons": comparisons,
                            "matches": list(matches),
                            "message": f"Tìm thấy mẫu tại vị trí {pos}. Giữ lại border dài nhất bằng lps[{m - 1}] = {lps[m - 1]}.",
                            "found_start": pos,
                        }
                    )
                    i = lps[m - 1]
                break

            if i == 0:
                states.append(
                    {
                        "phase": "advance",
                        "j": j,
                        "i": 0,
                        "shift": j,
                        "comparisons": comparisons,
                        "matches": list(matches),
                        "message": "i = 0 nên không còn border để lùi; chuyển sang ký tự tiếp theo của văn bản.",
                    }
                )
                break

            old_i = i
            i = lps[i - 1]
            states.append(
                {
                    "phase": "fallback",
                    "j": j,
                    "i": i,
                    "shift": j - i,
                    "comparisons": comparisons,
                    "matches": list(matches),
                    "message": f"Lùi trong mẫu: i <- lps[{old_i - 1}] = {i}. T[j] không đổi.",
                }
            )

    states.append(
        {
            "phase": "done",
            "j": None,
            "i": i,
            "shift": max(0, n - i),
            "comparisons": comparisons,
            "matches": list(matches),
            "message": f"Kết thúc. Các vị trí khớp: {matches}. Tổng số phép so sánh: {comparisons}.",
        }
    )
    return states


def render_kmp_state(text: str, pattern: str, state: dict) -> None:
    j = state.get("j")
    i = state.get("i", 0)
    shift = state.get("shift", 0)
    found_start = state.get("found_start")
    matches = set(state.get("matches", []))
    same = state.get("same")

    text_cells = []
    pattern_cells = []
    index_cells = []
    for idx, ch in enumerate(text):
        classes = ["viz-cell"]
        if idx == j:
            classes.append("active-match" if same else "active-mismatch")
        if any(pos <= idx < pos + len(pattern) for pos in matches):
            classes.append("matched")
        if found_start is not None and found_start <= idx < found_start + len(pattern):
            classes.append("just-found")
        text_cells.append(f'<div class="{" ".join(classes)}">{html.escape(ch)}</div>')
        index_cells.append(f'<div class="viz-index">{idx}</div>')

        p_idx = idx - shift
        if 0 <= p_idx < len(pattern):
            p_classes = ["viz-cell", "pattern"]
            if p_idx == i and idx == j:
                p_classes.append("active-match" if same else "active-mismatch")
            pattern_cells.append(f'<div class="{" ".join(p_classes)}">{html.escape(pattern[p_idx])}</div>')
        else:
            pattern_cells.append('<div class="viz-cell empty"></div>')

    st.markdown(
        f"""
        <style>
        .kmp-viz-wrap {{
            overflow-x: auto;
            padding: 0.35rem 0 0.7rem;
        }}
        .kmp-viz-row {{
            display: grid;
            grid-template-columns: repeat({max(len(text), 1)}, 2.35rem);
            gap: 0.28rem;
            width: max-content;
            align-items: center;
            margin-bottom: 0.25rem;
        }}
        .viz-cell {{
            height: 2.25rem;
            min-width: 2.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(49, 51, 63, 0.18);
            background: #ffffff;
            color: #111827;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 1rem;
            border-radius: 6px;
        }}
        .viz-cell.pattern {{
            background: #eef6ff;
            color: #111827;
        }}
        .viz-cell.empty {{
            border-color: transparent;
            background: transparent;
        }}
        .viz-index {{
            min-width: 2.25rem;
            text-align: center;
            color: #374151;
            font-size: 0.76rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}
        .viz-cell.active-match {{
            background: #dff7e8;
            border-color: #2e9d5f;
            box-shadow: 0 0 0 2px rgba(46, 157, 95, 0.16);
        }}
        .viz-cell.active-mismatch {{
            background: #ffe8e6;
            border-color: #d4493f;
            box-shadow: 0 0 0 2px rgba(212, 73, 63, 0.14);
        }}
        .viz-cell.matched {{
            background: #fff6cc;
        }}
        .viz-cell.just-found {{
            background: #e8ddff;
            border-color: #7b61d1;
        }}
        @media (max-width: 760px) {{
            .kmp-viz-row {{
                grid-template-columns: repeat({max(len(text), 1)}, 2rem);
                gap: 0.2rem;
            }}
            .viz-cell {{
                min-width: 2rem;
                height: 2rem;
                font-size: 0.9rem;
            }}
        }}
        </style>
        <div class="kmp-viz-wrap">
            <div class="kmp-viz-row">{''.join(index_cells)}</div>
            <div class="kmp-viz-row">{''.join(text_cells)}</div>
            <div class="kmp-viz-row">{''.join(pattern_cells)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_search_visualizer_tab(title: str = "Mô phỏng KMP Search") -> None:
    st.subheader(title)
    st.caption("Xem từng bước so sánh, khớp, mismatch và lùi bằng LPS.")

    default_text = "ababcababababaca"
    default_pattern = "ababaca"

    left, right = st.columns([1.2, 1])
    with left:
        raw_text = st.text_area(
            "Văn bản T",
            value=st.session_state.get("kmp_viz_applied_text", default_text),
            height=92,
            max_chars=500,
            help="Có thể paste đoạn văn tối đa 500 ký tự.",
            key="kmp-viz-input-text",
        )
    with right:
        raw_pattern = st.text_input(
            "Mẫu P",
            value=st.session_state.get("kmp_viz_applied_pattern", default_pattern),
            max_chars=20,
            key="kmp-viz-input-pattern",
        )

    apply_col, status_col, recommend_col = st.columns([1, 4.7, 0.3])
    if apply_col.button(
        "Apply",
        type="primary",
        key="kmp-viz-apply",
    ):
        st.session_state["kmp_viz_applied_text"] = raw_text[:500]
        st.session_state["kmp_viz_applied_pattern"] = raw_pattern
        st.session_state["kmp_viz_signature"] = (raw_text[:500], raw_pattern)
        st.session_state["kmp_viz_step"] = 0

    recommend_col.markdown(
        """
<span title="Recommend: Nhập văn bản T và mẫu P, sau đó bấm Apply để tạo số bước và ô ký tự."
      style="display:inline-flex;align-items:center;justify-content:center;width:1.6rem;height:1.6rem;margin-top:0.3rem;border-radius:999px;border:1px solid #cbd5e1;color:#2563eb;font-weight:700;cursor:help;">ⓘ</span>
""",
        unsafe_allow_html=True,
    )

    if len(raw_text) > 500:
        st.warning("Văn bản dài hơn 500 ký tự; mô phỏng chỉ dùng 500 ký tự đầu.")

    if "kmp_viz_applied_text" not in st.session_state or "kmp_viz_applied_pattern" not in st.session_state:
        status_col.caption("Chưa apply dữ liệu.")
        return

    text = st.session_state["kmp_viz_applied_text"]
    pattern = st.session_state["kmp_viz_applied_pattern"]
    status_col.caption(f"Đang mô phỏng: |T| = {len(text)}, |P| = {len(pattern)}")

    if not pattern:
        st.warning("Nhập mẫu không rỗng rồi bấm Apply để mô phỏng.")
        return
    if not text:
        st.warning("Nhập văn bản rồi bấm Apply để mô phỏng.")
        return

    states = kmp_trace(text, pattern)
    signature = (text, pattern)
    if st.session_state.get("kmp_viz_signature") != signature:
        st.session_state["kmp_viz_signature"] = signature
        st.session_state["kmp_viz_step"] = 0

    current = min(st.session_state.get("kmp_viz_step", 0), len(states) - 1)
    controls = st.columns([1, 1, 1, 5])
    if controls[0].button("◀", key="kmp-prev", help="Bước trước"):
        current = max(0, current - 1)
    if controls[1].button("▶", key="kmp-next", help="Bước sau"):
        current = min(len(states) - 1, current + 1)
    if controls[2].button("Reset", key="kmp-reset"):
        current = 0
    current = controls[3].slider("Bước", 0, len(states) - 1, current)
    st.session_state["kmp_viz_step"] = current

    state = states[current]
    metrics = st.columns(4)
    metrics[0].metric("Bước", f"{current}/{len(states) - 1}")
    metrics[1].metric("j", "-" if state.get("j") is None else state.get("j"))
    metrics[2].metric("i", state.get("i", 0))
    metrics[3].metric("So sánh", state.get("comparisons", 0))

    render_kmp_state(text, pattern, state)
    st.info(state["message"])
    st.dataframe(
        pd.DataFrame(
            {
                "LPS index": list(range(len(pattern))),
                "P[i]": list(pattern),
                "LPS[i]": build_lps(pattern),
            }
        ),
        hide_index=True,
        width="stretch",
    )


def render_kmp_demo() -> None:
    if not require_source():
        return

    st.subheader("Demo KMP")
    text = st.text_area("Văn bản", value="ababcababababaca", height=130)
    pattern = st.text_input("Mẫu", value="abab")
    overlapping = st.checkbox("Tính cả khớp chồng lấn", value=True)

    if not pattern:
        st.warning("Nhập mẫu không rỗng để chạy KMP.")
        return

    counter = OpCounter()
    try:
        lps = build_lps(pattern, counter)
        positions = kmp_search(text, pattern, counter, overlapping=overlapping, lps=lps)
    except ValueError as exc:
        st.error(str(exc))
        return

    cols = st.columns(4)
    cols[0].metric("Số match", len(positions))
    cols[1].metric("Độ dài văn bản", len(text))
    cols[2].metric("Độ dài mẫu", len(pattern))
    cols[3].metric("So sánh ký tự", counter.char_comparisons)

    st.dataframe(
        pd.DataFrame({"i": list(range(len(pattern))), "P[i]": list(pattern), "LPS[i]": lps}),
        hide_index=True,
        width="stretch",
    )
    st.write("Vị trí khớp:", positions)


def build_demo_trie(words_blob: str, alphabet_name: str) -> tuple[Any, list[str]]:
    alphabet = get_alphabet(alphabet_name)
    trie = Trie(alphabet)
    rejected: list[str] = []
    for raw in words_blob.splitlines():
        word = normalize_unicode(raw.strip().lower())
        if not word:
            continue
        try:
            trie.insert(word)
        except ValueError:
            rejected.append(word)
    return trie, rejected


def render_trie_demo() -> None:
    if not require_source():
        return

    st.subheader("Demo Trie")
    c1, c2 = st.columns([1, 1])
    with c1:
        alphabet_name = st.selectbox("Bảng chữ cái", sorted(ALPHABETS), index=sorted(ALPHABETS).index("ascii_lower"))
        prefix = normalize_unicode(st.text_input("Tiền tố autocomplete", value="ti").strip().lower())
        exact = normalize_unicode(st.text_input("Từ cần search", value="tin").strip().lower())
        k = st.slider("Số gợi ý tối đa", 1, 20, 5)
    with c2:
        words_blob = st.text_area("Từ điển demo", value=read_demo_words(), height=220)

    trie, rejected = build_demo_trie(words_blob, alphabet_name)
    result = trie.autocomplete(prefix, k)

    cols = st.columns(4)
    cols[0].metric("Từ phân biệt", trie.num_words)
    cols[1].metric("Số nút", trie.num_nodes)
    cols[2].metric("Exact search", "Có" if trie.search(exact) else "Không")
    cols[3].metric("Truncated", "Có" if result.truncated else "Không")

    st.dataframe(
        pd.DataFrame({"Gợi ý": result.suggestions}),
        hide_index=True,
        width="stretch",
    )
    st.caption(f"Có {trie.count_with_prefix(prefix)} lượt insert mang tiền tố {prefix!r}.")
    if rejected:
        st.warning(f"Bỏ qua {len(rejected)} từ không thuộc bảng chữ cái đã chọn: {', '.join(rejected[:8])}")


def render_aho_demo() -> None:
    if not require_source():
        return

    st.subheader("Demo Aho-Corasick")
    patterns_blob = st.text_area("Mỗi dòng một mẫu", value="he\nshe\nhis\nhers", height=120)
    text = st.text_area("Văn bản", value="ushers and his shell", height=120, key="aho-text")
    patterns = [line.strip() for line in patterns_blob.splitlines() if line.strip()]
    if not patterns:
        st.warning("Nhập ít nhất một mẫu.")
        return

    try:
        ac = AhoCorasick(patterns)
    except ValueError as exc:
        st.error(str(exc))
        return

    counter = OpCounter()
    matches = ac.search(text, counter)
    cols = st.columns(3)
    cols[0].metric("Số mẫu", len(patterns))
    cols[1].metric("Số nút", ac.num_nodes)
    cols[2].metric("Số match", len(matches))

    st.dataframe(
        pd.DataFrame([m.to_dict() for m in matches]),
        hide_index=True,
        width="stretch",
    )
    st.write("Failure depths theo BFS:", ac.failure_array())


def render_demo_tab() -> None:
    st.subheader("Demo tương tác từ source KMP-Trie")
    st.caption(f"Source đang dùng: {KMP_REPO}")
    demo_default = set_default_tab_from_route("demo_tab", DEMO_TAB_LABELS, DEMO_ROUTE_TABS, "demo", "kmp")
    kmp_tab, trie_tab, aho_tab = st.tabs(
        DEMO_TAB_LABELS,
        default=demo_default,
        key="demo_tab",
    )
    with kmp_tab:
        render_kmp_demo()
    with trie_tab:
        render_trie_demo()
    with aho_tab:
        render_aho_demo()


def main() -> None:
    st.set_page_config(page_title="KMP & Trie Report", layout="wide")
    inject_responsive_styles()
    st.title("KMP & Trie")
    st.caption("Dashboard báo cáo chuyên đề: cài đặt, chứng minh, kiểm thử và thực nghiệm")

    main_default = set_default_tab_from_route("main_tab", MAIN_TAB_LABELS, MAIN_ROUTE_TABS, "tab", "gioi-thieu")
    tabs = st.tabs(
        MAIN_TAB_LABELS,
        default=main_default,
        key="main_tab",
    )
    renderers = [
        render_overview_tab,
        render_theory_tab,
        render_algorithm_tab,
        render_experiments_tab,
        render_conclusion_tab,
        render_demo_tab,
    ]
    for tab, render in zip(tabs, renderers):
        with tab:
            render()


if __name__ == "__main__":
    main()
