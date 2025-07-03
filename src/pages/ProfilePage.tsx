
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import { toast } from 'sonner';
import MainLayout from "@/components/layout/MainLayout";

interface Profile {
  first_name: string;
  last_name: string;
  dob: string;
  last_four_of_ssn: string;
  address1: string;
  address2: string;
  city: string;
  state: string;
  zip: string;
  phone: string;
}

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile>({
    first_name: '',
    last_name: '',
    dob: '',
    last_four_of_ssn: '',
    address1: '',
    address2: '',
    city: '',
    state: '',
    zip: '',
    phone: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      fetchProfile();
    }
  }, [user]);

  const fetchProfile = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('first_name, last_name, address1, address2, city, state, zip, phone')
        .eq('user_id', user.id)
        .single();

      if (error && error.code !== 'PGRST116') {
        throw error;
      }

      if (data) {
        setProfile({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          dob: '',
          last_four_of_ssn: '',
          address1: data.address1 || '',
          address2: data.address2 || '',
          city: data.city || '',
          state: data.state || '',
          zip: data.zip?.toString() || '',
          phone: data.phone || ''
        });
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    // Validate required fields
    if (!profile.first_name || !profile.last_name) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Validate SSN last 4 digits
    if (profile.last_four_of_ssn && !/^\d{4}$/.test(profile.last_four_of_ssn)) {
      toast.error('Last 4 digits of SSN must be exactly 4 numbers');
      return;
    }

    // Validate zip code
    if (profile.zip && !/^\d{5}(-\d{4})?$/.test(profile.zip)) {
      toast.error('Please enter a valid zip code');
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase
        .from('profiles')
        .upsert({
          user_id: user.id,
          first_name: profile.first_name,
          last_name: profile.last_name,
          address1: profile.address1 || null,
          address2: profile.address2 || null,
          city: profile.city || null,
          state: profile.state || null,
          zip: profile.zip || null,
          phone: profile.phone || null,
          updated_at: new Date().toISOString()
        });

      if (error) throw error;

      toast.success('Profile updated successfully!');
    } catch (error: any) {
      console.error('Error updating profile:', error);
      toast.error('Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof Profile, value: string) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  return (
    <MainLayout>
      <div className="container mx-auto py-10 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>
              Update your personal information and preferences
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="firstName">First Name *</Label>
                  <Input
                    id="firstName"
                    value={profile.first_name}
                    onChange={(e) => handleInputChange('first_name', e.target.value)}
                    placeholder="Enter your first name"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="lastName">Last Name *</Label>
                  <Input
                    id="lastName"
                    value={profile.last_name}
                    onChange={(e) => handleInputChange('last_name', e.target.value)}
                    placeholder="Enter your last name"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="dob">Date of Birth</Label>
                  <Input
                    id="dob"
                    type="date"
                    value={profile.dob}
                    onChange={(e) => handleInputChange('dob', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="lastFourSSN">Last 4 digits of SSN</Label>
                  <Input
                    id="lastFourSSN"
                    value={profile.last_four_of_ssn}
                    onChange={(e) => handleInputChange('last_four_of_ssn', e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="1234"
                    maxLength={4}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="address1">Address Line 1</Label>
                <Input
                  id="address1"
                  value={profile.address1}
                  onChange={(e) => handleInputChange('address1', e.target.value)}
                  placeholder="123 Main Street"
                />
              </div>

              <div>
                <Label htmlFor="address2">Address Line 2</Label>
                <Input
                  id="address2"
                  value={profile.address2}
                  onChange={(e) => handleInputChange('address2', e.target.value)}
                  placeholder="Apt 4B, Suite 100, etc."
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="city">City</Label>
                  <Input
                    id="city"
                    value={profile.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    placeholder="New York"
                  />
                </div>
                <div>
                  <Label htmlFor="state">State</Label>
                  <Input
                    id="state"
                    value={profile.state}
                    onChange={(e) => handleInputChange('state', e.target.value.toUpperCase().slice(0, 2))}
                    placeholder="NY"
                    maxLength={2}
                  />
                </div>
                <div>
                  <Label htmlFor="zip">Zip Code</Label>
                  <Input
                    id="zip"
                    value={profile.zip}
                    onChange={(e) => handleInputChange('zip', e.target.value)}
                    placeholder="10001"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  value={profile.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="(555) 123-4567"
                />
              </div>

              <Button type="submit" disabled={isLoading} className="w-full">
                {isLoading ? 'Updating...' : 'Update Profile'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
