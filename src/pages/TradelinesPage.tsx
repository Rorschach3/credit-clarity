
import MainLayout from "@/components/layout/MainLayout";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Database } from "@/integrations/supabase/types";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

// Define Tradeline type from Supabase schema
type Tradeline = Database["public"]["Tables"]["tradelines"]["Row"];

const NegativeTradelinesPage = () => {
  const [accounts, setAccounts] = useState<Tradeline[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();
  const [editingAccount, setEditingAccount] = useState<Tradeline | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTradelines, setSelectedTradelines] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    const fetchNegativeTradelines = async () => {
      if (!user) return;
      setIsLoading(true);
      setError(null);
      try {
        const { data, error } = await supabase
          .from("tradelines")
          .select("*")
          .eq("user_id", user.id)
          .eq("is_negative", true);

        if (error) throw error;
        if (data) setAccounts(data);
      } catch (error: unknown) {
        console.error("Error fetching negative tradelines:", error);
        setError(error instanceof Error ? error.message : "Failed to load negative tradelines.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchNegativeTradelines();
  }, [user]);

  const handleSaveEdit = async (updatedTradeline: Tradeline) => {
    try {
      const { error } = await supabase
        .from("tradelines")
        .update(updatedTradeline)
        .eq("id", updatedTradeline.id);

      if (error) {
        console.error("Error updating tradeline:", error);
        setError(error.message || "Failed to update tradeline.");
      } else {
        setAccounts(accounts.map((acc) => (acc.id === updatedTradeline.id ? updatedTradeline : acc)));
        setEditingAccount(null);
      }
    } catch (editError: unknown) {
      console.error("Unexpected error updating tradeline:", editError);
      setError(editError instanceof Error ? editError.message : "Failed to update tradeline.");
    }
  };

  return (
   <MainLayout>
    <div className="container mx-auto px-4 py-8">
     <h1 className="text-2xl font-bold mb-4">Negative Tradelines</h1>
      {error && <p className="text-red-500 mb-2">Error: {error}</p>}
      {isLoading ? (
        <p>Loading negative tradelines...</p>
      ) : accounts.length === 0 ? (
        <p>No negative tradelines found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {accounts.map((account) => (
            <Card key={account.id} className="border-red-500 bg-[rgba(255,255,255,0.08)]">
              <CardHeader>
                <CardTitle>{account.creditor_name}</CardTitle>
                <Badge variant="destructive">Negative</Badge>
              </CardHeader>
              <CardContent>
                <input
                  type="checkbox"
                  checked={selectedTradelines.has(account.id)}
                  onChange={() => {
                    const newSelected = new Set(selectedTradelines);
                    if (newSelected.has(account.id)) {
                      newSelected.delete(account.id);
                    } else {
                      newSelected.add(account.id);
                    }
                    setSelectedTradelines(newSelected);
                  }}
                  className="mb-2"
                />
                <p><strong>Account Number:</strong> {account.account_number}</p>
                <p><strong>Status:</strong> {account.account_status}</p>
                <p><strong>Balance:</strong> {account.account_balance}</p>
                <p><strong>Date Opened:</strong> {account.date_opened}</p>
                <p><strong>Type:</strong> {account.account_type}</p>
              </CardContent>
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={async () => {
                    if (window.confirm("Are you sure you want to delete this tradeline?")) {
                      try {
                        const { error } = await supabase
                          .from("tradelines")
                          .delete()
                          .eq("id", account.id);
                        if (error) {
                          setError(error.message || "Failed to delete tradeline.");
                        } else {
                          setAccounts(accounts.filter((acc) => acc.id !== account.id));
                        }
                      } catch (deleteError: unknown) {
                        setError(deleteError instanceof Error ? deleteError.message : "Failed to delete tradeline.");
                      }
                    }
                  }}
                  className="bg-[rgba(255,255,255,0.3)] hover:bg-red-700 hover:text-white text-[rgba(255,255,255,0.8)] font-bold py-2 px-4 rounded"
                >
                  Delete
                </button>
                <button
                  onClick={() => setEditingAccount(account)}
                  className="hover:bg-blue-700 text-[rgba(255,255,255,0.8)] hover:text-white font-bold py-2 px-4 rounded"
                >
                  Edit
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
      <div className="mt-4">
        <button
          disabled={selectedTradelines.size === 0}
          onClick={() => {
            const selected = accounts.filter((acc) => selectedTradelines.has(acc.id));
            navigate("/dispute-generator", { state: { initialSelectedTradelines: selected } });
          }}
          className="bg-green-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
        >
          Add Selected to Dispute Letter
        </button>
      </div>

      {editingAccount && (
        <EditTradelineForm
          tradeline={editingAccount}
          onSave={handleSaveEdit}
          onCancel={() => setEditingAccount(null)}
        />
      )}
    </div>
   </MainLayout>
  );
};

export default NegativeTradelinesPage;

const EditTradelineForm = ({ tradeline, onSave, onCancel }: { tradeline: Tradeline; onSave: (updatedTradeline: Tradeline) => void; onCancel: () => void }) => {
  const [formData, setFormData] = useState<Tradeline>(tradeline);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <Dialog open={!!tradeline} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Tradeline</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="creditor_name" className="text-right">Creditor</Label>
            <Input id="creditor_name" name="creditor_name" value={formData.creditor_name || ''} onChange={handleChange} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="account_number" className="text-right">Account Number</Label>
            <Input id="account_number" name="account_number" value={formData.account_number || ''} onChange={handleChange} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="account_status" className="text-right">Status</Label>
            <Input id="account_status" name="account_status" value={formData.account_status || ''} onChange={handleChange} className="col-span-3" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
            <Button type="submit">Save changes</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
