import { supabase } from "../../supabase/client";

export async function uploadDisputePacket({
  file,
  userId,
  letterId,
}: {
  file: File;
  userId: string;
  letterId: string;
}): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const path = `packets/${userId}/${letterId}-${timestamp}.pdf`;

  const { error } = await supabase.storage
    .from("dispute_documents")
    .upload(path, file, {
      contentType: "application/pdf",
      upsert: true,
    });

  if (error) {
    console.error("Upload failed:", error);
    throw new Error("Failed to upload dispute packet.");
  }

  const { error: insertError } = await supabase.from("dispute_packets").insert({
    user_id: userId,
    letter_id: letterId,
    file_path: path,
    uploaded_at: new Date().toISOString(),
  });

  if (insertError) {
    console.error("DB insert failed:", insertError);
    throw new Error("Failed to log uploaded packet.");
  }

  return path;
}
