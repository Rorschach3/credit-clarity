import { useAiAgent } from "@/hooks/useAiAgent";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

const ProjectAnalysis = () => {
  const { loading, response, error, analyzeProject } = useAiAgent();
  const [context, setContext] = useState("");

  const handleAnalyze = () => {
    analyzeProject(context || undefined);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>AI Project Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 rounded-md border px-3 py-2 text-sm"
            placeholder="Optional: add context about the project or focus area..."
            value={context}
            onChange={(e) => setContext(e.target.value)}
            disabled={loading}
          />
          <Button onClick={handleAnalyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Project"}
          </Button>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {response && (
          <pre className="max-h-[600px] overflow-auto whitespace-pre-wrap rounded-md bg-gray-50 p-4 text-sm">
            {response}
          </pre>
        )}
      </CardContent>
    </Card>
  );
};

export default ProjectAnalysis;
