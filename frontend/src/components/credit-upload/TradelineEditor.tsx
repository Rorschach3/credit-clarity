import React from 'react';
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelineEditorProps {
  tradeline: ParsedTradeline;
  index: number;
  onUpdate: (updates: Partial<ParsedTradeline>) => void;
  onDelete: () => void;
  isSaving?: boolean;
  hasError?: boolean;
}

export const TradelineEditor: React.FC<TradelineEditorProps> = ({
  tradeline,
  onUpdate,
  onDelete,
  isSaving = false,
  hasError = false
}) => {
  
  const handleFieldUpdate = (field: keyof ParsedTradeline, value: string | boolean) => {
    onUpdate({ [field]: value });
  };

  const handleDelete = () => {
    onDelete();
  };

  return (
    <div className="border rounded-lg p-4 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">{tradeline.creditor_name || 'Unknown Creditor'}</h3>
        <div className="flex items-center text-sm">
          {isSaving && (
            <span className="text-blue-600 flex items-center">
              <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full mr-1"></div>
              Saving...
            </span>
          )}
          {hasError && (
            <span className="text-red-600 flex items-center">
              <span className="mr-1">⚠️</span>
              Save failed
            </span>
          )}
          {!isSaving && !hasError && (
            <span className="text-green-600 flex items-center">
              <span className="mr-1">✓</span>
              Saved
            </span>
          )}
        </div>
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