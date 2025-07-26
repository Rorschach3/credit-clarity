import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { ParsedTradeline } from "@/utils/tradelineParser";

const letterSchema = z.object({
  name: z.string().min(2, "Name is required"),
  address: z.string().min(5, "Address is required"),
  city: z.string(),
  state: z.string(),
  zip: z.string().regex(/^\d{5}$/, "Zip must be 5 digits"),
  body: z.string().min(10, "Letter body cannot be empty"),
});

export type LetterFormData = z.infer<typeof letterSchema>;

interface LetterEditorProps {
  userInfo: Omit<LetterFormData, "body">;
  selectedTradelines: ParsedTradeline[];
  letter: string;
  setLetter: (text: string) => void;
  setShowDocsSection?: (val: boolean) => void;
}

export function LetterEditor({
  userInfo,
  selectedTradelines,
  letter,
  setLetter,
  setShowDocsSection,
}: LetterEditorProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<LetterFormData>({
    resolver: zodResolver(letterSchema),
    defaultValues: { ...userInfo, body: letter },
  });

  const watched = watch();

  useEffect(() => {
    if (!selectedTradelines.length) return;

    const itemText = selectedTradelines
      .map((t, i) => `Item ${i + 1}: ${t.creditorName}\nAccount Number: ${t.accountNumber}\nReason: ${t.negativeReason || "Inaccurate or not mine"}`)
      .join("\n\n");

    const fullLetter = `
${watched.name}
${watched.address}
${watched.city}, ${watched.state} ${watched.zip}

Date: ${new Date().toLocaleDateString()}

To Whom It May Concern,

I am disputing the following items on my credit report:

${itemText}

Under the Fair Credit Reporting Act (FCRA), Section 611, I request a full investigation within 30 days. Please correct or remove any inaccurate information.

Sincerely,
${watched.name}
`.trim();

    setLetter(fullLetter);
  }, [watched.name, watched.address, watched.city, watched.state, watched.zip, selectedTradelines]);

  return (
    <form onSubmit={handleSubmit(() => {})} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Label htmlFor="name">Full Name</Label>
          <Input id="name" {...register("name")} />
          {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
        </div>
        <div>
          <Label htmlFor="address">Address</Label>
          <Input id="address" {...register("address")} />
          {errors.address && <p className="text-sm text-red-500">{errors.address.message}</p>}
        </div>
        <div>
          <Label htmlFor="zip">Zip Code</Label>
          <Input id="zip" {...register("zip")} />
          {errors.zip && <p className="text-sm text-red-500">{errors.zip.message}</p>}
        </div>
      </div>

      <div>
        <Label htmlFor="body">Generated Letter</Label>
        <Textarea
          id="body"
          rows={12}
          className="font-mono"
          readOnly
          value={letter}
        />
      </div>

      {setShowDocsSection && (
        <div className="flex justify-end">
          <Button type="button" onClick={() => setShowDocsSection(true)}>
            Continue to Upload Documents
          </Button>
        </div>
      )}
    </form>
  );
}
