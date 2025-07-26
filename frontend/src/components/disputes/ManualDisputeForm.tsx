
import { useState } from "react";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { NegativeItem } from "@/types/document";

// Form schema with validation
const formSchema = z.object({
  creditorName: z.string().min(1, "Creditor name is required"),
  accountNumber: z.string().min(1, "Account number is required"),
  amount: z.string().min(1, "Amount is required"),
  dateOpened: z.string().optional(),
  accountType: z.string().optional(),
  reason: z.string().optional(),
  balance: z.string().optional(),
  monthlyPayment: z.string().optional(),
  bureaus: z.array(z.string()).min(1, "Select at least one bureau"),
});

type FormValues = z.infer<typeof formSchema>;

interface ManualDisputeFormProps {
  onItemCreated: (item: NegativeItem) => void;
}

export function ManualDisputeForm({ onItemCreated }: ManualDisputeFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      creditorName: "",
      accountNumber: "",
      amount: "",
      dateOpened: "",
      accountType: "",
      reason: "",
      balance: "",
      monthlyPayment: "",
      bureaus: ["Experian"],
    },
  });

  const onSubmit = (values: FormValues) => {
    setIsSubmitting(true);
    
    try {
      // Create a negative item object from form values
      const newItem: NegativeItem = {
        id: crypto.randomUUID(),
        creditorName: values.creditorName,
        accountNumber: values.accountNumber,
        amount: values.amount,
        dateReported: values.dateOpened || new Date().toISOString().split('T')[0],
        bureaus: values.bureaus as any,
        reason: values.reason || "Information is inaccurate",
        status: "Active",
        // Remove properties that aren't in the NegativeItem type
        // score and recommendedReason were removed
      };
      
      onItemCreated(newItem);
      form.reset();
    } catch (error) {
      console.error("Error creating manual dispute item:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Manual Dispute Entry</CardTitle>
        <CardDescription>
          Enter the details of the account you want to dispute
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="creditorName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Creditor Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Bank of America" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="accountNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Account Number *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., 123456xxxx or last 4 digits" {...field} />
                    </FormControl>
                    <FormDescription>
                      Partial account numbers are acceptable
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Amount *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., $1,500" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="dateOpened"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date Opened/Reported</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="accountType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Account Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select account type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="credit_card">Credit Card</SelectItem>
                        <SelectItem value="loan">Loan</SelectItem>
                        <SelectItem value="collection">Collection</SelectItem>
                        <SelectItem value="medical">Medical</SelectItem>
                        <SelectItem value="utility">Utility</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="balance"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current Balance</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., $500" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="monthlyPayment"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monthly Payment</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., $25" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reason for Dispute</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Explain why you're disputing this item (optional)" 
                      className="min-h-24"
                      {...field} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="bureaus"
              render={() => (
                <FormItem>
                  <FormLabel>Credit Bureaus to Dispute With *</FormLabel>
                  <div className="flex flex-wrap gap-2">
                    {["Experian", "TransUnion", "Equifax"].map((bureau) => (
                      <FormField
                        key={bureau}
                        control={form.control}
                        name="bureaus"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-1 space-y-0">
                            <input
                              type="checkbox"
                              id={bureau}
                              checked={field.value?.includes(bureau)}
                              onChange={(e) => {
                                const checked = e.target.checked;
                                if (checked) {
                                  field.onChange([...field.value, bureau]);
                                } else {
                                  field.onChange(
                                    field.value?.filter((value) => value !== bureau)
                                  );
                                }
                              }}
                              className="h-4 w-4 rounded border-gray-300"
                            />
                            <label
                              htmlFor={bureau}
                              className="text-sm font-medium mr-4"
                            >
                              {bureau}
                            </label>
                          </FormItem>
                        )}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Dispute Item"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
