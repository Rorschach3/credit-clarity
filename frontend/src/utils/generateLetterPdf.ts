import html2pdf from "html2pdf.js";

export function generateLetterPdf(letterText: string, filename = "dispute-letter.pdf") {
  const element = document.createElement("div");
  element.style.whiteSpace = "pre-wrap";
  element.style.fontFamily = "monospace";
  element.style.fontSize = "12px";
  element.style.padding = "20px";
  element.innerText = letterText;

  html2pdf().from(element).set({
    margin: 0.5,
    filename,
    html2canvas: { scale: 2 },
    jsPDF: { unit: "in", format: "letter", orientation: "portrait" },
  }).save();
}
