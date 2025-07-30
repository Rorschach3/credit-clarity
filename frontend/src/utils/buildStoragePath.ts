/**
 * Builds a consistent file path for uploading documents to Supabase Storage.
 * @param userId - The user's unique ID
 * @param documentType - The type of document ("photo_id" | "ssn_card" | "utility_bill")
 * @param fileName - The original file name
 * @returns The storage path string
 */
export function buildStoragePath(
  userId: string,
  documentType: "photo_id" | "ssn_card" | "utility_bill",
  fileName: string
): string {
  return `${documentType}/user-${userId}/${fileName}`;
}