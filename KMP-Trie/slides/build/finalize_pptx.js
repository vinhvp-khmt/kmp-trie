/**
 * Hoàn thiện PPTX sau khi PptxGenJS sinh file:
 * - giữ lời thoại trong Notes Placeholder của từng slide;
 * - mở bài ở Normal View với vùng Speaker Notes đủ lớn để nhìn thấy ngay;
 * - đặt ngôn ngữ notes là tiếng Việt.
 */

const fs = require("fs");
const path = require("path");
const JSZip = require("jszip");

const pptxPath = process.argv[2];
if (!pptxPath) {
  throw new Error("Thiếu đường dẫn PPTX cần hoàn thiện.");
}

async function main() {
  const input = await fs.promises.readFile(pptxPath);
  const zip = await JSZip.loadAsync(input);

  const viewFile = zip.file("ppt/viewProps.xml");
  if (!viewFile) {
    throw new Error("PPTX không có ppt/viewProps.xml.");
  }

  let viewXml = await viewFile.async("string");
  viewXml = viewXml
    .replace(
      /<p:viewPr([^>]*)>/,
      (_, attrs) => `<p:viewPr${attrs.replace(/\s+lastView="[^"]*"/, "")} lastView="sldThumbnailView">`
    )
    .replace(
      /<p:normalViewPr(?:\s+horzBarState="[^"]*")?>/,
      "<p:normalViewPr>"
    )
    .replace(
      /<p:restoredTop sz="\d+"\/>/,
      '<p:restoredTop sz="76000"/>'
    );
  zip.file("ppt/viewProps.xml", viewXml);

  const noteFiles = Object.keys(zip.files)
    .filter((name) => /^ppt\/notesSlides\/notesSlide\d+\.xml$/.test(name))
    .sort((a, b) => {
      const numberOf = (name) => Number(name.match(/notesSlide(\d+)\.xml$/)[1]);
      return numberOf(a) - numberOf(b);
    });

  if (noteFiles.length !== 18) {
    throw new Error(`PPTX phải có 18 Notes Slide; hiện có ${noteFiles.length}.`);
  }

  for (const name of noteFiles) {
    const file = zip.file(name);
    let xml = await file.async("string");
    const bodyMatch = xml.match(
      /<p:ph type="body"[^>]*\/>[\s\S]*?<p:txBody>[\s\S]*?<a:t>([\s\S]*?)<\/a:t>/
    );
    if (!bodyMatch || !bodyMatch[1].trim()) {
      throw new Error(`${name} chưa có lời thoại trong Notes Placeholder.`);
    }
    xml = xml.replaceAll('lang="en-US"', 'lang="vi-VN"');
    zip.file(name, xml);
  }

  const output = await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  });
  const tempPath = `${pptxPath}.tmp`;
  await fs.promises.writeFile(tempPath, output);
  await fs.promises.rename(tempPath, pptxPath);

  console.log(
    `✓ Đã nhúng và kiểm tra speaker notes trực tiếp trong ${noteFiles.length} slide`
  );
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
