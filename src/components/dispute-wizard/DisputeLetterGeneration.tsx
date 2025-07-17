import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { FileText, Download, Edit3, Save, X, RefreshCw } from 'lucide-react';

interface GeneratedDisputeLetter {
  id: string;
  creditBureau: string;
  tradelines: any[];
  letterContent: string;
  disputeCount: number;
  isEdited?: boolean;
}

interface PacketProgress {
  step: string;
  progress: number;
  message: string;
}

interface DisputeLetterGenerationProps {
  isGenerating: boolean;
  generationProgress: PacketProgress;
  generatedLetters: GeneratedDisputeLetter[];
  editingLetter: string | null;
  editedContent: string;
  isReadyToGenerate: boolean;
  onGenerate: () => void;
  onEditLetter: (letterId: string, content: string) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onEditContentChange: (content: string) => void;
  onDownloadPDF: () => void;
  generatedPDF: Blob | null;
}

export const DisputeLetterGeneration: React.FC<DisputeLetterGenerationProps> = ({
  isGenerating,
  generationProgress,
  generatedLetters,
  editingLetter,
  editedContent,
  isReadyToGenerate,
  onGenerate,
  onEditLetter,
  onSaveEdit,
  onCancelEdit,
  onEditContentChange,
  onDownloadPDF,
  generatedPDF
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Generate Dispute Letters
          {generatedLetters.length > 0 && (
            <Badge variant="default" className="ml-auto">
              {generatedLetters.length} letter{generatedLetters.length !== 1 ? 's' : ''} generated
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        
        {/* Generation Progress */}
        {isGenerating && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{generationProgress.step}</span>
              <span className="text-sm text-muted-foreground">{generationProgress.progress}%</span>
            </div>
            <Progress value={generationProgress.progress} className="w-full" />
            <p className="text-sm text-muted-foreground">{generationProgress.message}</p>
          </div>
        )}

        {/* Generate Button */}
        {!isGenerating && generatedLetters.length === 0 && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Generate personalized dispute letters for your selected negative tradelines.
            </p>
            <Button
              onClick={onGenerate}
              disabled={!isReadyToGenerate}
              className="w-full"
              size="lg"
            >
              <FileText className="h-4 w-4 mr-2" />
              Generate Dispute Letters
            </Button>
          </div>
        )}

        {/* Generated Letters */}
        {generatedLetters.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Generated Letters</h3>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={onGenerate}
                  disabled={isGenerating}
                  size="sm"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Regenerate
                </Button>
                {generatedPDF && (
                  <Button
                    onClick={onDownloadPDF}
                    size="sm"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </Button>
                )}
              </div>
            </div>

            {generatedLetters.map((letter) => (
              <Card key={letter.id} className="border-l-4 border-l-blue-500">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">{letter.creditBureau}</CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {letter.disputeCount} item{letter.disputeCount !== 1 ? 's' : ''} to dispute
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {letter.isEdited && (
                        <Badge variant="secondary" className="text-xs">Edited</Badge>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onEditLetter(letter.id, letter.letterContent)}
                        disabled={isGenerating}
                      >
                        <Edit3 className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {editingLetter === letter.id ? (
                    <div className="space-y-3">
                      <Textarea
                        value={editedContent}
                        onChange={(e) => onEditContentChange(e.target.value)}
                        className="min-h-[300px] font-mono text-sm"
                        placeholder="Edit letter content..."
                      />
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={onCancelEdit}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Cancel
                        </Button>
                        <Button
                          size="sm"
                          onClick={onSaveEdit}
                        >
                          <Save className="h-4 w-4 mr-1" />
                          Save Changes
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                      <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed">
                        {letter.letterContent}
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};