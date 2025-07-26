/**
 * Generates a dispute packet PDF containing user information and selected tradelines.
 * @param userInfo - The user's personal information.
 * @param tradelines - An array of tradelines to include in the dispute.
 * @returns A promise that resolves to a Uint8Array representing the PDF bytes.
 */
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import html2pdf from "html2pdf.js";

interface Tradeline {
  creditorName: string;
  balance: number;
  status: string;
}

interface UserInfo {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

// You can extend this with more precise rendering later
function renderLetterHTML(userInfo: UserInfo, documents: File[]): HTMLElement {
  const container = document.createElement("div");
  container.innerHTML = `
    <div>
      <p>${userInfo.name}</p>
      <p>${userInfo.address}</p>
      <p>${userInfo.city}, ${userInfo.state} ${userInfo.zip}</p>
      <p>Date: ${new Date().toLocaleDateString()}</p>
      <br />
      <p>To Whom It May Concern,</p>
      <p>I am writing to dispute items on my credit report. Please investigate and remove inaccuracies.</p>
      <br />
      <p>Sincerely,</p>
      <p>${userInfo.name}</p>
    </div>
  `;
  return container;
}

function renderLetterHTML(userInfo: UserInfo, documents: File[]): HTMLElement {
  const container = document.createElement("div");
  container.innerHTML = `
    <div>
      <p>${userInfo.name}</p>
      <p>${userInfo.address}</p>
      <p>${userInfo.city}, ${userInfo.state} ${userInfo.zip}</p>
      <p>Date: ${new Date().toLocaleDateString()}</p>
      <br />
      <p>To Whom It May Concern,</p>
      <p>I am writing to dispute items on my credit report. Please investigate and remove inaccuracies.</p>
      <br />
      <p>Sincerely,</p>
      <p>${userInfo.name}</p>
    </div>
  `;
  return container;
}

export async function generateDisputePacketPdf(
  userInfo: UserInfo,
  documents: File[]
): Promise<Blob> {
  const element = renderLetterHTML(userInfo, documents);

  return new Promise<Blob>((resolve, reject) => {
    html2pdf()
      .from(element)
      .outputPdf("blob")
      .then(resolve)
      .catch(reject);
  });
}