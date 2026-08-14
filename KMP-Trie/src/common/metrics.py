"""Đo lường cho phần thực nghiệm.

Vì nhóm chọn Python thay vì C++17 (khuyến nghị của đề), phần thực nghiệm phải
được củng cố bằng các chỉ số **độc lập ngôn ngữ**:

  - `char_comparisons`: số phép so sánh ký tự. Đây là bằng chứng chính cho
    lập luận khấu hao O(n+m) của KMP: tỉ số comparisons/n phải bị chặn bởi
    một hằng số khi n tăng, trong khi với naive tỉ số này tăng theo m.
  - `nodes_visited` / `nodes_created`: số nút Trie duyệt/tạo — chứng thực
    autocomplete dừng sớm và chi phí insert tỉ lệ độ dài chuỗi.

Thời gian tường (wall time) vẫn được đo, nhưng chỉ dùng để so sánh tương đối
trong cùng một môi trường, và luôn báo cáo trung vị của nhiều lần lặp.
"""

from __future__ import annotations

import platform
import statistics
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

__all__ = ["OpCounter", "TimingResult", "measure", "environment_info"]


@dataclass
class OpCounter:
    """Bộ đếm thao tác đặc trưng.

    Được truyền tường minh vào thuật toán (dependency injection) thay vì dùng
    biến toàn cục, để việc đếm không gây tác dụng phụ giữa các phép đo và để
    có thể tắt hoàn toàn (truyền None) khi đo thời gian thuần.
    """

    char_comparisons: int = 0
    nodes_visited: int = 0
    nodes_created: int = 0
    lps_comparisons: int = 0

    def reset(self) -> None:
        self.char_comparisons = 0
        self.nodes_visited = 0
        self.nodes_created = 0
        self.lps_comparisons = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass
class TimingResult:
    """Kết quả đo thời gian của một cấu hình.

    Đề cảnh báo: "không chỉ chụp một lần chạy" — nên mọi phép đo đều lặp
    `repeat` lần và báo cáo trung vị cùng độ phân tán.
    """

    repeat: int
    times_ns: list[int] = field(default_factory=list)
    peak_mem_bytes: int = 0
    result: Any = None

    @property
    def median_ns(self) -> float:
        return statistics.median(self.times_ns)

    @property
    def min_ns(self) -> int:
        return min(self.times_ns)

    @property
    def mean_ns(self) -> float:
        return statistics.fmean(self.times_ns)

    @property
    def stdev_ns(self) -> float:
        return statistics.stdev(self.times_ns) if len(self.times_ns) > 1 else 0.0

    @property
    def relative_spread(self) -> float:
        """Độ lệch chuẩn / trung vị — dùng để đánh giá phép đo có ổn định không."""
        med = self.median_ns
        return self.stdev_ns / med if med else 0.0

    def summary(self) -> dict[str, float]:
        return {
            "repeat": self.repeat,
            "median_ns": self.median_ns,
            "min_ns": self.min_ns,
            "mean_ns": self.mean_ns,
            "stdev_ns": self.stdev_ns,
            "relative_spread": self.relative_spread,
            "peak_mem_bytes": self.peak_mem_bytes,
        }


def measure(
    func: Callable[[], Any],
    repeat: int = 5,
    warmup: int = 1,
    track_memory: bool = False,
) -> TimingResult:
    """Đo `func` bằng perf_counter_ns, lặp `repeat` lần.

    Args:
        func: hàm không tham số (dùng lambda/partial để đóng gói tham số).
        repeat: số lần lặp; đề yêu cầu nhiều hơn một lần chạy.
        warmup: số lần chạy bỏ đi trước khi đo, để làm nóng cache và loại
            ảnh hưởng của lần cấp phát đầu tiên.
        track_memory: nếu True, đo thêm bộ nhớ đỉnh bằng tracemalloc. Việc này
            làm chậm đáng kể nên được đo trong một lần chạy riêng, không trộn
            vào số liệu thời gian.

    Returns:
        TimingResult với danh sách thời gian, bộ nhớ đỉnh và kết quả cuối cùng.
    """
    if repeat < 1:
        raise ValueError("repeat phải ≥ 1")

    for _ in range(warmup):
        func()

    times: list[int] = []
    result = None
    for _ in range(repeat):
        start = time.perf_counter_ns()
        result = func()
        times.append(time.perf_counter_ns() - start)

    peak = 0
    if track_memory:
        tracemalloc.start()
        func()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    return TimingResult(
        repeat=repeat, times_ns=times, peak_mem_bytes=peak, result=result
    )


def environment_info() -> dict[str, str]:
    """Thông tin môi trường chạy.

    Checklist của đề: "Kết quả thực nghiệm có môi trường chạy, kích thước dữ
    liệu và đơn vị đo." Hàm này được gọi và ghi vào mọi tệp kết quả.
    """
    return {
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "timer": "time.perf_counter_ns",
        "timer_resolution_ns": str(time.get_clock_info("perf_counter").resolution * 1e9),
    }
