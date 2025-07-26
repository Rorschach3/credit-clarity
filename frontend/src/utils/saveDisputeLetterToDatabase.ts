import { supabase } from "../../supabase/client";
import { z } from "zod";

export const DisputeLetterSchema = z.object({
  user_id: z.string().uuid(),
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  address: z.string().min(1),
  city: z.string(),
  state: z.string(),
  zip: z.string().regex(/^\d{5}$/),
  email: z.string().email(),
  tradelines: z.array(z.object({
    creditorName: z.string(),
    accountNumber: z.string(),
    accountSatus: z.string(),
    })),
});

export type DisputeLetterPayload = z.infer<typeof DisputeLetterSchema>;

export async function saveDisputeLetterToDatabase(
  data: DisputeLetterPayload,
  options?: { lobId?: string; deliveryStatus?: string }
): Promise<string> {
  const validated = DisputeLetterSchema.safeParse(data);
  if (!validated.success) {
    console.error("Invalid dispute letter payload:", validated.error.format());
    throw new Error("Invalid data for dispute letter.");
  }

  // Format data to match the database schema
  const formattedData = {
    user_id: validated.data.user_id,
    credit_bureau: "unknown", // Required field
    letter_content: JSON.stringify(validated.data.tradelines), // Required field
    mailing_address: `${validated.data.address}, ${validated.data.city}, ${validated.data.state} ${validated.data.zip}`, // Required field
    tracking_number: options?.lobId ?? null, // Optional field
    status: options?.deliveryStatus ?? null, // Optional field
  };

  // INSERT + RETURN ID
  const { data: inserted, error } = await supabase
    .from("disputes")
    .insert(formattedData)
    .select("id")
    .single();

  if (error) {
    console.error("Failed to save dispute letter:", error);
    throw new Error("Failed to save dispute letter.");
  }

  const letterId = inserted.id;

  // Optional: update Lob info
  if (options?.lobId || options?.deliveryStatus) {
    const { error: updateError } = await supabase
      .from("disputes")
      .update({
        tracking_number: options.lobId ?? null,
        status: options.deliveryStatus ?? null,
      })
      .eq("id", letterId);

    if (updateError) {
      console.error("Failed to update delivery status:", updateError);
      throw new Error("Failed to update Lob tracking info.");
    }
  }

  return letterId;
}
