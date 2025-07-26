import { pdfjs } from 'react-pdf';
import workerUrl from "pdfjs-dist/build/pdf.worker.js?url";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
export const pdfWorker = workerUrl;