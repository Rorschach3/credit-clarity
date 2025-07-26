// hooks/useUserDocumentsStatus.ts
import { useState, useEffect, useCallback } from "react";
import { supabase } from "../../supabase/client";
import type { Database } from "../../supabase/types/supabase";

export type DocumentType = "photo_id" | "ssn_card" | "utility_bill";

export interface DocumentStatus {
  photo_id: boolean;
  ssn_card: boolean;
  utility_bill: boolean;
}

// Pull in the exact row type from your generated Database:
type UserDocumentRow = Database["public"]["Tables"]["user_documents"]["Row"];
// Then pick only the column we need:
type UserDocumentTypeRow = Pick<UserDocumentRow, "document_type">;

export const useUserDocumentsStatus = (userId?: string) => {
  const [status, setStatus] = useState<DocumentStatus>({
    photo_id: false,
    ssn_card: false,
    utility_bill: false,
  });

  const fetchStatus = useCallback(async () => {
    if (!userId) return;

    // Use the two‐generic overload so TS knows both the table name and the row shape:
    const { data, error } = await supabase
      .from("user_documents")
      .select("document_type")
      .eq("user_id", userId);

    if (error) {
      console.error("Error fetching document status:", error);
      return;
    }

    // Reset & flag the document types the user has uploaded
    const updated: DocumentStatus = {
      photo_id: false,
      ssn_card: false,
      utility_bill: false,
    };

    data?.forEach(({ document_type }) => {
      if (
        document_type === "photo_id" ||
        document_type === "ssn_card" ||
        document_type === "utility_bill"
      ) {
        updated[document_type] = true;
      }
    });

    setStatus(updated);
  }, [userId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return { status, fetchStatus };
};
