/**
 * Dựng slide thuyết trình kèm speaker notes cho từng slide.
 *
 * Bài nói 10–15 phút theo yêu cầu của đề. 18 slide, mỗi slide có phần notes
 * viết sẵn thành lời nói liền mạch để đọc thẳng khi trình bày.
 *
 * Bảng màu "Ocean Gradient": nền tối cho slide mở/đóng và các slide bước
 * chuyển, nền sáng cho slide nội dung.
 *
 * Chạy:  node slides/build/deck.js
 */

const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

const ROOT = path.join(__dirname, "..", "..");
const FIG = (n) => path.join(ROOT, "results", "figures", n);
const OUT = path.join(ROOT, "slides", "SLIDE-CHUYEN-DE-10.pptx");

// --- Bảng màu ---------------------------------------------------------------
const DEEP = "21295C";   // nền tối
const BLUE = "065A82";   // xanh chủ đạo
const TEAL = "1C7293";   // xanh phụ
const MINT = "5BC0BE";   // nhấn sáng
const GOLD = "E8A33D";   // nhấn cảnh báo / số liệu
const INK = "1B2430";    // chữ trên nền sáng
const GREY = "6B7280";   // chữ phụ
const PAPER = "FFFFFF";
const TINT = "EEF3F8";   // nền khối nội dung

const H_FONT = "Times New Roman";
const B_FONT = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";              // 13.3 x 7.5 inch
pres.author = "Huỳnh Phát Lợi";
pres.title = "Chuyên đề 10 — KMP và Trie";

const W = 13.3, HT = 7.5, M = 0.6;
const TEAM = [
  {
    name: "Huỳnh Phát Lợi",
    role: "Trưởng nhóm · KMP · tích hợp",
    work: "Thiết kế kiến trúc; build_lps, kmp_search; Aho–Corasick; CLI/Web demo",
  },
  {
    name: "Võ Phú Vinh",
    role: "Lý thuyết · báo cáo",
    work: "Định nghĩa, chứng minh tính đúng, phân tích khấu hao; biên tập nội dung trình bày",
  },
  {
    name: "Thanh Tú",
    role: "Trie · kiểm thử · thực nghiệm",
    work: "Trie/autocomplete; baseline; test biên/đối kháng/ngẫu nhiên; benchmark và biểu đồ",
  },
];

// Notes được viết cho nhịp nói 10–15 phút. Tên người nói nằm ngay đầu
// từng note để PowerPoint Presenter View hỗ trợ chuyển lượt rõ ràng.
const SPEAKER_NOTES = [
  `[HUỲNH PHÁT LỢI — khoảng 40 giây]
Kính chào thầy và các bạn. Nhóm em trình bày chuyên đề 10: xử lý chuỗi bằng KMP và Trie. Sản phẩm là một hệ thống nhỏ: người dùng gõ tiền tố, Trie đề xuất từ khóa; sau khi chọn, KMP tìm mọi vị trí của từ khóa trong văn bản. Bài nói đi từ bài toán và chứng minh, sang demo, kiểm thử, thực nghiệm rồi kết luận. Em xin bắt đầu bằng phần phân công.`,

  `[HUỲNH PHÁT LỢI — khoảng 35 giây]
Nhóm có ba thành viên và đây là trách nhiệm chính, không phải ba phần tách rời. Em phụ trách KMP, tích hợp và demo; Võ Phú Vinh phụ trách lý thuyết, chứng minh và biên tập báo cáo; Thanh Tú phụ trách Trie, kiểm thử và thực nghiệm. Cả ba cùng review mã lõi và số liệu để có thể trả lời chéo. Báo cáo cá nhân chỉ ghi phần đóng góp của người nộp; bảng này là nơi công bố đầy đủ phân công nhóm.`,

  `[HUỲNH PHÁT LỢI — khoảng 40 giây]
Hai bài toán đều liên quan đến chuỗi nhưng khác ở dữ liệu biết trước. Với tìm mẫu, ta tiền xử lý mẫu và dùng KMP. Với gợi ý, từ điển đã có sẵn nên ta tiền xử lý toàn bộ từ điển bằng Trie. Sự khác biệt này quyết định cấu trúc dữ liệu và cả độ phức tạp. Trong mã nguồn, hai module độc lập, không import lẫn nhau; chúng chỉ gặp nhau ở tầng ứng dụng.`,

  `[HUỲNH PHÁT LỢI — khoảng 45 giây]
Module A nhận văn bản T và mẫu P không rỗng, trả về tất cả vị trí khớp, kể cả các lần khớp chồng lấn. Module B nhận một từ điển và cung cấp insert, search, starts_with, autocomplete. Hợp đồng lỗi cũng được xác định: mẫu rỗng hoặc ký tự ngoài alphabet bị từ chối rõ ràng. Điểm cần nhớ là KMP đạt O(n+m), còn thao tác Trie phụ thuộc độ dài chuỗi chứ không phụ thuộc số từ. Sau đây Vinh trình bày phần chứng minh.`,

  `[VÕ PHÚ VINH — khoảng 50 giây]
Prefix function tại vị trí i là độ dài border dài nhất của tiền tố kết thúc ở i. Khi có mismatch sau j ký tự, ta không thử lại từ đầu mà chuyển j về π[j−1], tức border dài nhất vẫn có thể tiếp tục. Ví dụ trên slide cho thấy thông tin của các lần so khớp trước được giữ lại. Đây là lý do KMP tránh lặp lại phép so sánh mà naive thường thực hiện.`,

  `[VÕ PHÚ VINH — khoảng 50 giây]
Bất biến của vòng lặp là trước mỗi lần so sánh, P[0..j−1] khớp với hậu tố của phần văn bản đã đọc. Khi mismatch, π[j−1] cho biết border dài nhất còn hợp lệ nên chỉ j lùi, còn con trỏ văn bản không lùi. Khi hai ký tự bằng nhau, cả hai con trỏ tiến. Bất biến vừa chứng minh không bỏ sót kết quả, vừa giải thích trực tiếp vì sao mỗi ký tự văn bản không bị quét lại từ đầu.`,

  `[VÕ PHÚ VINH — khoảng 45 giây]
Sau khi tìm thấy một khớp đầy đủ, dòng j bằng π[m−1] là bắt buộc nếu muốn bắt các khớp chồng lấn. Với mẫu “aba” trong “ababa”, lần khớp đầu kết thúc nhưng hậu tố “a” cũng là tiền tố của mẫu, nên ta giữ trạng thái đó. Nếu đặt j về 0, kết quả ở vị trí 2 sẽ bị bỏ lỡ. Đây là một ca kiểm thử riêng trong dự án.`,

  `[VÕ PHÚ VINH — khoảng 50 giây]
Chặn tuyến tính dùng lập luận khấu hao. Mỗi lần so sánh thành công làm j tăng; mỗi vòng mismatch làm j giảm theo prefix function. Tổng số lần giảm không thể vượt tổng số lần tăng, nên tìm kiếm dùng không quá khoảng 2n phép so sánh. BUILD_LPS có lập luận tương tự với m. Vì vậy tổng là O(n+m), không phải chỉ là kết luận từ biểu đồ. Em chuyển sang Tú với Trie và kiểm thử.`,

  `[THANH TÚ — khoảng 50 giây]
Trie được mô tả bởi bốn bất biến: mỗi cạnh mang đúng một ký tự; đường từ gốc tạo thành một tiền tố; nút kết thúc đánh dấu đúng một từ đã chèn; và các từ chung tiền tố dùng chung đường đi. Insert duy trì các bất biến bằng cách chỉ tạo cạnh còn thiếu. Search đi đúng một đường nên chi phí là O(L), với L là độ dài từ, độc lập số lượng từ N.`,

  `[THANH TÚ — khoảng 45 giây]
Autocomplete trước hết đi đến nút của tiền tố trong O(|p|), sau đó DFS theo thứ tự ổn định và dừng ngay khi đủ k kết quả. Vì thế chi phí là O(|p|+V), trong đó V là số nút thật sự đã thăm, không phải toàn bộ cây. Tham số k âm bị từ chối nhất quán ở cả biến thể hash map và mảng; đây là trường hợp biên vừa được bổ sung vào bộ test.`,

  `[THANH TÚ — khoảng 65 giây]
Đây là điểm chuyển sang demo. Em sẽ chạy hai thao tác: gõ tiền tố để nhận tối đa k gợi ý, rồi chọn một gợi ý để KMP tìm mọi vị trí trong văn bản. Khi demo, xin chú ý ba điều: kết quả autocomplete dừng đúng k; KMP trả về cả vị trí overlapping; và đầu vào sai được báo lỗi thay vì làm hỏng cấu trúc. Nếu giao diện gặp sự cố, cùng luồng này có thể chạy bằng CLI với dữ liệu mẫu trong thư mục data/demo.`,

  `[THANH TÚ — khoảng 45 giây]
Bộ kiểm thử có 276 test tự động và 10 doctest. Ba nhóm chính gồm unit và biên, đối kháng, cùng ngẫu nhiên đối chiếu. KMP được so với cách tìm naive độc lập; Trie được so với tập hợp và lọc tuyến tính; Aho–Corasick được so với việc chạy KMP cho từng mẫu. Nhờ baseline độc lập, test không chỉ kiểm tra mã chạy được mà còn kiểm tra kết quả đúng.`,

  `[THANH TÚ — khoảng 45 giây]
Test đối kháng được chọn để tấn công giả định cụ thể. Chuỗi Fibonacci tạo dãy border dài, ép KMP nhiều lần lùi và kiểm tra chặn 2n. Cây “chổi” có nhiều từ chung tiền tố dài để kiểm tra early stop. Ký tự ngoài alphabet đặt ở cuối một từ dài kiểm tra insert thất bại nhưng không làm bẩn Trie. Seed cố định giúp tái tạo đúng các ca ngẫu nhiên.`,

  `[THANH TÚ — khoảng 45 giây]
E1 đo số phép so sánh thay vì chỉ đo thời gian. Trường hợp uniform gần đạt 2n, cụ thể khoảng 1,9999n, cho thấy chặn lý thuyết vừa đúng vừa gần chặt. Trên dữ liệu natural-like tổng hợp theo Zipf hoặc random với alphabet lớn, naive cũng gần tuyến tính nên KMP không luôn nhanh hơn nhiều. Kết quả này được giữ nguyên vì nó mô tả đúng điều kiện KMP tạo lợi thế.`,

  `[THANH TÚ — khoảng 40 giây]
Biểu đồ chuẩn hóa số phép so sánh theo n làm xu hướng rõ hơn số mili-giây. Đường KMP bị chặn quanh 2 và hầu như phẳng khi n tăng; naive tăng mạnh trên dữ liệu lặp. “Natural” ở đây là nhãn cho dữ liệu tổng hợp theo Zipf, không phải corpus tự nhiên thu thập từ bên ngoài. Việc ghi rõ nguồn dữ liệu tránh diễn giải quá mức kết quả.`,

  `[THANH TÚ — khoảng 50 giây]
E2 xác nhận khi độ dài mẫu tăng 1.024 lần, chi phí tìm kiếm KMP chuẩn hóa theo n gần như giữ nguyên. E3 tăng từ điển 500 lần nhưng search Trie vẫn chỉ duyệt khoảng 6 đến 10 nút, bằng độ dài từ. Với autocomplete, số nút thăm chủ yếu phụ thuộc k. Biến thể mảng dùng khoảng 1,50 đến 1,53 lần bộ nhớ của hash map ở alphabet 26; kết luận cho alphabet 105 vẫn là giới hạn cần đo thêm. Em chuyển lại cho Lợi.`,

  `[HUỲNH PHÁT LỢI — khoảng 50 giây]
Aho–Corasick là phần mở rộng nối hai ý tưởng: cấu trúc Trie lưu nhiều mẫu, còn failure link tổng quát hóa prefix function của KMP. Khi số mẫu tăng từ 1 lên 100, số phép so sánh chỉ tăng nhẹ; chạy KMP lặp lại tăng gần tuyến tính theo số mẫu. Tuy vậy với đúng một mẫu, KMP vẫn phù hợp hơn vì Aho–Corasick có chi phí dựng cấu trúc. Mở rộng này chứng minh hai module có thể tích hợp mà không phá vỡ thiết kế độc lập.`,

  `[HUỲNH PHÁT LỢI — khoảng 55 giây]
Nhóm hoàn thành hai module độc lập, demo CLI và web, 276 test cùng 10 doctest, năm nhóm thực nghiệm và pipeline tái lập bằng seed cùng SHA-256. Kết quả chính là các chặn 2n và 2m được kiểm chứng, search Trie độc lập N, và Aho–Corasick có lợi khi có nhiều mẫu. Giới hạn còn lại là đo trên CPython, dữ liệu natural-like tổng hợp, và trade-off alphabet mới đo ở 26 ký tự. Cảm ơn thầy và các bạn; nhóm em sẵn sàng trả lời câu hỏi.`,
];

function addSpeakerNotes(slide, slideNumber) {
  const note = SPEAKER_NOTES[slideNumber - 1];
  if (!note) throw new Error(`Missing speaker note for slide ${slideNumber}`);
  slide.addNotes(note);
}

// --- Tiện ích ---------------------------------------------------------------

/** Slide nền tối, dùng cho mở đầu, bước chuyển và kết luận. */
function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: DEEP };
  return s;
}

/** Slide nội dung nền sáng, có tiêu đề ở trên. */
function contentSlide(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: M, y: 0.34, w: 8, h: 0.28, fontSize: 11, bold: true,
      color: TEAL, fontFace: B_FONT, charSpacing: 1.6, margin: 0,
    });
  }
  s.addText(title, {
    x: M, y: kicker ? 0.62 : 0.5, w: W - 2 * M, h: 0.8,
    fontSize: 30, bold: true, color: INK, fontFace: H_FONT, margin: 0,
  });
  return s;
}

/** Khối số liệu lớn — dùng cho các con số cần nhớ. */
function stat(s, x, y, w, value, label, color) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h: 1.5, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText(value, {
    x, y: y + 0.16, w, h: 0.75, fontSize: 34, bold: true,
    color: color || BLUE, align: "center", fontFace: H_FONT, margin: 0,
  });
  s.addText(label, {
    x: x + 0.1, y: y + 0.92, w: w - 0.2, h: 0.5, fontSize: 11,
    color: GREY, align: "center", fontFace: B_FONT, margin: 0,
  });
}

/** Bảng gọn, canh trái cột đầu. */
function tbl(s, rows, opts = {}) {
  s.addTable(rows, {
    x: opts.x ?? M, y: opts.y ?? 1.7, w: opts.w ?? (W - 2 * M),
    colW: opts.colW,
    fontSize: opts.fontSize ?? 13, fontFace: B_FONT, color: INK,
    border: { type: "solid", pt: 0.5, color: "D3DCE6" },
    fill: { color: PAPER },
    autoPage: false,
    rowH: opts.rowH ?? 0.32,
    valign: "middle",
  });
}

function headerRow(cells) {
  return cells.map((t) => ({
    text: t,
    options: { bold: true, color: PAPER, fill: { color: BLUE }, fontSize: 12 },
  }));
}

function row(cells, opts = {}) {
  return cells.map((t, i) => ({
    text: String(t),
    options: {
      align: i === 0 ? "left" : (opts.align || "center"),
      bold: opts.bold && i === 0,
      color: opts.color || INK,
      fill: { color: opts.fill || PAPER },
    },
  }));
}

/** Khối mã / mã giả trên nền tối nhạt. */
function code(s, x, y, w, h, lines, fontSize = 12) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: "10233A" }, line: { color: "10233A" },
  });
  s.addText(lines.map((t, i) => ({
    text: t || " ",
    options: { breakLine: i < lines.length - 1 },
  })), {
    x: x + 0.18, y: y + 0.12, w: w - 0.36, h: h - 0.24,
    fontSize, fontFace: "Courier New", color: "D7E3F4", margin: 0,
    lineSpacing: fontSize * 1.35,
  });
}

/** Dòng chú thích nguồn ở đáy slide. */
function source(s, text) {
  s.addText(text, {
    x: M, y: HT - 0.55, w: W - 2 * M, h: 0.3, fontSize: 9.5,
    color: GREY, italic: true, fontFace: B_FONT, margin: 0,
  });
}

/** Số slide góc phải dưới. */
function num(s, n) {
  s.addText(String(n), {
    x: W - 0.9, y: HT - 0.55, w: 0.4, h: 0.3, fontSize: 11,
    color: GREY, align: "right", fontFace: B_FONT, margin: 0,
  });
}

// ===========================================================================
// SLIDE 1 — Trang bìa
// ===========================================================================
{
  const s = darkSlide();
  s.addText("CHUYÊN ĐỀ 10", {
    x: M, y: 1.5, w: 10, h: 0.4, fontSize: 14, bold: true,
    color: MINT, fontFace: B_FONT, charSpacing: 3, margin: 0,
  });
  s.addText("Xử lý chuỗi với thuật toán KMP\nvà cấu trúc dữ liệu Trie", {
    x: M, y: 2.0, w: 11.5, h: 1.8, fontSize: 40, bold: true,
    color: PAPER, fontFace: H_FONT, lineSpacing: 46, margin: 0,
  });
  s.addText("Interactive Text Search & Autocomplete System", {
    x: M, y: 3.95, w: 11, h: 0.5, fontSize: 19, italic: true,
    color: MINT, fontFace: B_FONT, margin: 0,
  });
  s.addShape(pres.ShapeType.rect, {
    x: M, y: 4.75, w: 2.2, h: 0.035, fill: { color: TEAL }, line: { color: TEAL },
  });
  s.addText("Nhóm chuyên đề 10  ·  Trình bày: Huỳnh Phát Lợi · Võ Phú Vinh · Thanh Tú", {
    x: M, y: 5.1, w: 8, h: 0.35, fontSize: 16, color: PAPER,
    fontFace: B_FONT, margin: 0,
  });
  s.addText("Môn: Các thuật toán tối ưu   ·   Tháng 8 năm 2026", {
    x: M, y: 5.5, w: 9, h: 0.35, fontSize: 13, color: "9FB3C8",
    fontFace: B_FONT, margin: 0,
  });
  addSpeakerNotes(s, 1);
}

// ===========================================================================
// SLIDE 2 — Thành viên và đóng góp
// ===========================================================================
{
  const s = contentSlide("Thành viên và phần đóng góp", "Nhóm thực hiện");
  TEAM.forEach((member, i) => {
    const y = 1.62 + i * 1.48;
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y, w: W - 2 * M, h: 1.18, rectRadius: 0.08,
      fill: { color: i === 0 ? "E7F4F4" : TINT },
      line: { color: i === 0 ? MINT : "D7E0EA", pt: 0.8 },
    });
    s.addText(member.name, {
      x: M + 0.3, y: y + 0.18, w: 3.2, h: 0.36,
      fontSize: 17, bold: true, color: i === 0 ? BLUE : INK,
      fontFace: H_FONT, margin: 0,
    });
    s.addText(member.role, {
      x: M + 3.55, y: y + 0.17, w: 3.4, h: 0.35,
      fontSize: 13, bold: true, color: TEAL, fontFace: B_FONT, margin: 0,
    });
    s.addText(member.work, {
      x: M + 3.55, y: y + 0.56, w: 8.15, h: 0.42,
      fontSize: 12.2, color: GREY, fontFace: B_FONT, margin: 0,
    });
  });
  s.addText("Phân công là trách nhiệm chính; cả ba thành viên cùng review phần lõi và có thể giải thích KMP, Trie, baseline và kết quả thực nghiệm.", {
    x: M, y: 6.2, w: W - 2 * M, h: 0.45, fontSize: 12.5,
    italic: true, color: BLUE, fontFace: B_FONT, margin: 0,
  });
  num(s, 2);
  addSpeakerNotes(s, 2);
}

// ===========================================================================
// SLIDE 3 — Đặt vấn đề
// ===========================================================================
{
  const s = contentSlide("Hai bài toán nghe giống nhau, cấu trúc khác hẳn nhau", "Đặt vấn đề");
  tbl(s, [
    headerRow(["", "Tìm mẫu trong văn bản", "Gợi ý theo tiền tố"]),
    row(["Cái gì biết trước?", "không gì cả", "toàn bộ từ điển"], { bold: true }),
    row(["Tiền xử lý phía nào?", "MẪU", "DỮ LIỆU"], { bold: true }),
    row(["Thuật toán", "KMP", "Trie"], { bold: true }),
    row(["Phụ thuộc |Σ|?", "KHÔNG", "CÓ"], { bold: true }),
  ], { y: 1.85, colW: [3.5, 4.3, 4.3], rowH: 0.5, fontSize: 15 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.75, w: W - 2 * M, h: 1.15, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("Cái gì được biết trước quyết định nên tiền xử lý phía nào.", {
    x: M + 0.35, y: 4.92, w: W - 2 * M - 0.7, h: 0.4, fontSize: 19, bold: true,
    color: BLUE, fontFace: H_FONT, margin: 0,
  });
  s.addText("Đó là lý do đề bài yêu cầu hai module độc lập — trong mã nguồn, src/kmp và src/trie không import lẫn nhau.", {
    x: M + 0.35, y: 5.35, w: W - 2 * M - 0.7, h: 0.4, fontSize: 13.5,
    color: INK, fontFace: B_FONT, margin: 0,
  });
  num(s, 3);
  addSpeakerNotes(s, 3);
}

// ===========================================================================
// SLIDE 4 — Phát biểu hai module
// ===========================================================================
{
  const s = contentSlide("Phát biểu bài toán", "Module A và Module B");

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.75, w: 5.95, h: 4.0, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("MODULE A — KMP", {
    x: M + 0.3, y: 1.95, w: 5.4, h: 0.35, fontSize: 15, bold: true,
    color: BLUE, fontFace: B_FONT, charSpacing: 1.2, margin: 0,
  });
  s.addText([
    { text: "Vào: ", options: { bold: true, breakLine: false } },
    { text: "văn bản T (|T| = n), mẫu P (|P| = m ≥ 1)", options: { breakLine: true } },
    { text: "Ra: ", options: { bold: true, breakLine: false } },
    { text: "MỌI vị trí xuất hiện, kể cả overlapping", options: { breakLine: true } },
    { text: "Thời gian: ", options: { bold: true, breakLine: false } },
    { text: "O(n + m), số so sánh ≤ 2n", options: { breakLine: true } },
    { text: "Bộ nhớ phụ: ", options: { bold: true, breakLine: false } },
    { text: "O(m) cho mảng LPS", options: {} },
  ], {
    x: M + 0.3, y: 2.4, w: 5.4, h: 1.5, fontSize: 13.5, color: INK,
    fontFace: B_FONT, margin: 0, lineSpacing: 22,
  });
  tbl(s, [
    headerRow(["T", "P", "Kết quả"]),
    row(["aaaa", "aa", "[0, 1, 2]"]),
    row(["mississippi", "issi", "[1, 4]"]),
    row(["abc", "abcd", "[ ]   (m > n)"]),
  ], { x: M + 0.3, y: 4.05, w: 5.4, colW: [1.7, 1.5, 2.2], rowH: 0.34, fontSize: 12 });

  s.addShape(pres.ShapeType.roundRect, {
    x: 6.9, y: 1.75, w: 5.8, h: 4.0, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("MODULE B — TRIE", {
    x: 7.2, y: 1.95, w: 5.2, h: 0.35, fontSize: 15, bold: true,
    color: TEAL, fontFace: B_FONT, charSpacing: 1.2, margin: 0,
  });
  s.addText([
    { text: "Bốn thao tác bắt buộc:", options: { bold: true, breakLine: true } },
    { text: "insert · exact search · prefix query", options: { breakLine: true } },
    { text: "autocomplete(q, k) có giới hạn kết quả", options: { breakLine: true } },
    { text: "Σ′ khai báo rõ: ", options: { bold: true, breakLine: false } },
    { text: "38 ký tự (mặc định), 105 (tiếng Việt)", options: {} },
  ], {
    x: 7.2, y: 2.4, w: 5.2, h: 1.5, fontSize: 13.5, color: INK,
    fontFace: B_FONT, margin: 0, lineSpacing: 22,
  });
  tbl(s, [
    headerRow(["Truy vấn", "Kết quả"]),
    row(["search(\"ti\")", "False  ← chỉ là tiền tố"]),
    row(["starts_with(\"ti\")", "True   ← ngược lại"]),
    row(["autocomplete(\"t\", 2)", "[tin, tinh], truncated"]),
  ], { x: 7.2, y: 4.05, w: 5.2, colW: [2.3, 2.9], rowH: 0.34, fontSize: 12 });
  num(s, 4);
  addSpeakerNotes(s, 4);
}

// ===========================================================================
// SLIDE 5 — prefix function
// ===========================================================================
{
  const s = contentSlide("Prefix function π — trái tim của KMP", "Lý thuyết");
  s.addText("π[i] = độ dài border dài nhất của P[0..i]", {
    x: M, y: 1.62, w: 8, h: 0.4, fontSize: 17, bold: true, color: BLUE,
    fontFace: B_FONT, margin: 0,
  });
  s.addText("border = chuỗi vừa là tiền tố thật sự, vừa là hậu tố thật sự", {
    x: M, y: 2.0, w: 8, h: 0.35, fontSize: 13, italic: true, color: GREY,
    fontFace: B_FONT, margin: 0,
  });
  tbl(s, [
    row(["i", "0", "1", "2", "3", "4", "5", "6"], { bold: true, fill: "DCE6F1" }),
    row(["P[i]", "a", "b", "a", "b", "a", "c", "a"]),
    row(["π[i]", "0", "0", "1", "2", "3", "0", "1"], { color: BLUE }),
  ], { y: 2.55, colW: [1.1, 1.44, 1.44, 1.44, 1.44, 1.44, 1.44, 1.36], rowH: 0.42, fontSize: 15 });

  s.addText("π[4] = 3  vì  \"ababa\"  có border dài nhất là  \"aba\"", {
    x: M, y: 3.98, w: 7, h: 0.35, fontSize: 14, color: INK, fontFace: B_FONT, margin: 0,
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.5, w: W - 2 * M, h: 1.5, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("Bổ đề (chuỗi border)", {
    x: M + 0.35, y: 4.65, w: 6, h: 0.32, fontSize: 14, bold: true,
    color: BLUE, fontFace: B_FONT, margin: 0,
  });
  s.addText("Tập MỌI border của S  =  π[k−1] → π[π[k−1]−1] → … → 0", {
    x: M + 0.35, y: 5.02, w: 11, h: 0.36, fontSize: 16, bold: true,
    color: INK, fontFace: "Courier New", margin: 0,
  });
  s.addText("Khi một border độ dài L không dùng được, border tiếp theo dài đúng π[L−1] — ta nhảy thẳng, không thử tuần tự.", {
    x: M + 0.35, y: 5.44, w: 11.5, h: 0.4, fontSize: 13, color: GREY,
    fontFace: B_FONT, margin: 0,
  });
  num(s, 5);
  addSpeakerNotes(s, 5);
}

// ===========================================================================
// SLIDE 6 — Bất biến, vì sao không lùi
// ===========================================================================
{
  const s = contentSlide("Vì sao con trỏ văn bản không bao giờ lùi", "Lý thuyết");
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.62, w: W - 2 * M, h: 0.95, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("Bất biến (BB-A): trước khi xử lý T[j], i là độ dài lớn nhất < m sao cho P[0..i−1] là hậu tố của T[0..j−1]", {
    x: M + 0.3, y: 1.78, w: W - 2 * M - 0.6, h: 0.65, fontSize: 15, bold: true,
    color: INK, fontFace: B_FONT, margin: 0,
  });
  s.addText("Trạng thái là MỘT SỐ NGUYÊN duy nhất — không phải một tập vị trí. Đó chính là lý do j không cần lùi.", {
    x: M, y: 2.72, w: W - 2 * M, h: 0.4, fontSize: 14, color: TEAL,
    italic: true, fontFace: B_FONT, margin: 0,
  });
  code(s, M, 3.22, W - 2 * M, 2.55, [
    "for j <- 0 to n-1:",
    "    while T[j] != P[i] and i > 0:",
    "        i <- pi[i-1]        # dịch MẪU, j KHÔNG lùi",
    "    if T[j] = P[i]: i <- i+1",
    "    if i = m:",
    "        báo khớp tại j-m+1",
    "        i <- pi[m-1]        # KHÔNG phải i <- 0 !",
  ], 14);
  num(s, 6);
  addSpeakerNotes(s, 6);
}

// ===========================================================================
// SLIDE 7 — dòng i <- pi[m-1]
// ===========================================================================
{
  const s = contentSlide("Dòng quan trọng nhất:  i ← π[m−1]", "Lý thuyết");
  s.addText("T = \"aaaa\",   P = \"aa\",   π = [0, 1]", {
    x: M, y: 1.65, w: 7, h: 0.4, fontSize: 17, bold: true, color: BLUE,
    fontFace: "Courier New", margin: 0,
  });
  tbl(s, [
    headerRow(["j", "i sau khi xử lý", "Hành động"]),
    row(["1", "2 = m", "báo vị trí 0, đặt i ← π[1] = 1"]),
    row(["2", "2 = m", "báo vị trí 1, đặt i ← 1"]),
    row(["3", "2 = m", "báo vị trí 2"]),
  ], { y: 2.2, colW: [1.2, 3.0, 7.9], rowH: 0.42, fontSize: 14 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.05, w: 5.9, h: 2.0, rectRadius: 0.08,
    fill: { color: "E6F4EA" }, line: { color: "E6F4EA" },
  });
  s.addText("i ← π[m−1]", {
    x: M + 0.3, y: 4.3, w: 5.3, h: 0.45, fontSize: 20, bold: true,
    color: "1E7B3C", fontFace: "Courier New", margin: 0,
  });
  s.addText("Kết quả  [0, 1, 2]   ✓  đủ nghiệm", {
    x: M + 0.3, y: 4.88, w: 5.3, h: 0.45, fontSize: 17, bold: true,
    color: "1E7B3C", fontFace: B_FONT, margin: 0,
  });
  s.addText("Giữ lại hậu tố dài nhất còn là tiền tố của mẫu", {
    x: M + 0.3, y: 5.42, w: 5.3, h: 0.4, fontSize: 12, color: "2F6B47",
    fontFace: B_FONT, margin: 0,
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 6.8, y: 4.05, w: 5.9, h: 2.0, rectRadius: 0.08,
    fill: { color: "FCE9E6" }, line: { color: "FCE9E6" },
  });
  s.addText("i ← 0", {
    x: 7.1, y: 4.3, w: 5.3, h: 0.45, fontSize: 20, bold: true,
    color: "B3261E", fontFace: "Courier New", margin: 0,
  });
  s.addText("Kết quả  [0, 2]   ✗  MẤT một nghiệm", {
    x: 7.1, y: 4.88, w: 5.3, h: 0.45, fontSize: 17, bold: true,
    color: "B3261E", fontFace: B_FONT, margin: 0,
  });
  s.addText("Vứt bỏ toàn bộ thông tin đã đọc, phải bắt đầu lại", {
    x: 7.1, y: 5.42, w: 5.3, h: 0.4, fontSize: 12, color: "8C3B33",
    fontFace: B_FONT, margin: 0,
  });
  source(s, "Lỗi kinh điển. Test đối kháng test_periodic_pattern_with_long_border được viết riêng để bắt lỗi này.");
  num(s, 7);
  addSpeakerNotes(s, 7);
}

// ===========================================================================
// SLIDE 8 — Chứng minh độ phức tạp
// ===========================================================================
{
  const s = contentSlide("Chặn O(n+m): lập luận khấu hao", "Chứng minh");
  s.addText("Định lý.  Số phép so sánh ≤ 2n ở vòng chính,  ≤ 2m khi xây π.", {
    x: M, y: 1.62, w: 11.5, h: 0.4, fontSize: 17, bold: true, color: BLUE,
    fontFace: B_FONT, margin: 0,
  });
  s.addText("Chứng minh bằng hàm thế Φ = 2j − i:", {
    x: M, y: 2.05, w: 8, h: 0.35, fontSize: 14, italic: true, color: GREY,
    fontFace: B_FONT, margin: 0,
  });

  const items = [
    ["So sánh THÀNH CÔNG", "i tăng 1, rồi j tăng  →  không quá n lần", "1E7B3C"],
    ["So sánh THẤT BẠI (i > 0)", "i GIẢM NGẶT vì π[i−1] < i  (border là thật sự)", GOLD],
    ["Cân bằng tăng/giảm", "i chỉ tăng 1 mỗi lần khớp ⇒ tổng tăng ≤ n ⇒ tổng giảm ≤ n", BLUE],
  ];
  items.forEach(([t, d, c], i) => {
    const y = 2.55 + i * 1.15;
    s.addShape(pres.ShapeType.ellipse, {
      x: M, y: y + 0.08, w: 0.5, h: 0.5, fill: { color: c }, line: { color: c },
    });
    s.addText(String(i + 1), {
      x: M, y: y + 0.08, w: 0.5, h: 0.5, fontSize: 16, bold: true,
      color: PAPER, align: "center", fontFace: B_FONT, margin: 0,
    });
    s.addText(t, {
      x: M + 0.72, y: y, w: 4.6, h: 0.36, fontSize: 15.5, bold: true,
      color: INK, fontFace: B_FONT, margin: 0,
    });
    s.addText(d, {
      x: M + 0.72, y: y + 0.4, w: 8.3, h: 0.5, fontSize: 13.5,
      color: GREY, fontFace: B_FONT, margin: 0,
    });
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 9.6, y: 2.55, w: 3.1, h: 3.15, rectRadius: 0.08,
    fill: { color: DEEP }, line: { color: DEEP },
  });
  s.addText("≤ 2n", {
    x: 9.6, y: 3.25, w: 3.1, h: 0.8, fontSize: 46, bold: true,
    color: MINT, align: "center", fontFace: H_FONT, margin: 0,
  });
  s.addText("|Σ| KHÔNG xuất hiện", {
    x: 9.7, y: 4.25, w: 2.9, h: 0.35, fontSize: 13, color: "9FB3C8",
    align: "center", fontFace: B_FONT, margin: 0,
  });
  s.addText("Bộ nhớ phụ O(m)", {
    x: 9.7, y: 4.65, w: 2.9, h: 0.35, fontSize: 13, color: "9FB3C8",
    align: "center", fontFace: B_FONT, margin: 0,
  });
  source(s, "So với naive O(n·m) — cận của naive cũng chặt trên chính T = aⁿ, P = aᵐ⁻¹b.");
  num(s, 8);
  addSpeakerNotes(s, 8);
}

// ===========================================================================
// SLIDE 9 — Trie: bất biến
// ===========================================================================
{
  const s = contentSlide("Bốn bất biến của Trie", "Lý thuyết · Module B");

  const inv = [
    ["I1", "Mỗi nút ⟷ ĐÚNG MỘT tiền tố", BLUE],
    ["I2", "is_end ⟺ tiền tố đó là một từ trong D", TEAL],
    ["I3", "word_count = số lần từ đó đã insert", TEAL],
    ["I4", "prefix_count = tổng word_count của CẢ CÂY CON", GOLD],
  ];
  inv.forEach(([k, t, c], i) => {
    const y = 1.75 + i * 0.72;
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y, w: 0.75, h: 0.55, rectRadius: 0.08,
      fill: { color: c }, line: { color: c },
    });
    s.addText(k, {
      x: M, y, w: 0.75, h: 0.55, fontSize: 16, bold: true, color: PAPER,
      align: "center", fontFace: B_FONT, margin: 0,
    });
    s.addText(t, {
      x: M + 0.95, y: y + 0.05, w: 11, h: 0.45, fontSize: 15,
      color: INK, fontFace: B_FONT, margin: 0,
    });
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.75, w: 5.9, h: 1.35, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("I1  ⇒  chia sẻ tiền tố", {
    x: M + 0.3, y: 4.9, w: 5.3, h: 0.35, fontSize: 14, bold: true,
    color: BLUE, fontFace: B_FONT, margin: 0,
  });
  s.addText("Bộ nhớ tỉ lệ số tiền tố PHÂN BIỆT, không phải tổng độ dài các từ. Đo được 0,31–0,82 nút mỗi ký tự.", {
    x: M + 0.3, y: 5.25, w: 5.3, h: 0.7, fontSize: 12.5, color: GREY,
    fontFace: B_FONT, margin: 0,
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 6.8, y: 4.75, w: 5.9, h: 1.35, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("I4  ⇒  đếm trong O(|q|)", {
    x: 7.1, y: 4.9, w: 5.3, h: 0.35, fontSize: 14, bold: true,
    color: GOLD, fontFace: B_FONT, margin: 0,
  });
  s.addText("“Có bao nhiêu từ mang tiền tố q?” không cần duyệt cây con. Demo hiển thị “8 / 2 513 kết quả” nhờ đúng bất biến này.", {
    x: 7.1, y: 5.25, w: 5.3, h: 0.7, fontSize: 12.5, color: GREY,
    fontFace: B_FONT, margin: 0,
  });
  num(s, 9);
  addSpeakerNotes(s, 9);
}

// ===========================================================================
// SLIDE 10 — autocomplete early stop
// ===========================================================================
{
  const s = contentSlide("autocomplete: DFS dừng sớm", "Lý thuyết · Module B");
  code(s, M, 1.7, 7.3, 2.7, [
    "path <- list(q); stack <- [FRAME(node_q)]",
    "while stack khác rỗng:",
    "    u <- frame hiện tại",
    "    if u.is_end:",
    "        if |out| = k:",
    "            truncated <- true; BREAK   # dừng sớm",
    "        out.append(join(path))",
    "    lấy cạnh tiếp theo theo thứ tự TĂNG; push FRAME(con)",
  ], 12);

  const pts = [
    ["Thứ tự XÁC ĐỊNH", "thứ tự từ điển ⇒ đối chiếu được với baseline"],
    ["Stack tường minh", "không đệ quy ⇒ chạy được với từ 50 000 ký tự"],
    ["Cờ truncated chính xác", "false ⇒ đã trả HẾT kết quả"],
  ];
  pts.forEach(([t, d], i) => {
    const y = 1.75 + i * 0.92;
    s.addShape(pres.ShapeType.ellipse, {
      x: 8.2, y: y + 0.04, w: 0.3, h: 0.3, fill: { color: MINT }, line: { color: MINT },
    });
    s.addText(t, {
      x: 8.65, y: y - 0.02, w: 4.1, h: 0.34, fontSize: 13.5, bold: true,
      color: INK, fontFace: B_FONT, margin: 0,
    });
    s.addText(d, {
      x: 8.65, y: y + 0.3, w: 4.2, h: 0.55, fontSize: 12, color: GREY,
      fontFace: B_FONT, margin: 0,
    });
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.62, w: W - 2 * M, h: 1.35, rectRadius: 0.08,
    fill: { color: DEEP }, line: { color: DEEP },
  });
  s.addText("Đo thực tế: cây con có 2 513 từ,  k = 1  ⇒  duyệt 6 nút  (0,08 % cây con)", {
    x: M + 0.35, y: 4.8, w: 11.5, h: 0.45, fontSize: 17, bold: true,
    color: MINT, fontFace: B_FONT, margin: 0,
  });
  s.addText("Số nút duyệt ≈ 3k — tỉ lệ với k, KHÔNG tỉ lệ với kích thước cây con. Đúng thứ ô tìm kiếm cần: người dùng chỉ xem 8–10 gợi ý.", {
    x: M + 0.35, y: 5.25, w: 11.5, h: 0.5, fontSize: 12.5, color: "C7D6E8",
    fontFace: B_FONT, margin: 0,
  });
  num(s, 10);
  addSpeakerNotes(s, 10);
}

// ===========================================================================
// SLIDE 11 — Bước chuyển sang DEMO
// ===========================================================================
{
  const s = darkSlide();
  s.addText("DEMO", {
    x: M, y: 2.6, w: 8, h: 1.0, fontSize: 54, bold: true, color: PAPER,
    fontFace: H_FONT, margin: 0,
  });
  s.addText("Hai module cùng chạy trên một luồng người dùng thật", {
    x: M, y: 3.7, w: 10, h: 0.5, fontSize: 20, color: MINT,
    fontFace: B_FONT, margin: 0,
  });
  const flow = [
    ["1", "Gõ tiền tố", "Trie gợi ý, hiện số nút đã duyệt"],
    ["2", "Chọn gợi ý", "KMP tìm, tô sáng, hiện bảng π"],
    ["3", "Nhiều mẫu", "Aho–Corasick, so với KMP lặp"],
  ];
  flow.forEach(([n, t, d], i) => {
    const x = M + i * 4.1;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 4.6, w: 3.8, h: 1.35, rectRadius: 0.08,
      fill: { color: "2E3A6E" }, line: { color: "2E3A6E" },
    });
    s.addText(n, {
      x: x + 0.25, y: 4.75, w: 0.5, h: 0.4, fontSize: 20, bold: true,
      color: MINT, fontFace: H_FONT, margin: 0,
    });
    s.addText(t, {
      x: x + 0.8, y: 4.78, w: 2.8, h: 0.35, fontSize: 15, bold: true,
      color: PAPER, fontFace: B_FONT, margin: 0,
    });
    s.addText(d, {
      x: x + 0.25, y: 5.2, w: 3.3, h: 0.6, fontSize: 12, color: "9FB3C8",
      fontFace: B_FONT, margin: 0,
    });
  });
  addSpeakerNotes(s, 11);
}

// ===========================================================================
// SLIDE 12 — Kiểm thử
// ===========================================================================
{
  const s = contentSlide("276 test · 3 baseline độc lập", "Kiểm thử");
  stat(s, M, 1.7, 2.85, "276", "test tự động + 10 doctest", BLUE);
  stat(s, M + 3.05, 1.7, 2.85, "18", "test ĐỐI KHÁNG", GOLD);
  stat(s, M + 6.1, 1.7, 2.85, "22", "test ngẫu nhiên đối chiếu", TEAL);
  stat(s, M + 9.15, 1.7, 2.85, "6", "property test", "1E7B3C");

  s.addText("Ba baseline, KHÔNG dùng lại một dòng nào của src/", {
    x: M, y: 3.45, w: 11, h: 0.4, fontSize: 16, bold: true, color: INK,
    fontFace: B_FONT, margin: 0,
  });
  tbl(s, [
    headerRow(["Baseline", "Đối chiếu cho", "Vì sao độc lập"]),
    row(["naive_search  O(n·m)", "KMP", "thuật toán khác hẳn, ngây thơ tới mức đọc là tin"]),
    row(["str.find của CPython", "KMP", "viết bằng C, dùng thuật toán two-way"]),
    row(["naive_build_lps  O(m³)", "build_lps", "dịch TRỰC TIẾP từ định nghĩa border"]),
    row(["linear_autocomplete_sorted", "Trie", "quét list đã sắp; không set/sort trong vùng đo"]),
  ], { y: 3.9, colW: [3.5, 2.2, 6.4], rowH: 0.38, fontSize: 12.5 });
  source(s, "Nếu baseline dùng chung mã với cài đặt, một lỗi logic sẽ xuất hiện ở cả hai phía và test pass sai.");
  num(s, 12);
  addSpeakerNotes(s, 12);
}

// ===========================================================================
// SLIDE 13 — Test đối kháng
// ===========================================================================
{
  const s = contentSlide("Test đối kháng: mỗi ca có mục tiêu tấn công", "Kiểm thử");
  tbl(s, [
    headerRow(["Trường hợp", "Tấn công vào", "Kết quả"]),
    row(["T = aⁿ,  P = aᵐ⁻¹b", "ca xấu nhất của naive", "KMP ≤ 2n, naive ~ n·m"]),
    row(["chuỗi FIBONACCI", "vòng while lùi π (dãy border dài nhất)", "vẫn ≤ 2n"]),
    row(["P = \"abab\" tuần hoàn", "bảo vệ tính chất overlapping", "999 nghiệm, đủ"]),
    row(["cây chổi: 2 000 từ, tiền tố 100 ký tự", "cơ chế early stop của Trie", "duyệt < 300 nút"]),
    row(["từ dài 50 000 ký tự", "giới hạn đệ quy của Python", "pass (stack tường minh)"]),
    row(["ký tự lạ ở CUỐI từ dài", "cây bị bẩn khi insert thất bại", "num_nodes không đổi"]),
  ], { y: 1.85, colW: [4.3, 4.4, 3.4], rowH: 0.44, fontSize: 12.5 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.15, w: W - 2 * M, h: 0.85, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("Chuỗi Fibonacci có dãy border dài nhất trong các chuỗi cùng độ dài — nếu lập luận khấu hao sai ở đâu đó, chính ca này sẽ làm vượt chặn 2n.", {
    x: M + 0.3, y: 5.32, w: 12, h: 0.55, fontSize: 13, color: INK,
    fontFace: B_FONT, margin: 0,
  });
  num(s, 13);
  addSpeakerNotes(s, 13);
}

// ===========================================================================
// SLIDE 14 — E1
// ===========================================================================
{
  const s = contentSlide("Chặn 2n chặt tới bốn chữ số thập phân", "Thực nghiệm · E1");
  tbl(s, [
    headerRow(["Văn bản", "n", "KMP cmp/n", "naive cmp/n", "Tăng tốc"]),
    row(["natural", "10⁶", "1,143", "—", "—"]),
    row(["random_s26", "10⁶", "1,039", "—", "—"]),
    row(["repetitive", "10⁵", "1,000", "32,5", "32,5×"]),
    row(["uniform", "10⁵", "1,9994", "64,0", "32,0×"]),
    row(["uniform", "10⁶", "1,9999", "—", "—"], { fill: "E6F4EA" }),
  ], { y: 1.8, colW: [2.8, 1.6, 2.5, 2.5, 2.7], rowH: 0.4, fontSize: 13 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.35, w: 6.0, h: 1.15, rectRadius: 0.08,
    fill: { color: DEEP }, line: { color: DEEP },
  });
  s.addText("1,9999 · n", {
    x: M + 0.3, y: 4.5, w: 5.4, h: 0.55, fontSize: 30, bold: true,
    color: MINT, fontFace: H_FONT, margin: 0,
  });
  s.addText("sát cận 2n, chưa bao giờ vượt", {
    x: M + 0.3, y: 5.05, w: 5.4, h: 0.35, fontSize: 12.5, color: "9FB3C8",
    fontFace: B_FONT, margin: 0,
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 6.9, y: 4.35, w: 5.8, h: 1.15, rectRadius: 0.08,
    fill: { color: "FFF4E0" }, line: { color: "FFF4E0" },
  });
  s.addText("Trung thực:", {
    x: 7.2, y: 4.48, w: 5.2, h: 0.3, fontSize: 13, bold: true,
    color: "8A5A00", fontFace: B_FONT, margin: 0,
  });
  s.addText("Trên dữ liệu natural-like tổng hợp theo Zipf, KMP ≈ naive (1,0–1,1×). Với |Σ| lớn, naive ĐÃ gần tuyến tính. Lợi thế KMP chỉ hiện khi dữ liệu lặp.", {
    x: 7.2, y: 4.78, w: 5.2, h: 0.65, fontSize: 11.5, color: "8A5A00",
    fontFace: B_FONT, margin: 0,
  });
  source(s, "Nguồn: e1_scaling_n.csv · trung vị 7 lần · m = 64 · CPython 3.11.9, macOS arm64");
  num(s, 14);
  addSpeakerNotes(s, 14);
}

// ===========================================================================
// SLIDE 15 — Biểu đồ E1
// ===========================================================================
{
  const s = contentSlide("Số phép so sánh chuẩn hóa theo n", "Thực nghiệm · E1");
  if (fs.existsSync(FIG("fig2_comparisons_per_n.png"))) {
    s.addImage({ path: FIG("fig2_comparisons_per_n.png"), x: 2.3, y: 1.5, w: 8.7, h: 5.0 });
  }
  num(s, 15);
  addSpeakerNotes(s, 15);
}

// ===========================================================================
// SLIDE 16 — E2 + E3
// ===========================================================================
{
  const s = contentSlide("m không ảnh hưởng KMP · N không ảnh hưởng Trie", "Thực nghiệm · E2 và E3");
  s.addText("E2 — m biến thiên 1 024 lần (n = 30 000)", {
    x: M, y: 1.62, w: 6, h: 0.35, fontSize: 14, bold: true, color: BLUE,
    fontFace: B_FONT, margin: 0,
  });
  tbl(s, [
    headerRow(["m", "KMP cmp/n", "naive cmp/n", "LPS cmp/m"]),
    row(["4", "1,9999", "4,0", "1,25"]),
    row(["64", "1,9979", "63,9", "1,95"]),
    row(["1 024", "1,9659", "—", "1,997"], { fill: "E6F4EA" }),
  ], { x: M, y: 2.0, w: 5.9, colW: [1.2, 1.7, 1.7, 1.3], rowH: 0.38, fontSize: 12.5 });

  s.addText("E3 — N biến thiên 500 lần", {
    x: 6.9, y: 1.62, w: 6, h: 0.35, fontSize: 14, bold: true, color: TEAL,
    fontFace: B_FONT, margin: 0,
  });
  tbl(s, [
    headerRow(["N", "Trie", "Tuyến tính", "Tăng tốc", "search"]),
    row(["1 000", "14,4 µs", "19,3 µs", "1,3×", "6 nút"]),
    row(["100 000", "7,1 µs", "1 832 µs", "258,6×", "10 nút"]),
    row(["500 000", "8,6 µs", "9 161 µs", "1 062×", "10 nút"], { fill: "E6F4EA" }),
  ], { x: 6.9, y: 2.0, w: 5.8, colW: [1.3, 1.1, 1.3, 1.1, 1.0], rowH: 0.38, fontSize: 11.5 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 3.72, w: 5.9, h: 1.5, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("Chặn 2m của BUILD_LPS cũng chặt: 1,997", {
    x: M + 0.3, y: 3.92, w: 5.3, h: 0.4, fontSize: 15, bold: true,
    color: BLUE, fontFace: B_FONT, margin: 0,
  });
  s.addText("Cột KMP giữ nguyên khi m biến thiên 1 024 lần ⇒ chặn là 2n, không phải hàm của m.", {
    x: M + 0.3, y: 4.35, w: 5.3, h: 0.75, fontSize: 12, color: GREY,
    fontFace: B_FONT, margin: 0,
  });
  s.addShape(pres.ShapeType.roundRect, {
    x: 6.9, y: 3.72, w: 5.8, h: 1.5, rectRadius: 0.08,
    fill: { color: TINT }, line: { color: TINT },
  });
  s.addText("search duyệt 6–10 nút = ĐỘ DÀI TỪ, độc lập N", {
    x: 7.2, y: 3.92, w: 5.2, h: 0.4, fontSize: 15, bold: true,
    color: TEAL, fontFace: B_FONT, margin: 0,
  });
  s.addText("Trie gần như phẳng; baseline quét tăng theo N và không gồm chi phí set/sort.", {
    x: 7.2, y: 4.35, w: 5.2, h: 0.75, fontSize: 12, color: GREY,
    fontFace: B_FONT, margin: 0,
  });
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.42, w: W - 2 * M, h: 0.78, rectRadius: 0.08,
    fill: { color: DEEP }, line: { color: DEEP },
  });
  s.addText("Số đếm nút là bằng chứng sạch hơn cả thời gian — chính xác tuyệt đối, không bị nhiễu bởi ngôn ngữ hay phần cứng.", {
    x: M + 0.35, y: 5.6, w: 11.8, h: 0.45, fontSize: 14, bold: true,
    color: MINT, fontFace: B_FONT, margin: 0,
  });
  source(s, "Nguồn: e2_scaling_m.csv và e3_trie_vs_linear.csv");
  num(s, 16);
  addSpeakerNotes(s, 16);
}

// ===========================================================================
// SLIDE 17 — Aho-Corasick
// ===========================================================================
{
  const s = contentSlide("Mở rộng: Aho–Corasick nối hai module", "Mở rộng");
  tbl(s, [
    headerRow(["KMP (module A)", "Aho–Corasick"]),
    row(["π trên MỘT mẫu, lưu bằng mảng", "failure link trên TRIE nhiều mẫu"]),
    row(["π[i] = border dài nhất của P[0..i]", "fail(u) = hậu tố dài nhất còn là tiền tố của một mẫu"]),
    row(["lùi theo dãy border", "lùi theo dãy failure link"]),
    row(["O(n + m)", "O(n + Σ|Pᵢ| + số khớp)"]),
  ], { y: 1.8, colW: [5.5, 6.6], rowH: 0.44, fontSize: 12.5 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 3.9, w: W - 2 * M, h: 0.75, rectRadius: 0.08,
    fill: { color: DEEP }, line: { color: DEEP },
  });
  s.addText("Aho–Corasick  =  cấu trúc của module B  +  ý tưởng của module A", {
    x: M + 0.3, y: 4.05, w: 11.8, h: 0.45, fontSize: 18, bold: true,
    color: MINT, align: "center", fontFace: H_FONT, margin: 0,
  });

  tbl(s, [
    headerRow(["Số mẫu", "AC (so sánh)", "KMP lặp (so sánh)", "Tỉ số"]),
    row(["1", "109 539", "108 737", "0,99× (chậm hơn!)"], { fill: "FFF4E0" }),
    row(["10", "144 341", "1 057 779", "7,3×"]),
    row(["100", "148 241", "10 440 185", "70,4×"], { fill: "E6F4EA" }),
  ], { y: 4.8, colW: [1.8, 3.0, 3.6, 3.7], rowH: 0.36, fontSize: 12 });
  num(s, 17);
  addSpeakerNotes(s, 17);
}

// ===========================================================================
// SLIDE 18 — Giới hạn + kết luận
// ===========================================================================
{
  const s = darkSlide();
  s.addText("Giới hạn — nói thẳng", {
    x: M, y: 0.6, w: 8, h: 0.6, fontSize: 30, bold: true, color: PAPER,
    fontFace: H_FONT, margin: 0,
  });
  const lim = [
    ["Nhiều truy vấn / cùng văn bản", "KMP xử lý MẪU ⇒ mỗi truy vấn vẫn O(n)", "suffix automaton"],
    ["Tìm mờ, lỗi chính tả", "Trie chỉ khớp tiền tố CHÍNH XÁC", "Trie + Levenshtein"],
    ["Xếp hạng theo tần suất", "phải xem hết cây con ⇒ MẤT early stop", "lưu sẵn top-k mỗi nút"],
  ];
  lim.forEach(([a, b, c], i) => {
    const y = 1.45 + i * 0.78;
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y, w: W - 2 * M, h: 0.62, rectRadius: 0.06,
      fill: { color: "2E3A6E" }, line: { color: "2E3A6E" },
    });
    s.addText(a, { x: M + 0.25, y: y + 0.14, w: 3.6, h: 0.35, fontSize: 13, bold: true, color: PAPER, fontFace: B_FONT, margin: 0 });
    s.addText(b, { x: M + 3.95, y: y + 0.14, w: 5.2, h: 0.35, fontSize: 12, color: "C7D6E8", fontFace: B_FONT, margin: 0 });
    s.addText("→ " + c, { x: M + 9.25, y: y + 0.14, w: 2.8, h: 0.35, fontSize: 12, color: MINT, fontFace: B_FONT, margin: 0 });
  });

  s.addText("KHÔNG khẳng định KMP nhanh hơn str.find — hàm đó viết bằng C, nhanh hơn hàng chục lần.", {
    x: M, y: 3.95, w: 12, h: 0.4, fontSize: 13, italic: true, color: GOLD,
    fontFace: B_FONT, margin: 0,
  });
  s.addText("Giá trị của module A: mọi vị trí kể cả overlapping, với chặn 2n CHỨNG MINH ĐƯỢC — và là nền cho Aho–Corasick.", {
    x: M, y: 4.32, w: 12, h: 0.4, fontSize: 13, color: "C7D6E8",
    fontFace: B_FONT, margin: 0,
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.95, w: W - 2 * M, h: 1.35, rectRadius: 0.08,
    fill: { color: "2E3A6E" }, line: { color: "2E3A6E" },
  });
  s.addText("8 / 9", {
    x: M + 0.4, y: 5.15, w: 1.8, h: 0.75, fontSize: 34, bold: true,
    color: MINT, fontFace: H_FONT, margin: 0,
  });
  s.addText("khẳng định lý thuyết được số liệu xác nhận đầy đủ.", {
    x: M + 2.3, y: 5.2, w: 9.5, h: 0.35, fontSize: 15, bold: true,
    color: PAPER, fontFace: B_FONT, margin: 0,
  });
  s.addText("Khẳng định thứ 9 (mảng tốn bộ nhớ hơn hash map) đúng HƯỚNG nhưng chỉ 1,50–1,53× ở |Σ′| = 26 — do chi tiết cài đặt CPython. Em giữ nguyên kết quả này kèm phân tích thay vì lược bỏ.", {
    x: M + 2.3, y: 5.55, w: 9.8, h: 0.65, fontSize: 12, color: "C7D6E8",
    fontFace: B_FONT, margin: 0,
  });
  s.addText("Xin cảm ơn thầy và các bạn đã lắng nghe.", {
    x: M, y: 6.55, w: 8, h: 0.4, fontSize: 15, italic: true, color: MINT,
    fontFace: B_FONT, margin: 0,
  });
  addSpeakerNotes(s, 18);
}

pres.writeFile({ fileName: OUT }).then(() => {
  const kb = (fs.statSync(OUT).size / 1024).toFixed(0);
  console.log(`✓ Đã ghi: ${OUT} (${kb} KB)`);
});
