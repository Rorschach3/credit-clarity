import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import QRCode from 'qrcode.react';
import { supabase } from "../../../supabase/client";
import { toast } from 'sonner';

interface TotpSetupProps {
  userId: string;
}

const TotpSetup: React.FC<TotpSetupProps> = ({ userId }) => {
  const [totpSecret, setTotpSecret] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerateTotp = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/supabase/functions/setup-totp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession())?.data?.session?.access_token}`,
        },
        body: JSON.stringify({ userId }),
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setTotpSecret(data.totpSecret);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>TOTP Setup for User {userId}</CardTitle>
      </CardHeader>
      <CardContent>
        {totpSecret ? (
          <div>
            <Label>TOTP Secret:</Label>
            <Input type="text" value={totpSecret} readOnly />
            <Label>QR Code:</Label>
            <QRCode value={'otpauth://totp/CreditClarity:' + userId + '?secret=' + totpSecret + '&issuer=CreditClarity'} />
          </div>
        ) : (
          <Button disabled={isLoading} onClick={handleGenerateTotp}>
            {isLoading ? 'Generating...' : 'Generate TOTP Secret'}
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default TotpSetup;