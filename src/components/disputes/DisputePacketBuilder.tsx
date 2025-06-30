
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { FileText, Package, Calendar, MapPin } from 'lucide-react';

interface DisputePacketBuilderProps {
  selectedItems: any[];
  personalInfo: any;
}

export function DisputePacketBuilder({ selectedItems, personalInfo }: DisputePacketBuilderProps) {
  const [activeTab, setActiveTab] = useState('overview');

  const totalItems = selectedItems.length;
  const bureaus = ['Experian', 'TransUnion', 'Equifax'];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          <CardTitle>Dispute Packet Builder</CardTitle>
        </div>
        <CardDescription>
          Build comprehensive dispute packets for each credit bureau
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="letters">Letters</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="mailing">Mailing</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{totalItems}</div>
                <div className="text-sm text-muted-foreground">Items to Dispute</div>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-2xl font-bold text-green-600">{bureaus.length}</div>
                <div className="text-sm text-muted-foreground">Credit Bureaus</div>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-2xl font-bold text-purple-600">3</div>
                <div className="text-sm text-muted-foreground">Letters Ready</div>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <div className="text-2xl font-bold text-orange-600">85%</div>
                <div className="text-sm text-muted-foreground">Completion</div>
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <h4 className="font-semibold">Bureau Status</h4>
              {bureaus.map((bureau) => (
                <div key={bureau} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4" />
                    <span className="font-medium">{bureau}</span>
                  </div>
                  <Badge variant="default">Ready</Badge>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="letters" className="space-y-4">
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Dispute Letters</h3>
              <p className="text-muted-foreground mb-4">
                Professional dispute letters have been generated for each bureau
              </p>
              <Button>Preview Letters</Button>
            </div>
          </TabsContent>

          <TabsContent value="documents" className="space-y-4">
            <div className="text-center py-8">
              <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Supporting Documents</h3>
              <p className="text-muted-foreground mb-4">
                Additional documents to strengthen your disputes
              </p>
              <Button variant="outline">Manage Documents</Button>
            </div>
          </TabsContent>

          <TabsContent value="mailing" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                <h4 className="font-semibold">Mailing Information</h4>
              </div>
              
              <div className="grid gap-4">
                {bureaus.map((bureau) => (
                  <Card key={bureau}>
                    <CardContent className="pt-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h5 className="font-medium">{bureau}</h5>
                          <p className="text-sm text-muted-foreground mt-1">
                            Dispute Department<br />
                            P.O. Box 123456<br />
                            City, ST 12345
                          </p>
                        </div>
                        <Badge variant="outline">
                          <Calendar className="h-3 w-3 mr-1" />
                          Ready to Mail
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
