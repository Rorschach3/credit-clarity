import React from "react";

const BUREAU_ADDRESSES = [
  {
    name: "Equifax",
    address: `Equifax Information Services LLC\nP.O. Box 740256\nAtlanta, GA 30374-0256`,
  },
  {
    name: "Experian",
    address: `Experian\nP.O. Box 4500\nAllen, TX 75013`,
  },
  {
    name: "TransUnion",
    address: `TransUnion Consumer Solutions\nP.O. Box 2000\nChester, PA 19016-2000`,
  },
];

const DEFAULT_COMPLIANCE_NOTE = `IMPORTANT: Include a copy of your government-issued ID and a recent utility bill or bank statement to verify your identity. Mail your dispute letter to the appropriate credit bureau address.`;

export const MailingInstructions: React.FC = () => {
  return (
    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
      <strong>Mailing Instructions:</strong>
      <ul className="list-disc ml-6 mt-2">
        {BUREAU_ADDRESSES.map((b, idx) => (
          <li key={idx}>
            <span className="font-semibold">{b.name}:</span>
            <pre className="whitespace-pre-wrap">{b.address}</pre>
          </li>
        ))}
      </ul>
      <div className="mt-2 text-sm text-yellow-800">{DEFAULT_COMPLIANCE_NOTE}</div>
    </div>
  );
};
