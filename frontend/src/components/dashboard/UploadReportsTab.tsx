"use client";

import { FileUploader } from "./FileUploader";
import { UploadTips } from "./UploadTips";

interface UploadReportsTabProps {
  onBackToOverview: () => void;
}

export const UploadReportsTab = ({ onBackToOverview }: UploadReportsTabProps) => {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
      <div className="lg:col-span-2">
        <FileUploader />
      </div>
      <div>
        <UploadTips onBackToOverview={onBackToOverview} />
      </div>
    </section>
  );
};
