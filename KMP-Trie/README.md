# KMP và Trie: cài đặt, kiểm thử và thực nghiệm

Đây là mã nguồn cho Chuyên đề 10 về xử lý chuỗi bằng KMP và Trie. Kho mã
gồm phần cài đặt, các cách làm đơn giản dùng để đối chiếu kết quả, bộ kiểm thử,
dữ liệu sinh từ giá trị khởi tạo ngẫu nhiên (`seed`) cố định và các lệnh để
chạy lại bảng số liệu, biểu đồ.

## Câu hỏi nghiên cứu

1. Khi loại văn bản và độ dài mẫu thay đổi, số phép so sánh của KMP có còn
   tăng tuyến tính theo kích thước đầu vào không?
2. Thời gian tìm chính xác và tìm theo tiền tố của Trie có phụ thuộc vào số từ
   `N` không? Việc nhiều từ chung tiền tố tiết kiệm bao nhiêu nút?
3. Khi autocomplete dừng ngay sau khi đủ `k` kết quả, nó bớt duyệt bao nhiêu
   nút?
4. Khi nào Aho–Corasick có lợi hơn việc chạy KMP cho từng mẫu?

KMP và Trie là hai mô-đun độc lập. `src/kmp/` không import `src/trie/` và ngược
lại; chúng chỉ được ghép ở tầng demo. Aho–Corasick là phần mở rộng nhiều mẫu.

## Chạy nhanh

Yêu cầu: Python 3.10+, XeLaTeX/latexmk để dựng báo cáo, Node.js 18+ và
LibreOffice nếu cần dựng PPTX/PDF thuyết trình.

```bash
python -m pip install -r requirements.txt
npm ci

python -m pytest tests/ -q
python -m pytest --doctest-modules src/ tests/baseline.py -q
python -m demo.web --self-test
```

Kết quả kiểm chứng hiện tại: **276 phép kiểm thử và 10 doctest đều đạt**.

## Chạy demo và định dạng vào–ra

CLI nhận văn bản UTF-8 bằng `--text`, từ điển UTF-8 một từ mỗi dòng bằng
`--dict`, và có thể xuất JSON ổn định bằng `--json`:

```bash
# KMP: tìm mọi vị trí 0-based, kể cả chồng lấn
python -m demo.cli \
  --text data/small/demo_corpus.txt \
  --search abab --json

# Trie: tối đa 5 gợi ý theo thứ tự từ điển
python -m demo.cli \
  --dict data/dictionaries/demo_words.txt \
  --alphabet ascii_lower \
  --suggest ti -k 5 --json

# Web demo, sau đó mở http://localhost:8000
python -m demo.web
```

Kết quả KMP có `pattern`, `positions`, `count`, `lps`,
`char_comparisons`; kết quả Trie có `prefix`, `suggestions`, `truncated` và
`nodes_visited`. Xem toàn bộ tham số bằng `python -m demo.cli --help`.

## Chạy lại thực nghiệm

```bash
# Dữ liệu đầy đủ, seed mặc định 20260728; MANIFEST chứa SHA-256 từng tệp
python scripts/gen_data.py

# Năm thí nghiệm; mọi phép đo thời gian lặp 7 lần + 1 warmup
python scripts/run_benchmark.py --repeat 7
python scripts/plot_results.py
```

Có thể chạy riêng một thí nghiệm:

```bash
python scripts/run_benchmark.py --repeat 7 --only 1
python scripts/run_benchmark.py --repeat 7 --only 3 \
  --dict-sizes 1000,5000,20000,100000,500000
```

Mỗi CSV nằm trong `results/benchmarks/`; môi trường và đơn vị đo nằm trong
`results/benchmarks/environment.json`. Biểu đồ được sinh vào `results/figures/`.
Nhãn `natural` chỉ dữ liệu tổng hợp có phân bố Zipf để mô phỏng ngôn ngữ tự
nhiên, không phải văn bản thu thập ngoài đời; kết luận chỉ áp dụng cho mô hình
dữ liệu này.

## Đầu vào, đầu ra và độ phức tạp

### KMP

- `build_lps(pattern)` công khai mảng prefix/LPS.
- `kmp_search(text, pattern)` trả mọi vị trí 0-based, kể cả chồng lấn.
- Mẫu rỗng bị từ chối bằng `ValueError`; mẫu dài hơn văn bản trả `[]`.
- Thời gian `O(n+m)`, bộ nhớ phụ `O(m)`.
- Phép đo ghi riêng thời gian tạo mảng LPS, thời gian tìm trên đối tượng đã có
  LPS và tổng thời gian của cả hai bước.

### Trie

- Có `insert`, `search`, `starts_with`, `autocomplete(prefix, k)`.
- `insert` kiểm tra toàn bộ từ theo bảng chữ cái đã chọn trước khi sửa cây, nên
  từ không hợp lệ không làm thay đổi Trie.
- Kết quả autocomplete tăng theo thứ tự từ điển và có cờ `truncated`.
- Phép duyệt theo chiều sâu dùng ngăn xếp và chỉ lưu một đường đi dùng chung,
  không sao chép cả chuỗi tại mỗi cạnh.
- Với `V` nút thực sự duyệt, thời gian là
  `O(|q| + V·|Σ|log|Σ| + k·L_max)`; khi bảng chữ cái cố định, phần chính rút
  gọn thành `O(|q| + V + k·L_max)`.

## Cách kiểm tra kết quả

- KMP được so với cách tìm vét cạn `O(n·m)`, `str.find` và mảng LPS tính trực
  tiếp từ định nghĩa.
- Kết quả Trie được so với cách lọc danh sách bằng `startswith` rồi sắp xếp.
- Khi đo tốc độ Trie, cách đối chiếu nhận sẵn danh sách đã sắp và loại trùng,
  sau đó quét đến kết quả thứ `k+1`; thời gian đo không gồm `set` hoặc `sort`.
- Aho–Corasick được so với cách chạy tìm kiếm riêng cho từng mẫu rồi gộp kết
  quả.

Test được chia thành:

- `tests/unit/`: trường hợp cơ bản và biên;
- `tests/adversarial/`: dữ liệu được thiết kế để tấn công giả thiết/cận;
- `tests/random/`: đối chiếu ngẫu nhiên với seed cố định.

## Kết quả hiện tại

Môi trường đo: CPython 3.11.9, macOS arm64, trung vị 7 lần.

| Kết quả | Số đo |
|---|---:|
| KMP trên đầu vào đối kháng | tối đa `1.9999·n` phép so sánh |
| BUILD_LPS | tối đa `1.997·m` phép so sánh |
| Trie tìm chính xác, `N=10³…5·10⁵` | 6–10 nút, bằng độ dài từ |
| Trie so với quét tuyến tính, dữ liệu tổng hợp `N=500 000` | `1 062×` trong cấu hình đo |
| Chia sẻ tiền tố, dữ liệu tổng hợp `N=500 000` | `0.260` nút/ký tự |
| Autocomplete `k=1` | 6/7 596 nút của cây con |
| Trie dùng mảng / Trie dùng bảng băm, `|Σ|=26` | `1.50–1.53×` bộ nhớ |
| Aho–Corasick, 100 mẫu | `70.4×` ít phép so sánh hơn KMP lặp |

Các tỉ số thời gian chỉ có ý nghĩa trong đúng môi trường và dữ liệu đã ghi.
Số đếm thao tác và xu hướng tiệm cận là bằng chứng chính.

## Cấu trúc repository

```text
src/                    cài đặt KMP, Trie, Aho–Corasick và tiện ích
tests/                  kiểm thử cơ bản, ca khó và đối chiếu ngẫu nhiên
data/                   văn bản/từ điển sinh từ seed và SHA-256 trong MANIFEST
scripts/                sinh dữ liệu, chạy phép đo, vẽ biểu đồ
results/benchmarks/     CSV và environment.json
results/figures/        biểu đồ tái sinh từ CSV
demo/                   CLI và web demo dùng thư viện chuẩn
report/latex/           nguồn LaTeX cá nhân theo mẫu quy định
report/                 PDF cá nhân và nguồn LaTeX chính thức
slides/                 PPTX/PDF thuyết trình nhóm + source build
docs/                   đề bài gốc
```

## Giới hạn

- Trie chưa hỗ trợ `delete` hoặc Trie nén.
- Phép đo quét tuyến tính giả thiết danh sách đã sắp và loại trùng.
- So sánh cách lưu cạnh bằng bảng băm và bằng mảng mới được đo với `|Σ|=26`.
- KMP không phải lựa chọn tối ưu khi cần tìm nhiều mẫu trên cùng một văn bản.
- Trie hiện chỉ hỗ trợ khớp tiền tố chính xác, không xử lý lỗi chính tả.

Tóm lại, KMP phù hợp để tìm một mẫu trong văn bản; Trie phù hợp để tra từ và
gợi ý theo tiền tố; Aho–Corasick là phần mở rộng khi cần tìm nhiều mẫu cùng
lúc.
