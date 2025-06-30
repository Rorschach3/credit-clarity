
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Edit3, Save, RotateCcw } from 'lucide-react';

interface LetterEditorProps {
  initialContent: string;
  bureau: string;
  onSave: (content: string) => void;
}

export function LetterEditor({ initialContent, bureau, onSave }: LetterEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [isEditing, setIsEditing] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleContentChange = (value: string) => {
    setContent(value);
    setHasChanges(value !== initialContent);
  };

  const handleSave = () => {
    onSave(content);
    setIsEditing(false);
    setHasChanges(false);
  };

  const handleReset = () => {
    setContent(initialContent);
    setHasChanges(false);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Edit3 className="h-4 w-4" />
              Letter Editor - {bureau}
            </CardTitle>
            <CardDescription>
              Customize your dispute letter content
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {hasChanges && <Badge variant="secondary">Unsaved Changes</Badge>}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? 'Preview' : 'Edit'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isEditing ? (
          <div className="space-y-4">
            <Textarea
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              className="min-h-[400px] font-mono text-sm"
              placeholder="Enter your dispute letter content..."
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleReset} disabled={!hasChanges}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Button onClick={handleSave} disabled={!hasChanges}>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>
        ) : (
          <div className="whitespace-pre-wrap font-mono text-sm p-4 bg-gray-50 rounded-md border min-h-[400px]">
            {content}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
