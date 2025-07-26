import React from "react";
import { GroupedTradeline, Bureau } from "@/utils/groupTradelinesByAccount";

const BUREAUS: { key: Bureau; label: string }[] = [
  { key: "equifax", label: "Equifax" },
  { key: "transunion", label: "TransUnion" },
  { key: "experian", label: "Experian" },
];

type FieldKey =
  | "accountName"
  | "accountNumber"
  | "status"
  | "dateOpened"
  | "balance"
  | "type"
  | "creditLimit"
  | "monthlyPayment"
  | "disputeCount";

type FieldConfig = {
  key: FieldKey;
  label: string;
  format?: (v: string | number | undefined) => string;
};

const FIELDS: FieldConfig[] = [
  { key: "accountName", label: "Account Name" },
  { key: "accountNumber", label: "Account Number" },
  { key: "status", label: "Status" },
  { key: "dateOpened", label: "Date Opened" },
  { key: "balance", label: "Balance", format: (v) => v != null ? `$${Number(v).toFixed(2)}` : "" },
  { key: "type", label: "Type" },
  { key: "creditLimit", label: "Credit Limit", format: (v) => v != null ? `$${Number(v).toFixed(2)}` : "" },
  { key: "monthlyPayment", label: "Monthly Payment", format: (v) => v != null ? `$${Number(v).toFixed(2)}` : "" },
  { key: "disputeCount", label: "Dispute Count" },
];

const NEGATIVE_STATUSES = ["chargeoff", "collections", "latepayment"];

function isInconsistent(values: (string | number | undefined)[]) {
  const filtered = values.filter((v) => v !== undefined && v !== "");
  return new Set(filtered).size > 1;
}

export const TradelineGrid: React.FC<{ tradelines: GroupedTradeline[] }> = ({ tradelines }) => {
  return (
    <div className="space-y-8">
      {tradelines.map((group) => {
        const statusValues = BUREAUS.map((b) => {
          const t = group[b.key];
          const s = t?.status?.toLowerCase();
          return s && NEGATIVE_STATUSES.includes(s);
        });

        return (
          <div key={group.key} className="overflow-x-auto rounded border shadow bg-white">
            <table className="min-w-[600px] w-full text-sm">
              <thead>
                <tr>
                  <th className="bg-slate-800 text-white px-3 py-2 text-left w-40">Bureau</th>
                  {BUREAUS.map((b, i) => (
                    <th
                      key={b.key}
                      className={`px-3 py-2 text-center font-bold text-black ${statusValues[i] ? "bg-red-200 text-red-800" : "bg-green-200 text-green-800"}`}
                    >
                      {b.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FIELDS.map((field) => {
                  const values = BUREAUS.map((b) => {
                    const t = group[b.key];
                    let v: string | number | undefined = t ? t[field.key] : "";
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
                          className={`px-3 py-2 border text-center: ""}`}
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
        );
      })}
    </div>
  );
};
