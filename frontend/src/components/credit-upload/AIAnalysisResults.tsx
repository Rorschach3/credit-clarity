
import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

interface AIAnalysisResultsProps {
  keywords: string[];
  insights: string;
  extractedText: string;
}

export const AIAnalysisResults: React.FC<AIAnalysisResultsProps> = ({
  keywords,
  insights,
  extractedText
}) => {
  return (
    <Card>
      <CardContent className="pt-6">
        <Tabs defaultValue="keywords" className="w-full">
          <TabsList>
            <TabsTrigger value="keywords">Keywords</TabsTrigger>
            <TabsTrigger value="insights">AI Insights</TabsTrigger>
            <TabsTrigger value="text">Extracted Text</TabsTrigger>
          </TabsList>
          <TabsContent value="keywords" className="space-y-2">
            <h4 className="font-semibold">Extracted Keywords</h4>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword, i) => (
                <Badge key={i} variant="secondary">{keyword}</Badge>
              ))}
              {keywords.length === 0 && (
                <p className="text-muted-foreground text-sm">No keywords extracted yet.</p>
              )}
            </div>
          </TabsContent>
          <TabsContent value="insights" className="space-y-2">
            <h4 className="font-semibold">AI Analysis</h4>
            <div className="bg-muted p-4 rounded-md text-sm whitespace-pre-line">
              {insights || "No insights generated yet."}
            </div>
          </TabsContent>
          <TabsContent value="text" className="space-y-2">
            <h4 className="font-semibold">Raw Extracted Text</h4>
            <div className="bg-muted p-4 rounded-md text-xs max-h-60 overflow-y-auto">
              {extractedText ? extractedText.substring(0, 2000) + (extractedText.length > 2000 ? '...' : '') : "No text extracted yet."}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
