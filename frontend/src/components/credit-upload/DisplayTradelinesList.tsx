import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface DisplayTradelinesListProps {
  tradelines: ParsedTradeline[];
}

export const DisplayTradelinesList = ({ tradelines }: DisplayTradelinesListProps) => {
  if (tradelines.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Extracted Tradelines</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">No tradelines found.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Extracted Tradelines ({tradelines.length})</CardTitle>
        <p className="text-sm text-muted-foreground">
          These tradelines have been extracted from your credit report and saved to your account.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {tradelines.map((tradeline, index) => (
          <Card key={tradeline.id || index} className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Creditor Info */}
                <div>
                  <h4 className="font-semibold text-sm text-gray-600 uppercase tracking-wide">
                    Creditor
                  </h4>
                  <p className="font-medium">{tradeline.creditor_name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {tradeline.credit_bureau || 'Unknown'}
                    </Badge>
                    {tradeline.is_negative && (
                      <Badge variant="destructive" className="text-xs">
                        Negative
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Account Details */}
                <div>
                  <h4 className="font-semibold text-sm text-gray-600 uppercase tracking-wide">
                    Account
                  </h4>
                  <p className="text-sm">
                    <span className="font-medium">Type:</span> {tradeline.account_type}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Status:</span> {tradeline.account_status}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Number:</span> {tradeline.account_number}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Opened:</span> {tradeline.date_opened || 'Unknown'}
                  </p>
                </div>

                {/* Financial Info */}
                <div>
                  <h4 className="font-semibold text-sm text-gray-600 uppercase tracking-wide">
                    Balances
                  </h4>
                  <p className="text-sm">
                    <span className="font-medium">Balance:</span> {tradeline.account_balance || '$0'}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Credit Limit:</span> {tradeline.credit_limit || 'N/A'}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Monthly Payment:</span> {tradeline.monthly_payment || '$0'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </CardContent>
    </Card>
  );
};