import { getDocument, GlobalWorkerOptions, PDFDocumentProxy } from 'pdfjs-dist';

GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@5.3.31/build/pdf.worker.min.mjs`;

export async function pdfToImages(buffer: ArrayBuffer): Promise<string[]> {
  let pdf: PDFDocumentProxy;
  try {
    pdf = await getDocument({ data: buffer }).promise;
    console.log(`[pdfToImage] PDF loaded successfully with ${pdf.numPages} pages.`);
  } catch (error) {
    console.error("[pdfToImage] Error loading PDF:", error);
    throw error;
  }
  const images: string[] = [];

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: 2.0 });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    const context = canvas.getContext("2d");
    if (!context) throw new Error("Failed to get canvas 2D context");

    await page.render({ canvasContext: context, viewport }).promise;
    images.push(canvas.toDataURL("image/png"));
  }
  console.log(`[pdfToImage] Generated ${images.length} images. First image size: ${images[0]?.length || 0} bytes.`);
  return images;
}
