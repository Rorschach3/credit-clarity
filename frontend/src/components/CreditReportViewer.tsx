import React, { useState, useEffect } from "react";
import { aiService } from "@/utils/ai-service";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { z } from "zod";
import { AccountSchema, Account } from "@/utils/ai-service";

const CreditReportViewerPropsSchema = z.object({
  fileUrl: z.string(),
  bureau: z.string(),
  onClose: z.function().args().returns(z.void()),
  ocrText: z.string(),
});

type CreditReportViewerProps = z.infer<typeof CreditReportViewerPropsSchema>;


const CreditReportViewer: React.FC<CreditReportViewerProps> = (props) => {
  const { fileUrl, bureau, onClose, ocrText } = CreditReportViewerPropsSchema.parse(props);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [labeledAccounts, setLabeledAccounts] = useState<(Account & { isNegative: boolean; reason: string })[]>([]);

  useEffect(() => {
    const loadAccounts = async () => {
      try {
        const accts = await aiService.ExtractedAccounts(ocrText);
        const validatedAccounts = z.array(AccountSchema).parse(accts);
        setAccounts(validatedAccounts);
      } catch (err) {
        console.error("Error loading accounts:", err);
      }
    };
    loadAccounts();
  }, [ocrText]);

  useEffect(() => {
    if (accounts.length === 0) return;
    const labelAccounts = async () => {
      try {
        const results = await Promise.all(
          accounts.map(async account => {
            const { isNegative, reason } = await aiService.classifyTradeline(
              account.name + account.status + account.paymentHistory + account.balance
            );
            return { ...account, isNegative, reason };
          })
        );
        setLabeledAccounts(results);
      } catch (err) {
        console.error("Error labeling accounts:", err);
      }
    };
    labelAccounts();
  }, [accounts]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-11/12 max-w-5xl h-4/5 flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-lg font-semibold">{`Credit Report - ${bureau}`}</h2>
          <button
            onClick={onClose}
            className="text-gray-600 hover:text-gray-900 focus:outline-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <Card>
          {labeledAccounts.map((account, idx) => (
            <div key={idx} className="border p-4 mb-2 rounded-md shadow">
              <h3 className="text-lg font-semibold">{account.name}</h3>
              <p>Status: {account.status}</p>
              <p>Balance: {account.balance}</p>
              {account.isNegative && (
                <Badge variant="destructive">Negative: {account.reason}</Badge>
              )}
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
};

export default CreditReportViewer;