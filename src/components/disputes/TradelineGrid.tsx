
import React from "react";
import { GroupedTradeline } from "@/utils/groupTradelinesByAccount";

type Bureau = "equifax" | "transunion" | "experian";

const BUREAUS: { key: Bureau; label: string; color: string }[] = [
  { key: "equifax", label: "Equifax", color: "bg-green-200" },
  { key: "transunion", label: "TransUnion", color: "bg-green-200" },
  { key: "experian", label: "Experian", color: "bg-green-200" },
];

type FieldKey =
  | "creditor_name"
  | "account_number"
  | "account_status"
  | "date_opened"
  | "account_balance"
  | "credit_limit"
  | "monthly_payment"
  | "dispute_count";

type FieldConfig = {
  key: FieldKey;
  label: string;
  format?: (v: string | number | undefined) => string;
};

const FIELDS: FieldConfig[] = [
  { key: "creditor_name", label: "Account Name" },
  { key: "account_number", label: "Account Number" },
  { key: "account_status", label: "Status" },
  { key: "date_opened", label: "Date Opened" },
  { key: "account_balance", label: "Balance" },
  { key: "credit_limit", label: "Credit Limit" },
  { key: "monthly_payment", label: "Monthly Payment" },
  { key: "dispute_count", label: "Dispute Count" },
];

function isInconsistent(values: (string | number | undefined)[]) {
  const filtered = values.filter((v) => v !== undefined && v !== "");
  return new Set(filtered).size > 1;
}

export const TradelineGrid: React.FC<{
  tradelines: GroupedTradeline[];
  onAddManual: () => void;
}> = ({ tradelines, onAddManual }) => {
  return (
    <div className="space-y-8">
      {tradelines.map((group, index) => (
        <div key={`${group.creditor_name}-${index}`} className="overflow-x-auto rounded border shadow bg-white">
          <table className="min-w-[600px] w-full text-sm">
            <thead>
              <tr>
                <th className="bg-slate-800 text-white px-3 py-2 text-left w-40">{group.creditor_name}</th>
                {BUREAUS.map((b) => (
                  <th key={b.key} className={`px-3 py-2 text-center font-bold ${b.color}`}>{b.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FIELDS.map((field) => {
                const values = BUREAUS.map((b) => {
                  const accounts = group.accounts.filter(acc => acc.credit_bureau === b.key);
                  const firstAccount = accounts[0];
                  let v: string | number | undefined = firstAccount ? (firstAccount as any)[field.key] : "";
                  if (field.format && v) v = field.format(v);
                  return v;
                });
                const inconsistent = isInconsistent(values);
                return (
                  <tr key={field.key}>
                    <td className="bg-slate-700 text-white px-3 py-2 font-semibold">{field.label}</td>
                    {values.map((v, i) => (
                      <td
                        key={BUREAUS[i].key}
                        className={`px-3 py-2 border ${inconsistent ? "bg-red-100 text-red-700 font-bold" : ""}`}
                      >
                        {v || <span className="text-slate-400">—</span>}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}
      <button onClick={onAddManual} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
        Add Manual Tradeline
      </button>
    </div>
  );
};
