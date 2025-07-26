
import { Tabs, TabsList, TabsContent, TabsTrigger } from "@/components/ui/tabs";
import { Upload, Plus } from "lucide-react";
import { ReactNode } from "react";

interface InputMethodTabsProps {
  entryMethod: 'scan' | 'manual';
  onMethodChange: (value: 'scan' | 'manual') => void;
  scanContent: ReactNode;
  manualContent: ReactNode;
}

export function InputMethodTabs({ 
  entryMethod, 
  onMethodChange, 
  scanContent, 
  manualContent 
}: InputMethodTabsProps) {
  return (
    <Tabs 
      defaultValue={entryMethod} 
      onValueChange={(value) => onMethodChange(value as 'scan' | 'manual')}
      className="w-full"
    >
      <TabsList className="grid grid-cols-2 w-full max-w-md mx-auto mb-6">
        <TabsTrigger value="scan" className="flex items-center gap-2">
          <Upload className="h-4 w-4" />
          Upload Credit Report
        </TabsTrigger>
        <TabsTrigger value="manual" className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Manual Entry
        </TabsTrigger>
      </TabsList>
      <TabsContent value="scan">
        {scanContent}
      </TabsContent>
      <TabsContent value="manual">
        {manualContent}
      </TabsContent>
    </Tabs>
  );
}
