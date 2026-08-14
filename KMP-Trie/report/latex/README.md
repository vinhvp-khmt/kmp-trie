# Báo cáo LaTeX — Chuyên đề 10

Đây là nguồn chính thức của báo cáo cá nhân **Huỳnh Phát Lợi**. Hệ thống
layout được kế thừa trực tiếp từ `latex-template-vn`:

- `extreport`, cỡ chữ thân bài 13pt;
- Times New Roman, fallback TeX Gyre Termes;
- lề trên 3cm, dưới 3cm, trái 3cm, phải 2cm;
- giãn dòng 1,5; thụt đầu dòng 1,25cm;
- số trang giữa đầu trang, không có đường kẻ;
- chương dạng `CHƯƠNG n : TÊN CHƯƠNG IN HOA`;
- mục 16pt, tiểu mục 15pt;
- caption và số hình/bảng/công thức theo chương;
- tài liệu tham khảo IEEEtran;
- hai trang bìa, gồm khung chấm điểm và bìa lót có vị trí dành cho logo.

## Build

Từ thư mục gốc repository:

```bash
bash report/latex/build/make.sh
```

Hoặc chạy trực tiếp:

```bash
cd report/latex
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

PDF nộp được ghi tại `report/BAO-CAO-CHUYEN-DE-10.pdf`.

## Chỉnh nội dung

- Thông tin bìa: `config/metadata.tex`.
- Lời cam đoan, cảm ơn, tóm tắt: `frontmatter/`.
- Nội dung tám chương: `chapters/report_content.tex`.
- Phụ lục: `appendices/appendix_resources.tex`.
- Tài liệu tham khảo: `references.bib`.

LaTeX là nguồn duy nhất của báo cáo. Không duy trì một bản DOCX song song,
vì hai nguồn nội dung độc lập rất dễ lệch số liệu sau mỗi lần chạy benchmark.
