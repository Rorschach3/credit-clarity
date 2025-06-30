
import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Download, Mail } from 'lucide-react';

interface DisputePacketBuilderProps {
  selectedItems: any[];
}

export function DisputePacketBuilder({ selectedItems }: DisputePacketBuilderProps) {
  const handleDownloadPacket = () => {
    // Generate and download the dispute packet
    console.log('Downloading dispute packet for items:', selectedItems);
  };

  const handleMailPacket = () => {
    // Mail the dispute packet
    console.log('Mailing dispute packet for items:', selectedItems);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Dispute Packet Builder
        </CardTitle>
        <CardDescription>
          Generate your complete dispute package with all necessary documents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button onClick={handleDownloadPacket} className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Download Packet
          </Button>
          <Button onClick={handleMailPacket} variant="outline" className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            Mail for Me
          </Button>
        </div>
        
        <div className="text-sm text-muted-foreground">
          <h4 className="font-semibold mb-2">Your packet will include:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Dispute letters for each bureau</li>
            <li>Supporting documentation</li>
            <li>Mailing instructions</li>
            <li>Response tracking forms</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
