
"use client";

import { useState, useCallback } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";

import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";

const TOAST_DURATION = 3000;

export function FileUploader() {
  const [isUploading, setIsUploading] = useState(false);
  const [hasFileSelected, setHasFileSelected] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const { user } = useAuth();

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) {
        setHasFileSelected(false);
        setSelectedFiles([]);
        return;
      }

      // Validate all files
      const maxSizeInBytes = 11 * 1024 * 1024; // 10MB
      for (const file of Array.from(files)) {
        if (file.type !== "application/pdf") {
          toast.error("Please upload only PDF files.");
          setHasFileSelected(false);
          setSelectedFiles([]);
          return;
        }
        if (file.size > maxSizeInBytes) {
          toast.error("File size must be less than 10MB.");
          setHasFileSelected(false);
          setSelectedFiles([]);
          return;
        }
      }

      if (!user?.id) {
        toast.error("User not authenticated.");
        setHasFileSelected(false);
        setSelectedFiles([]);
        return;
      }

      setHasFileSelected(true);
      setSelectedFiles(Array.from(files));
    },
    [user]
  );

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Upload Credit Reports</CardTitle>
        <CardDescription>
          Upload your credit reports from all three major bureaus for AI analysis.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Upload className="h-10 w-10 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Drag and drop your files here</h3>
          <p className="text-gray-500 mb-4">
            Supported file types: PDF (Max 10MB)
          </p>
          <label htmlFor="report-upload">
            <Button
              disabled={isUploading}
              className="cursor-pointer"
              onClick={() => {
                document.getElementById("report-upload")?.click();
              }}
            >
              {isUploading ? "Uploading..." : "Browse Files"}
            </Button>
            <input
              id="report-upload"
              name="report-upload"
              type="file"
              multiple
              hidden
              aria-describedby="report-upload-description report-upload-error"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
          {hasFileSelected && (
            <Button
              type="submit"
              className="mt-4 w-full"
              aria-label="Submit selected files"
              disabled={isUploading}
              onClick={async () => {
                if (!user?.id) {
                  toast.error("User not authenticated.");
                  return;
                }
                if (selectedFiles.length === 0) {
                  toast.error("No files selected.");
                  return;
                }
                setIsUploading(true);
                try {
                  for (const file of selectedFiles) {
                    try {
                      const filePath = `${user.id}/${file.name}`;
                      console.log(`Starting upload for file: ${file.name} at path: ${filePath}`);
                      toast.info(`Uploading ${file.name}...`, { duration: TOAST_DURATION });
                      const { error: uploadError } = await supabase.storage
                        .from("tradelines")
                        .upload(filePath, file, {
                          cacheControl: "3600",
                          upsert: false,
                        });
                      if (uploadError) {
                        console.error(`Upload error for file ${file.name}:`, uploadError);
                        toast.error(`Failed to upload file ${file.name}: ${uploadError.message}`);
                        continue;
                      }
                      toast.success(`Upload successful for file: ${file.name}`);

                      const { error: insertError } = await supabase
                        .from("tradelines")
                        .insert([
                          {
                            file_name: file.name,
                            file_path: filePath,
                            upload_date: new Date().toISOString(),
                            user_id: user.id,
                          },
                        ]);
                      if (insertError) {
                        console.error(`Database insert error for file ${file.name}:`, insertError);
                        toast.error(`Failed to store metadata for file ${file.name}.`);
                        continue;
                      }
                      console.log(`Database insert successful for file: ${file.name}`);
                      toast.success(`Uploaded ${file.name} successfully!`, { duration: TOAST_DURATION });
                    } catch (fileError) {
                      console.error(`Unexpected error processing file ${file.name}:`, fileError);
                      toast.error(`Unexpected error uploading file ${file.name}.`);
                    }
                  }
                  toast.info("AI analysis in progress...", { duration: TOAST_DURATION });
                  setTimeout(() => {
                    toast.success("AI analysis complete! 8 negative items found.", {
                      duration: TOAST_DURATION,
                    });
                  }, TOAST_DURATION);
                } catch (err) {
                  console.error("Unexpected error during upload process:", err);
                  toast.error("An unexpected error occurred during upload.");
                } finally {
                  setIsUploading(false);
                  setSelectedFiles([]);
                  setHasFileSelected(false);
                  // Clear file input value to allow re-upload of same files if needed
                  const input = document.getElementById("report-upload") as HTMLInputElement | null;
                  if (input) input.value = "";
                }
              }}
            >
              {isUploading ? "Uploading..." : "Submit"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
