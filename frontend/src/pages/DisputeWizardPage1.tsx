// "use client";

// import React, { useState, useEffect, useRef, ChangeEvent } from "react";
// import { createWorker, Worker } from "tesseract.js";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import { Textarea } from "@/components/ui/textarea";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { toast } from "@/components/ui/use-toast";
// import { Progress } from "@/components/ui/progress";
// import { pdfToImages } from "@/utils/pdfToImage";
// import { parseTradelinesFromText, ParsedTradeline, saveTradelinesToDatabase } from "@/utils/tradelineParser";
// import { useAuth } from "@/hooks/use-auth";
// import { aiService } from "@/utils/ai-service";
// import { supabase } from "../../supabase/client";
// import { UserDocumentsSection } from "@/components/disputes/UserDocumentsSection";
// import { PDFDocument, rgb, StandardFonts } from "pdf-lib";

// const DEFAULT_COMPLIANCE_NOTE = `IMPORTANT: Include a copy of your government-issued ID and a recent utility bill or bank statement to verify your identity. Mail your dispute letter to the appropriate credit bureau address.`;

// const BUREAU_ADDRESSES = [
//   {
//     name: "Equifax",
//     address: `Equifax Information Services LLC
// P.O. Box 740256
// Atlanta, GA 30374-0256`
//   },
//   {
//     name: "Experian",
//     address: `Experian
// P.O. Box 4500
// Allen, TX 75013`
//   },
//   {
//     name: "TransUnion",
//     address: `TransUnion Consumer Solutions
// P.O. Box 2000
// Chester, PA 19016-2000`
//   }
// ];

// const DisputeWizardPage = () => {
//   const { user } = useAuth();
//   const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
//   const [selected, setSelected] = useState<ParsedTradeline[]>([]);
//   const [name, setName] = useState("");
//   const [address, setAddress] = useState("");
//   const [city, setCity] = useState("");
//   const [stateVal, setStateVal] = useState("");
//   const [zip, setZip] = useState("");
//   const [letter, setLetter] = useState("");
//   const [uploading, setUploading] = useState(false);
//   const [uploadProgress, setUploadProgress] = useState(0);
//   const [editingLetter, setEditingLetter] = useState(false);
//   const [manualModalOpen, setManualModalOpen] = useState(false);
//   const [manualTradeline, setManualTradeline] = useState<ParsedTradeline>({
//     creditorName: "",
//     accountNumber: "",
//     accountStatus: "",
//     isNegative: true,
//     negativeReason: "",
//     accountBalance: "", // Changed to string to match ParsedTradeline type
//     dateOpened: ""
//   });
//   const [complianceNote] = useState(DEFAULT_COMPLIANCE_NOTE);
//   const [savingLetter, setSavingLetter] = useState(false);
//   const [packetLoading, setPacketLoading] = useState(false);
//   const [showDocsSection, setShowDocsSection] = useState(false);
//   const [docsSectionCollapsed, setDocsSectionCollapsed] = useState(false);
//   // Removed workerRef as Tesseract.js is no longer used client-side
//   // const workerRef = useRef<Worker | null>(null);

//   // Removed useEffect for worker initialization
//   // useEffect(() => {
//   //   const initializeWorker = async () => {
//   //     const worker = await createWorker();
//   //     workerRef.current = worker;
//   //   };
//   //   initializeWorker();

//   //   return () => {
//   //     if (workerRef.current) {
//   //       workerRef.current.terminate();
//   //     }
//   //   };
//   // }, []);

//   const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
//     const file = event.target.files?.[0];
//     if (!file) {
//       toast({ title: "No file selected", description: "Please select a PDF file to upload." });
//       return;
//     }

//     if (file.type !== "application/pdf") {
//       toast({ title: "Invalid file type", description: "Only PDF files are supported." });
//       return;
//     }

//     setUploading(true);
//     setUploadProgress(0);
//     setTradelines([]);
//     setSelected([]);
//     setLetter("");

//     try {
//       // Read file as Data URL (base64)
//       const reader = new FileReader();
//       reader.readAsDataURL(file);

//       reader.onloadend = async () => {
//         const base64data = reader.result;
//         if (typeof base64data !== 'string') {
//           toast({ title: "Upload Failed", description: "Failed to read file content." });
//           setUploading(false);
//           return;
//         }

//         setUploadProgress(50); // Indicate file is being sent

//         const { data, error } = await supabase.functions.invoke('upload-credit-report', {
//           body: { file: base64data },
//         });

//         if (error) {
//           throw new Error(error.message || 'Failed to upload file to Supabase function.');
//         }

//         setUploadProgress(100);
//         toast({ title: "File Uploaded", description: "Your PDF has been successfully uploaded for processing." });

//         // Assuming server-side processing will eventually provide tradelines,
//         // for now, we just indicate success.
//         // In a real application, you'd fetch the processed tradelines here.

//       };

//       reader.onerror = (error) => {
//         console.error("Error reading file:", error);
//         toast({ title: "File Read Error", description: "Failed to read the selected file." });
//         setUploading(false);
//       };

//     } catch (error) {
//       console.error("Error uploading PDF:", error);
//       toast({ title: "Upload Failed", description: `There was an error uploading your PDF: ${error instanceof Error ? error.message : String(error)}` });
//     } finally {
//       setUploading(false);
//     }
//   };

//   const handleToggle = (t: ParsedTradeline) => {
//     if (!t.isNegative) {
//       toast({ title: "Cannot dispute positive tradeline", description: "Only negative tradelines can be added to the dispute letter." });
//       return;
//     }
//     setSelected((prev) =>
//       prev.includes(t)
//         ? prev.filter((x) => x !== t)
//         : [...prev, t]
//     );
//   };

//   const handleManualTradelineAdd = () => {
//     if (!manualTradeline.creditorName || !manualTradeline.accountNumber) {
//       toast({ title: "Missing Info", description: "Please enter both creditor name and account number." });
//       return;
//     }
//     setTradelines((prev) => [...prev, { ...manualTradeline }]);
//     setManualTradeline({
//       creditorName: "",
//       accountNumber: "",
//       accountStatus: "",
//       isNegative: true,
//       negativeReason: "",
//       accountBalance: 0,
//       dateOpened: ""
//     });
//     setManualModalOpen(false);
//   };

//   const handleDownload = () => {
//     const blob = new Blob([letter], { type: "text/plain" });
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement("a");
//     a.href = url;
//     a.download = "dispute_letter.txt";
//     a.click();
//     URL.revokeObjectURL(url);
//   };

//   const handlePrint = () => {
//     const printWindow = window.open("", "_blank");
//     if (printWindow) {
//       printWindow.document.write(`<pre>${letter}</pre>`);
//       printWindow.document.close();
//       printWindow.print();
//     }
//   };

//   // Save the generated letter to the database
//   const saveLetterToDatabase = async () => {
//     if (!user) {
//       toast({ title: "Authentication Required", description: "Please sign in to save your letter." });
//       return;
//     }
//     setSavingLetter(true);
//     try {
//       // For demo, use the first selected bureau or "Equifax"
//       const creditBureau = selected[0]?.creditorName || "Equifax";
//       const { error } = await supabase.from("disputes").insert({
//         user_id: user.id,
//         letter_content: letter,
//         mailing_address: address,
//         credit_bureau: creditBureau,
//         status: "draft"
//       });
//       if (error) {
//         toast({ title: "Save Failed", description: error.message });
//       } else {
//         toast({ title: "Letter Saved", description: "Your dispute letter has been saved to your account." });
//       }
//     } catch (err) {
//       toast({ title: "Save Error", description: "Failed to save letter." });
//     } finally {
//       setSavingLetter(false);
//     }
//   };

//   // Prepare Dispute Packet: combine letter and uploaded docs into a single PDF
//   const prepareDisputePacket = async () => {
//     if (!user) {
//       toast({ title: "Authentication Required", description: "Please sign in to prepare your packet." });
//       return;
//     }
//     setPacketLoading(true);
//     try {
//       // 1. Create a new PDF and add the letter as the first page
//       const pdfDoc = await PDFDocument.create();
//       const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
//       const page = pdfDoc.addPage();
//       const { width, height } = page.getSize();
//       const fontSize = 12;
//       const lines = letter.split("\n");
//       let y = height - 40;
//       for (const line of lines) {
//         page.drawText(line, { x: 40, y, size: fontSize, font, color: rgb(0, 0, 0) });
//         y -= fontSize + 4;
//         if (y < 40) {
//           y = height - 40;
//           pdfDoc.addPage();
//         }
//       }

//       // 2. Fetch uploaded user documents from Supabase
//       // This section is commented out as it's not directly related to the PDF upload task
//       // and was causing type errors. It should be re-evaluated for proper implementation
//       // if document fetching is required for packet preparation.
//       /*
//       type UserDocuments = {
//         id: string;
//         user_id: string;
//         photo_id: string;
//         ssn_card: string;
//         utility_bill: string;
//       };
//       const { data, error } = await supabase
//         .from<UserDocuments>("user_documents")
//         .select("*")
//         .eq("user_id", user.id)
//         .single();

//       if (error) {
//         toast({ title: "Document Fetch Error", description: error.message });
//         setPacketLoading(false);
//         return;
//       }

//       // 3. For each document type, fetch the file from storage and add as a new page
//       const docTypes = [
//         { key: "photo_id", label: "Government-Issued Photo ID" },
//         { key: "ssn_card", label: "Social Security Card" },
//         { key: "utility_bill", label: "Utility Bill" }
//       ];
//       for (const docType of docTypes) {
//         const fileUrl = data?.[docType.key];
//         if (!fileUrl) continue;
//         const response = await fetch(fileUrl);
//         const fileBlob = await response.blob();
//         const fileType = fileBlob.type;

//         if (fileType === "application/pdf") {
//           const docBytes = await fileBlob.arrayBuffer();
//           const docPdf = await PDFDocument.load(docBytes);
//           const copiedPages = await pdfDoc.copyPages(docPdf, docPdf.getPageIndices());
//           copiedPages.forEach((p) => pdfDoc.addPage(p));
//         } else if (fileType.startsWith("image/")) {
//           const imgBytes = await fileBlob.arrayBuffer();
//           let img;
//           if (fileType === "image/png") {
//             img = await pdfDoc.embedPng(imgBytes);
//           } else {
//             img = await pdfDoc.embedJpg(imgBytes);
//           }
//           const imgPage = pdfDoc.addPage();
//           const { width: imgW, height: imgH } = img.scale(1);
//           imgPage.drawImage(img, {
//             x: 40,
//             y: 40,
//             width: Math.min(imgW, imgPage.getWidth() - 80),
//             height: Math.min(imgH, imgPage.getHeight() - 80)
//           });
//         }
//       }
//       */

//       // 4. Download the combined PDF
//       const pdfBytes = await pdfDoc.save();
//       const blob = new Blob([pdfBytes], { type: "application/pdf" });
//       const url = URL.createObjectURL(blob);
//       const a = document.createElement("a");
//       a.href = url;
//       a.download = "dispute_packet.pdf";
//       a.click();
//       URL.revokeObjectURL(url);
//       toast({ title: "Packet Ready", description: "Your dispute packet PDF is ready for download." });
//     } catch (err) {
//       toast({ title: "Packet Error", description: "Failed to prepare dispute packet." });
//     } finally {
//       setPacketLoading(false);
//     }
//   };

//   const generateLetter = async () => {
//     if (!name || !address || selected.length === 0) {
//       toast({ title: "Missing Info", description: "Please fill in your name and address, and select at least one tradeline to dispute." });
//       return;
//     }

//     // Compose context for AI
//     const itemText = selected
//       .map(
//         (t, i) => `Item ${i + 1}: ${t.creditorName}
// Account Number: ${t.accountNumber}
// Reason: ${t.negativeReason || "This item is inaccurate or does not belong to me."}`
//       )
//       .join("\n\n");

//     const prompt = `
// You are an expert credit dispute letter writer. Generate a professional, compliant, and persuasive dispute letter for the following user and tradelines. Use a respectful tone, reference FCRA Section 611, and include all necessary compliance language. Do not include [Date] or [Signature] lines.

// User Name: ${name}
// User Address: ${address}
// City: ${city}
// State: ${stateVal}
// Zip: ${zip}

// Tradelines to Dispute:
// ${itemText}
// `;

//     setLetter("Generating letter...");
//     setEditingLetter(false);

//     try {
//       const aiLetter = await aiService.chatCompletion([
//         { role: "system", content: "You are a helpful assistant for credit repair. Write dispute letters for users based on their selected tradelines and reasons." },
//         { role: "user", content: prompt }
//       ], "gpt-3.5-turbo-16k", 2048);
//       setLetter(aiLetter.trim());
//       setEditingLetter(true);
//     } catch (err) {
//       toast({ title: "AI Error", description: "Failed to generate letter with AI. Using fallback template." });
//       const fallback = `
// ${name}
// ${address}
// ${city}, ${stateVal} ${zip}

// To Whom It May Concern,

// I am formally disputing the following items from my credit report:

// ${itemText}

// Under the Fair Credit Reporting Act (FCRA), Section 611, I request a thorough investigation within 30 days. Please correct or remove any inaccurate information and send me an updated report.

// Sincerely,
// ${name}`.trim();
//       setLetter(fallback);
//       setEditingLetter(true);
//     }
//   };

//   return (
//     <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
//       <Card className="max-w-6xl mx-auto space-y-6">
//         <CardHeader>
//           <CardTitle className="text-2xl">Dispute Wizard</CardTitle>
//         </CardHeader>
//         <CardContent className="space-y-6">
//           <div>
//             <Label htmlFor="pdf-upload">Upload Credit Report (PDF)</Label>
//             <Input id="pdf-upload" type="file" accept="application/pdf" onChange={handleFileUpload} disabled={uploading} />
//             {uploading && (
//               <div className="mt-2">
//                 <Progress value={uploadProgress} className="w-full" />
//                 <p className="text-sm text-muted-foreground mt-1">Processing: {uploadProgress}%</p>
//               </div>
//             )}
//           </div>

//           {tradelines.length > 0 && (
//             <div>
//               <div className="flex items-center justify-between mb-2">
//                 <Label className="block">Select Tradelines to Dispute</Label>
//                 <Button size="sm" variant="outline" onClick={() => setManualModalOpen(true)}>
//                   + Add Tradeline Manually
//                 </Button>
//               </div>
//               {tradelines.map((t, i) => (
//                 <div key={i} className="border p-4 rounded mb-3 space-y-2">
//                   <div><strong>{t.creditorName}</strong></div>
//                   <div>Account #: {t.accountNumber}</div>
//                   <div>Status: {t.account_status} — Negative: {t.isNegative ? "Yes" : "No"}</div>
//                   {t.negativeReason && <div>Reason: {t.negativeReason}</div>}
//                   <div>Balance: ${t.account_balance?.toFixed(2) || '0.00'}</div>
//                   <div>Date Opened: {t.dateOpened || 'N/A'}</div>
//                   <Input
//                     placeholder="Reason for Dispute (optional, overrides detected reason)"
//                     defaultValue={t.negativeReason}
//                     onChange={(e) => (t.negativeReason = e.target.value)}
//                   />
//                   <Button
//                     variant={selected.includes(t) ? "destructive" : "default"}
//                     onClick={() => handleToggle(t)}
//                     disabled={!t.isNegative && !selected.includes(t)}
//                   >
//                     {selected.includes(t) ? "Remove from Dispute" : (!t.isNegative ? "Cannot Dispute" : "Add to Dispute")}
//                   </Button>
//                 </div>
//               ))}
//             </div>
//           )}

//           <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//             <div>
//               <Label htmlFor="your-name">Your Name</Label>
//               <Input id="your-name" value={name} onChange={(e) => setName(e.target.value)} />
//             </div>
//             <div>
//               <Label htmlFor="your-address">Address</Label>
//               <Input id="your-address" value={address} onChange={(e) => setAddress(e.target.value)} />
//             </div>
//             <div>
//               <Label htmlFor="your-city">City</Label>
//               <Input id="your-city" value={city} onChange={(e) => setCity(e.target.value)} />
//             </div>
//             <div>
//               <Label htmlFor="your-state">State</Label>
//               <Input id="your-state" value={stateVal} onChange={(e) => setStateVal(e.target.value)} />
//             </div>
//             <div>
//               <Label htmlFor="your-zip">Zip</Label>
//               <Input id="your-zip" value={zip} onChange={(e) => setZip(e.target.value)} />
//             </div>
//           </div>

//           <Button
//             onClick={generateLetter}
//             disabled={
//               selected.length === 0 ||
//               !name ||
//               !address ||
//               !city ||
//               !stateVal ||
//               !zip
//             }
//           >
//             Generate Letter
//           </Button>

//           {letter && (
//             <div className="space-y-4">
//               <Label>Edit & Export Letter</Label>
//               <Textarea
//                 rows={12}
//                 value={letter}
//                 onChange={e => setLetter(e.target.value)}
//                 className="font-mono"
//                 readOnly={!editingLetter}
//               />
//               <div className="flex gap-2">
//                 <Button onClick={handleDownload} variant="outline">Download</Button>
//                 <Button onClick={handlePrint} variant="outline">Print</Button>
//                 <Button onClick={saveLetterToDatabase} variant="outline" disabled={savingLetter}>
//                   {savingLetter ? "Saving..." : "Save to Account"}
//                 </Button>
//                 <Button onClick={() => setShowDocsSection(true)} variant="default">
//                   Add Optional Identity Docs & Prepare Dispute Packet
//                 </Button>
//               </div>
//               <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
//                 <strong>Mailing Instructions:</strong>
//                 <ul className="list-disc ml-6 mt-2">
//                   {BUREAU_ADDRESSES.map((b, idx) => (
//                     <li key={idx}>
//                       <span className="font-semibold">{b.name}:</span>
//                       <pre className="whitespace-pre-wrap">{b.address}</pre>
//                     </li>
//                   ))}
//                 </ul>
//                 <div className="mt-2 text-sm text-yellow-800">{complianceNote}</div>
//               </div>
//               {/* Optional Identity Docs Section */}
//               {showDocsSection && (
//                 <div
//                   className={`mt-8 transition-all duration-500 ${docsSectionCollapsed ? "max-h-0 overflow-hidden opacity-0" : "max-h-[2000px] opacity-100"
//                     }`}
//                 >
//                   <div className="flex flex-col items-center mb-6">
//                     <Button
//                       variant="secondary"
//                       className="mb-4"
//                       onClick={() => {
//                         setDocsSectionCollapsed(true);
//                         setTimeout(() => {
//                           setShowDocsSection(false);
//                         }, 600); // match transition duration
//                       }}
//                     >
//                       Skip Document Upload & Continue
//                     </Button>
//                     {docsSectionCollapsed && (
//                       <div className="w-full text-center text-green-700 bg-green-50 border border-green-200 rounded p-3 mt-2 transition-all duration-500">
//                         Document upload skipped. You may proceed to the next step.
//                       </div>
//                     )}
//                   </div>
//                   {!docsSectionCollapsed && (
//                     <>
//                       <h3 className="text-lg font-semibold mb-2 text-center">Upload Supporting Documents (Optional)</h3>
//                       <UserDocumentsSection />
//                       <div className="flex gap-2 mt-4">
//                         <Button onClick={prepareDisputePacket} variant="default" disabled={packetLoading}>
//                           {packetLoading ? "Preparing..." : "Prepare Dispute Packet"}
//                         </Button>
//                         <Button variant="outline" onClick={() => setShowDocsSection(false)}>
//                           Cancel
//                         </Button>
//                       </div>
//                     </>
//                   )}
//                 </div>
//               )}
//             </div>
//           )}

//           {/* Manual Tradeline Modal */}
//           {manualModalOpen && (
//             <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
//               <div className="bg-white p-6 rounded shadow-lg w-full max-w-md">
//                 <h3 className="text-lg font-semibold mb-2">Add Tradeline Manually</h3>
//                 <div className="space-y-2">
//                   <Input
//                     placeholder="Creditor Name"
//                     value={manualTradeline.creditorName}
//                     onChange={e => setManualTradeline({ ...manualTradeline, creditorName: e.target.value })}
//                   />
//                   <Input
//                     placeholder="Account Number"
//                     value={manualTradeline.accountNumber}
//                     onChange={e => setManualTradeline({ ...manualTradeline, accountNumber: e.target.value })}
//                   />
//                   <Input
//                     placeholder="Status"
//                     value={manualTradeline.account_status}
//                     onChange={e => setManualTradeline({ ...manualTradeline, account_status: e.target.value })}
//                   />
//                   <Input
//                     placeholder="Reason for Dispute"
//                     value={manualTradeline.negativeReason}
//                     onChange={e => setManualTradeline({ ...manualTradeline, negativeReason: e.target.value })}
//                   />
//                   <Input
//                     placeholder="Balance"
//                     type="number"
//                     value={manualTradeline.account_balance}
//                     onChange={e => setManualTradeline({ ...manualTradeline, account_balance: Number(e.target.value) })}
//                   />
//                   <Input
//                     placeholder="Date Opened"
//                     value={manualTradeline.dateOpened}
//                     onChange={e => setManualTradeline({ ...manualTradeline, dateOpened: e.target.value })}
//                   />
//                 </div>
//                 <div className="flex gap-2 mt-4">
//                   <Button onClick={handleManualTradelineAdd}>Add</Button>
//                   <Button variant="outline" onClick={() => setManualModalOpen(false)}>Cancel</Button>
//                 </div>
//               </div>
//             </div>
//           )}

//           {/* Document Upload Section */}
//           <div className="mt-8">
//             <h3 className="text-lg font-semibold mb-2">Upload Supporting Documents</h3>
//             <UserDocumentsSection />
//           </div>
//         </CardContent>
//       </Card>
//     </div>
//   );
// };

// export default DisputeWizardPage;