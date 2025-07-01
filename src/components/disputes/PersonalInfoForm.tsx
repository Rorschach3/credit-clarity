import { useState, useEffect } from "react";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Save } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

// Form schema with validation
const personalInfoSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  address: z.string().min(1, "Address is required"),
  city: z.string().min(1, "City is required"),
  state: z.string().min(1, "State is required"),
  zip: z.string().min(5, "Zip code is required"),
  phone: z.string().optional(),
  email: z.string().email("Please enter a valid email address"),
  ssnLastFour: z.string().length(4, "Please enter the last 4 digits of your SSN").regex(/^\d{4}$/, "Last 4 SSN digits must be numbers").optional(),
});

type PersonalInfoFormValues = z.infer<typeof personalInfoSchema>;

interface PersonalInfoFormProps {
  onComplete?: (info?: PersonalInfoFormValues) => void;
}

export function PersonalInfoForm({ onComplete }: PersonalInfoFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();

  const form = useForm<PersonalInfoFormValues>({
    resolver: zodResolver(personalInfoSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      address: "",
      city: "",
      state: "",
      zip: "",
      phone: "",
      email: user?.email || "",
      ssnLastFour: "",
    },
  });

  // Fetch existing personal info if available
  useEffect(() => {
    const fetchPersonalInfo = async () => {
      if (!user) return;

      try {
        const { data, error } = await supabase
          .from("profiles")
          .select("*")
          .eq("user_id", user.id)
          .single();

        if (error && error.code !== 'PGRST116') {
          console.error("Error fetching personal info:", error);
          return;
        }

        if (data) {
          // Populate form with existing data
          form.reset({
            firstName: data.first_name || "",
            lastName: data.last_name || "",
            address: data.address || "",
            city: data.city || "",
            state: data.state || "",
            zip: data.zip || "",
            phone: data.phone || "",
            email: data.email || user?.email || "",
            ssnLastFour: data.ssnlastfour || "",
          });
        }
      } catch (error) {
        console.error("Error in fetching personal info:", error);
      }
    };

    fetchPersonalInfo();
  }, [user, form]);

  const onSubmit = async (values: PersonalInfoFormValues) => {
    console.log("onSubmit called with values:", values);
    console.log("Current user:", user);
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in to save your personal information.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const personalInfo = {
        first_name: values.firstName,
        last_name: values.lastName,
        address: values.address,
        city: values.city,
        state: values.state,
        zip: values.zip,
        phone: values.phone,
        email: values.email,
        ssnlastfour: values.ssnLastFour,
        user_id: user.id,
        updated_at: new Date().toISOString()
      };

      const { error } = await supabase
        .from("profiles")
        .upsert(personalInfo, { 
          onConflict: 'user_id',
          ignoreDuplicates: false 
        });

      console.log("Supabase operation error:", error);

      if (error) {
        throw error;
      }

      toast({
        title: "Success",
        description: "Your personal information has been saved.",
      });

      if (onComplete) {
        onComplete(values);
      }
    } catch (error) {
      console.error("Error saving personal info:", error);
      toast({
        title: "Error",
        description: "There was a problem saving your information. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Personal Information</CardTitle>
        <CardDescription>
          This information will be included in your dispute letter. The credit bureaus require this to verify your identity.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="firstName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>First Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="John" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="lastName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Last Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="Doe" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email Address *</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="email@example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Address *</FormLabel>
                  <FormControl>
                    <Input placeholder="123 Main Street" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FormField
                control={form.control}
                name="city"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>City *</FormLabel>
                    <FormControl>
                      <Input placeholder="New York" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="state"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>State *</FormLabel>
                    <FormControl>
                      <Input placeholder="NY" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="zip"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>ZIP Code *</FormLabel>
                    <FormControl>
                      <Input placeholder="10001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone Number</FormLabel>
                    <FormControl>
                      <Input placeholder="(555) 555-5555" {...field} />
                    </FormControl>
                    <FormDescription>Optional, but recommended</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="ssnLastFour"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Last 4 Digits of SSN</FormLabel>
                    <FormControl>
                      <Input placeholder="1234" maxLength={4} {...field} />
                    </FormControl>
                    <FormDescription>Required by credit bureaus for verification</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Personal Information
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
