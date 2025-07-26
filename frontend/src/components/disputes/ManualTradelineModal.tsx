import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ParsedTradelineSchema } from "@/utils/tradelineParser";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { useEffect } from "react";

const ManualTradelineSchema = ParsedTradelineSchema.omit({ id: true });

type ManualTradelineData = z.infer<typeof ManualTradelineSchema>;

interface ManualTradelineModalProps {
  onClose: () => void;
  onAdd: (tradeline: ParsedTradeline) => void;
}

export function ManualTradelineModal({ onClose, onAdd }: ManualTradelineModalProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ManualTradelineData>({
    resolver: zodResolver(ManualTradelineSchema),
    defaultValues: {
      creditorName: "",
      accountNumber: "",
      status: "",
      isNegative: true,
      negativeReason: "",
      balance: "0.00",
      dateOpened: null,
      accountCondition: "",
      creditLimit: null,
      monthlyPayment: null,
      creditBureau: null,
      rawText: "",
    },
  });

  const onSubmit = (data: ManualTradelineData) => {
    const newTradeline: ParsedTradeline = {
      ...data,
      id: crypto.randomUUID(),
    };
    onAdd(newTradeline);
    reset();
  };

  useEffect(() => {
    reset(); // clear form when modal mounts
  }, [reset]);

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Manual Tradeline</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label>Creditor Name</Label>
            <Input {...register("creditorName")} />
            {errors.creditorName && (
              <p className="text-sm text-red-500">{errors.creditorName.message}</p>
            )}
          </div>

          <div>
            <Label>Account Number</Label>
            <Input {...register("accountNumber")} />
            {errors.accountNumber && (
              <p className="text-sm text-red-500">{errors.accountNumber.message}</p>
            )}
          </div>

          <div>
            <Label>Status</Label>
            <Input {...register("status")} />
            {errors.status && (
              <p className="text-sm text-red-500">{errors.status.message}</p>
            )}
          </div>

          <div>
            <Label>Negative Reason (optional)</Label>
            <Input {...register("negativeReason")} />
          </div>

          <div>
            <Label>Balance</Label>
            <Input {...register("balance")} />
            {errors.balance && (
              <p className="text-sm text-red-500">{errors.balance.message}</p>
            )}
          </div>

          <div>
            <Label>Date Opened (MM/DD/YYYY or null)</Label>
            <Input {...register("dateOpened")} />
          </div>

          <div>
            <Label>Credit Bureau (optional)</Label>
            <Input {...register("creditBureau")} />
          </div>

          <div>
            <Label>Raw Text (optional)</Label>
            <Input {...register("rawText")} />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Add Tradeline</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
