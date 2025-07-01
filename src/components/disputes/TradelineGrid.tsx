
import React from "react";
import { GroupedTradeline, Bureau } from "@/utils/groupTradelinesByAccount";

const BUREAUS: { key: Bureau; label: string; color: string }[] = [
  { key: "equifax", label: "Equifax", color: "bg-green-200" },
  { key: "transunion", label: "TransUnion", color: "bg-green-200" },
  { key: "experian", label: "Experian", color: "bg-green-200" },
];

type FieldKey =
  | "account_name"
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
  { key: "account_name", label: "Account Name" },
  { key: "account_number", label: "Account Number" },
  { key: "account_status", label: "Status" },
  { key: "date_opened", label: "Date Opened" },
  { key: "account_balance", label: "Balance", format: (v) => v != null ? `$${Number(v).toFixed(2)}` : "" },
  { key: "credit_limit", label: "Credit Limit", format: (v) => v != null ? `$${Number(v).toFixed(2)}` : "" },
  { key: "monthly_payment", label: "Monthly Payment", format: (v) => v != null ? `$${Number(v).toFixed(2)}` : "" },
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
      {tradelines.map((group) => (
        <div key={group.key} className="overflow-x-auto rounded border shadow bg-white">
          <table className="min-w-[600px] w-full text-sm">
            <thead>
              <tr>
                <th className="bg-slate-800 text-white px-3 py-2 text-left w-40"></th>
                {BUREAUS.map((b) => (
                  <th key={b.key} className={`px-3 py-2 text-center font-bold ${b.color}`}>{b.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FIELDS.map((field) => {
                const values = BUREAUS.map((b) => {
                  const t = group[b.key];
                  let v: string | number | undefined = t ? (t as any)[field.key] : "";
                  if (field.format) v = field.format(v);
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
      <button onClick={onAddManual}>Add Manual Tradeline</button>
    </div>
  );
};
