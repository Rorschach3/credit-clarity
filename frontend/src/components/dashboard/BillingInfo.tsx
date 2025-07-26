
import { CreditCard, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { useState } from "react";
import { supabase } from "../../../supabase/client";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";

export function BillingInfo() {
  const [isManagingSubscription, setIsManagingSubscription] = useState(false);
  const { user } = useAuth();

  const handleManageSubscription = async () => {
    if (!user) {
      toast.error("Please log in to manage your subscription");
      return;
    }

    try {
      setIsManagingSubscription(true);
      const { data, error } = await supabase.functions.invoke('customer-portal');
      
      if (error) throw new Error(error.message);
      if (!data?.url) throw new Error("No portal URL returned");
      
      // Redirect to Stripe Customer Portal
      window.location.href = data.url;
    } catch (error) {
      console.error('Error creating customer portal session:', error);
      toast.error("Could not open subscription management. Please try again.");
    } finally {
      setIsManagingSubscription(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment Method</CardTitle>
        <CardDescription>
          Manage your subscription and payment methods
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center space-x-4 p-4 border rounded-lg mb-6">
          <div className="bg-gray-100 p-2 rounded">
            <CreditCard className="h-6 w-6 text-gray-600" />
          </div>
          <div>
            <p className="font-medium">Credit Card ending in 4242</p>
            <p className="text-sm text-gray-500">Expires 12/25</p>
          </div>
          <Button variant="outline" size="sm" className="ml-auto">
            Update
          </Button>
        </div>
        
        <div className="space-y-4">
          <div className="flex justify-between">
            <span className="text-gray-600">Current Plan</span>
            <span className="font-medium">Premium Monthly</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Price</span>
            <span className="font-medium">$39.99/month</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Next Billing Date</span>
            <span className="font-medium">May 15, 2025</span>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t flex flex-col gap-3">
          <Button 
            variant="default" 
            className="w-full"
            onClick={handleManageSubscription}
            disabled={isManagingSubscription}
          >
            <Settings className="mr-2 h-4 w-4" />
            {isManagingSubscription ? "Loading..." : "Manage Subscription"}
          </Button>
          <Button variant="outline" className="w-full">
            Cancel Subscription
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
