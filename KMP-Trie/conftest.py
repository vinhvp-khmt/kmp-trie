"""Cấu hình pytest: đưa thư mục gốc của đồ án vào sys.path.

Nhờ tệp này, mọi test import được `src.*` và `tests.baseline` mà KHÔNG cần
cài đặt package hay đặt biến môi trường PYTHONPATH — đáp ứng checklist của đề:
"Mã nguồn chạy lại được theo README; không phụ thuộc đường dẫn cá nhân."
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
