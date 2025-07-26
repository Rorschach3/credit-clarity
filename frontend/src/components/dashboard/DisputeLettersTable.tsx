
import { Eye, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DisputeItem {
  bureau: string;
  company: string;
  type: string;
  amount: string;
  status: string;
}

interface DisputeLettersTableProps {
  disputeItems: DisputeItem[];
}

export function DisputeLettersTable({ disputeItems }: DisputeLettersTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3 px-4">Bureau</th>
            <th className="text-left py-3 px-4">Company</th>
            <th className="text-left py-3 px-4">Type</th>
            <th className="text-left py-3 px-4">Amount</th>
            <th className="text-left py-3 px-4">Status</th>
            <th className="text-left py-3 px-4">Actions</th>
          </tr>
        </thead>
        <tbody>
          {disputeItems.map((item, i) => (
            <tr key={i} className="border-b">
              <td className="py-3 px-4">{item.bureau}</td>
              <td className="py-3 px-4">{item.company}</td>
              <td className="py-3 px-4">{item.type}</td>
              <td className="py-3 px-4">{item.amount}</td>
              <td className="py-3 px-4">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  item.status === "Removed" ? "bg-green-100 text-green-800" :
                  item.status === "Disputed" ? "bg-blue-100 text-blue-800" :
                  item.status === "Pending" ? "bg-yellow-100 text-yellow-800" :
                  "bg-gray-100 text-gray-800"
                }`}>
                  {item.status}
                </span>
              </td>
              <td className="py-3 px-4">
                <div className="flex space-x-2">
                  <Button variant="ghost" size="icon">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <Mail className="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
