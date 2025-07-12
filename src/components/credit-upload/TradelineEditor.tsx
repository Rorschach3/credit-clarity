import React from 'react';
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelineEditorProps {
  tradeline: ParsedTradeline;
  index: number; // Keep for display purposes if needed
  isSelected: boolean;
  onUpdate: (updates: Partial<ParsedTradeline>) => void; // ✅ Simplified - no index needed
  onDelete: () => void; // ✅ Simplified - no index needed
  onSelect: (selected: boolean) => void; // ✅ Simplified - no id needed
}

export const TradelineEditor: React.FC<TradelineEditorProps> = ({
  tradeline,
  isSelected,
  onUpdate,
  onDelete,
  onSelect
}) => {
  
  const handleFieldUpdate = (field: keyof ParsedTradeline, value: string | boolean) => {
    onUpdate({ [field]: value }); // ✅ Just pass the updates, parent handles ID
  };

  const handleDelete = () => {
    onDelete(); // ✅ Just call delete, parent handles ID
  };

  const handleSelect = (checked: boolean) => {
    onSelect(checked); // ✅ Just pass selection state, parent handles ID
  };

  return (
    <div className="border rounded-lg p-4 mb-4">
      {/* Selection checkbox */}
      <div className="flex items-center mb-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => handleSelect(e.target.checked)}
          className="mr-2"
        />
        <h3 className="font-semibold">{tradeline.creditor_name || 'Unknown Creditor'}</h3>
      </div>

      {/* Editable fields */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Creditor Name</label>
          <input
            type="text"
            value={tradeline.creditor_name || ''}
            onChange={(e) => handleFieldUpdate('creditor_name', e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Account Number</label>
          <input
            type="text"
            value={tradeline.account_number || ''}
            onChange={(e) => handleFieldUpdate('account_number', e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Balance</label>
          <input
            type="text"
            value={tradeline.account_balance || ''}
            onChange={(e) => handleFieldUpdate('account_balance', e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Credit Limit</label>
          <input
            type="text"
            value={tradeline.credit_limit || ''}
            onChange={(e) => handleFieldUpdate('credit_limit', e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Account Status</label>
          <select
            value={tradeline.account_status || ''}
            onChange={(e) => handleFieldUpdate('account_status', e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">Select Status</option>
            <option value="Open">Open</option>
            <option value="Closed">Closed</option>
            <option value="Current">Current</option>
            <option value="Delinquent">Delinquent</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Account Type</label>
          <select
            value={tradeline.account_type || ''}
            onChange={(e) => handleFieldUpdate('account_type', e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">Select Type</option>
            <option value="Credit Card">Credit Card</option>
            <option value="Mortgage">Mortgage</option>
            <option value="Auto Loan">Auto Loan</option>
            <option value="Student Loan">Student Loan</option>
            <option value="Personal Loan">Personal Loan</option>
          </select>
        </div>
      </div>

      {/* Negative account toggle */}
      <div className="flex items-center mt-4">
        <input
          type="checkbox"
          checked={tradeline.is_negative || false}
          onChange={(e) => handleFieldUpdate('is_negative', e.target.checked)}
          className="mr-2"
        />
        <label className="text-sm">Mark as negative account</label>
      </div>

      {/* Delete button */}
      <div className="mt-4">
        <button
          onClick={handleDelete}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 text-sm"
        >
          Delete Tradeline
        </button>
      </div>
    </div>
  );
};