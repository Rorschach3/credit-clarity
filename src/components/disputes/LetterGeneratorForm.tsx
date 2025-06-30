
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { FileText, Download, Mail } from 'lucide-react';

interface LetterGeneratorFormProps {
  selectedItems: any[];
  onGenerate: (options: any) => void;
}

export function LetterGeneratorForm({ selectedItems, onGenerate }: LetterGeneratorFormProps) {
  const [selectedBureaus, setSelectedBureaus] = useState<string[]>(['experian', 'transunion', 'equifax']);
  const [includePersonalStatement, setIncludePersonalStatement] = useState(false);
  const [personalStatement, setPersonalStatement] = useState('');
  const [letterTone, setLetterTone] = useState<'professional' | 'assertive'>('professional');

  const bureaus = [
    { id: 'experian', name: 'Experian', address: 'P.O. Box 4500, Allen, TX 75013' },
    { id: 'transunion', name: 'TransUnion', address: 'P.O. Box 2000, Chester, PA 19016' },
    { id: 'equifax', name: 'Equifax', address: 'P.O. Box 740256, Atlanta, GA 30374' }
  ];

  const handleBureauToggle = (bureauId: string) => {
    setSelectedBureaus(prev => 
      prev.includes(bureauId) 
        ? prev.filter(id => id !== bureauId)
        : [...prev, bureauId]
    );
  };

  const handleGenerate = () => {
    onGenerate({
      bureaus: selectedBureaus,
      includePersonalStatement,
      personalStatement,
      letterTone,
      selectedItems
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Generate Dispute Letters
        </CardTitle>
        <CardDescription>
          Configure your dispute letters for each credit bureau
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Bureau Selection */}
        <div>
          <Label className="text-base font-semibold">Select Credit Bureaus</Label>
          <p className="text-sm text-muted-foreground mb-3">
            Choose which bureaus to send dispute letters to
          </p>
          <div className="space-y-3">
            {bureaus.map((bureau) => (
              <div key={bureau.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                <Checkbox
                  id={bureau.id}
                  checked={selectedBureaus.includes(bureau.id)}
                  onCheckedChange={() => handleBureauToggle(bureau.id)}
                />
                <div className="flex-1">
                  <Label htmlFor={bureau.id} className="font-medium cursor-pointer">
                    {bureau.name}
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">{bureau.address}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        {/* Letter Customization */}
        <div>
          <Label className="text-base font-semibold">Letter Customization</Label>
          
          <div className="mt-4 space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="personal-statement"
                checked={includePersonalStatement}
                onCheckedChange={setIncludePersonalStatement}
              />
              <Label htmlFor="personal-statement">Include Personal Statement</Label>
            </div>

            {includePersonalStatement && (
              <div>
                <Label htmlFor="statement">Personal Statement</Label>
                <Textarea
                  id="statement"
                  placeholder="Add your personal explanation or additional context..."
                  value={personalStatement}
                  onChange={(e) => setPersonalStatement(e.target.value)}
                  className="mt-2"
                />
              </div>
            )}
          </div>
        </div>

        <Separator />

        {/* Generation Actions */}
        <div className="flex gap-3">
          <Button 
            onClick={handleGenerate}
            disabled={selectedBureaus.length === 0}
            className="flex-1"
          >
            <FileText className="h-4 w-4 mr-2" />
            Generate Letters ({selectedBureaus.length})
          </Button>
          
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          
          <Button variant="outline">
            <Mail className="h-4 w-4 mr-2" />
            Mail Service
          </Button>
        </div>

        {/* Summary */}
        <div className="bg-muted p-4 rounded-lg">
          <h4 className="font-medium mb-2">Letter Summary</h4>
          <ul className="text-sm space-y-1">
            <li>• {selectedItems.length} negative items to dispute</li>
            <li>• {selectedBureaus.length} bureau(s) selected</li>
            <li>• {letterTone === 'professional' ? 'Professional' : 'Assertive'} tone</li>
            {includePersonalStatement && <li>• Personal statement included</li>}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
