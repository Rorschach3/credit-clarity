import { PDFDocument, rgb, StandardFonts } from "pdf-lib";

interface UserDocuments {
  photo_id?: string;
  ssn_card?: string;
  utility_bill?: string;
}

export async function prepareDisputePacket(letter: string, userDocuments: UserDocuments): Promise<Blob> {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const page = pdfDoc.addPage();
  const { width, height } = page.getSize();
  const fontSize = 12;

  const lines = letter.split("\n");
  let y = height - 40;
  for (const line of lines) {
    page.drawText(line, { x: 40, y, size: fontSize, font, color: rgb(0, 0, 0) });
    y -= fontSize + 4;
    if (y < 40) {
      y = height - 40;
      pdfDoc.addPage();
    }
  }

  const docTypes = ["photo_id", "ssn_card", "utility_bill"] as const;
  for (const key of docTypes) {
    const url = userDocuments[key];
    if (!url) continue;
    const response = await fetch(url);
    const fileBlob = await response.blob();
    const fileType = fileBlob.type;

    if (fileType === "application/pdf") {
      const docBytes = await fileBlob.arrayBuffer();
      const docPdf = await PDFDocument.load(docBytes);
      const copiedPages = await pdfDoc.copyPages(docPdf, docPdf.getPageIndices());
      copiedPages.forEach((p) => pdfDoc.addPage(p));
    } else if (fileType.startsWith("image/")) {
      const imgBytes = await fileBlob.arrayBuffer();
      const img = fileType === "image/png"
        ? await pdfDoc.embedPng(imgBytes)
        : await pdfDoc.embedJpg(imgBytes);

      const imgPage = pdfDoc.addPage();
      const { width: imgW, height: imgH } = img.scale(1);
      imgPage.drawImage(img, {
        x: 40,
        y: 40,
        width: Math.min(imgW, imgPage.getWidth() - 80),
        height: Math.min(imgH, imgPage.getHeight() - 80),
      });
    }
  }

  const pdfBytes = await pdfDoc.save();
  return new Blob([pdfBytes], { type: "application/pdf" });
}
