<<<<<<< Updated upstream:src/pages/ProfilePage.tsx
"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { supabase } from "../../supabase/client";
import { Database } from "../../supabase/types/supabase";
import { z } from "zod";

type SupabaseProfile = Database['public']['Tables']['profiles']['Row'];

export default function ProfilePage() {
  const { user } = useAuth();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [ssn, setSSN] = useState("");
  const [address1, setAddress1] = useState("");
  const [address2, setAddress2] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [zip, setZip] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    if (!user?.id) return;

    const fetchProfile = async () => {
      setLoading(true);
      try {
        const { data, error } = await supabase
          .from("profiles")
          .select("first_name, last_name, dob, ssn, address1, address2, city, state, zip")
          .eq("id", user.id)
          .returns<SupabaseProfile[]>();

        if (error) throw error;

        if (data && data.length > 0) {
          const profile = data[0];
          setFirstName(profile.first_name ?? "");
          setLastName(profile.last_name ?? "");
          setDob(profile.dob ?? "");
          setSSN(profile.ssn ?? "");
          setAddress1(profile.address1 ?? "");
          setAddress2(profile.address2 ?? "");
          setCity(profile.city ?? "");
          setState(profile.state ?? "");
          setZip(profile.zip ?? "");
        } else {
          setFeedback("Profile not found. Please create a profile.");
        }
      } catch (error: unknown) {
        console.error("Error loading profile:", error);
        setFeedback("Failed to load profile.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!firstName.trim()) newErrors.firstName = "First name is required";
    if (!lastName.trim()) newErrors.lastName = "Last name is required";
    if (!dob.trim()) newErrors.dob = "Date of birth is required";
    if (!ssn.trim() || !/^\d{3}-?\d{2}-?\d{4}$/.test(ssn)) {
      newErrors.ssn = "Valid SSN format is required (e.g., XXX-XX-XXXX)";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  return (
    <div className="min-h-screen py-10 px-4 md:px-10">
      <Card className="max-w-3xl mx-auto space-y-6">
        <CardHeader>
          <CardTitle className="text-2xl">Profile</CardTitle>
          <CardDescription>View and edit your personal profile information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {feedback && <p className="text-red-600">{feedback}</p>}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="firstName">First Name</Label>
              <Input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              {errors.firstName && <p className="text-red-500 text-sm">{errors.firstName}</p>}
            </div>

            <div>
              <Label htmlFor="lastName">Last Name</Label>
              <Input id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} />
              {errors.lastName && <p className="text-red-500 text-sm">{errors.lastName}</p>}
            </div>
          </div>

          <div>
            <Label htmlFor="dob">Date of Birth</Label>
            <Input id="dob" value={dob} onChange={(e) => setDob(e.target.value)} type="date" />
            {errors.dob && <p className="text-red-500 text-sm">{errors.dob}</p>}
          </div>

          <div>
            <Label htmlFor="ssn">SSN</Label>
            <Input id="ssn" value={ssn} onChange={(e) => setSSN(e.target.value)} />
            {errors.ssn && <p className="text-red-500 text-sm">{errors.ssn}</p>}
          </div>

          <div>
            <Label htmlFor="address1">Address Line 1</Label>
            <Input id="address1" value={address1} onChange={(e) => setAddress1(e.target.value)} />
          </div>

          <div>
            <Label htmlFor="address2">Address Line 2</Label>
            <Input id="address2" value={address2} onChange={(e) => setAddress2(e.target.value)} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="city">City</Label>
              <Input id="city" value={city} onChange={(e) => setCity(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="state">State</Label>
              <Input id="state" value={state} onChange={(e) => setState(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="zip">ZIP Code</Label>
              <Input id="zip" value={zip} onChange={(e) => setZip(e.target.value)} />
            </div>
          </div>

          <Button onClick={() => validateForm() && alert("Form is valid!")}>
            Save Changes
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
=======
import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { usePersistentProfile } from "@/hooks/usePersistentProfile";
import { supabase } from "@/integrations/supabase/client";
import { toast } from 'sonner';
import { Camera } from 'lucide-react';
import { CurrentUserAvatar } from '@/components/current-user-avatar';
import { z } from 'zod';

import type { Database } from '../integrations/supabase/types';

type Profile = Database['public']['Tables']['profiles']['Row'];

export default function ProfilePage() {
  const { user } = useAuth();
  const { 
    profile: persistentProfile, 
    updateProfile, 
    loading: profileLoading,
    error: profileError 
  } = usePersistentProfile();
  
  const profileSchema = z.object({
    first_name: z.string().min(1, "First name is required"),
    last_name: z.string().min(1, "Last name is required"),
    address1: z.string().nullable().optional(),
    address2: z.string().nullable().optional(),
    city: z.string().nullable().optional(),
    state: z.string().nullable().optional(),
    zip_code: z.string().nullable().optional(),
    phone_number: z.string().nullable().optional(),
    last_four_of_ssn: z.string().nullable().optional(),
    dob: z.string().nullable().optional(),
  });

  const [profile, setProfile] = useState<Partial<Profile>>({
    first_name: '',
    last_name: '',
    address1: null,
    address2: null,
    city: null,
    state: null,
    zip_code: null,
    phone_number: null,
    last_four_of_ssn: null,
    dob: null
  });
  const [isLoading, setIsLoading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync persistent profile to local state
  useEffect(() => {
    if (persistentProfile) {
      setProfile({
        first_name: persistentProfile.first_name || '',
        last_name: persistentProfile.last_name || '',
        address1: persistentProfile.address1 || null,
        address2: persistentProfile.address2 || null,
        city: persistentProfile.city || null,
        state: persistentProfile.state || null,
        zip_code: persistentProfile.zip_code || null,
        phone_number: persistentProfile.phone_number || null,
        last_four_of_ssn: persistentProfile.last_four_of_ssn || null,
        dob: persistentProfile.dob || null
      });
      setAvatarUrl(persistentProfile.avatar_url || null);
    }
  }, [persistentProfile]);

  // Memoize fetchProfile with useCallback
  const fetchProfile = useCallback(async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('first_name, last_name, address1, address2, city, state, zip_code, phone_number, last_four_of_ssn, dob')
        .eq('user_id', user.id)
        .single();

      if (error && error.code !== 'PGRST116') {
        console.error('Error fetching profile:', error);
        throw error;
      }

      if (data) {
        setProfile({
          first_name: data.first_name ?? '',
          last_name: data.last_name ?? '',
          address1: data.address1 ?? null,
          address2: data.address2 ?? null,
          city: data.city ?? null,
          state: data.state ?? null,
          zip_code: data.zip_code ?? null,
          phone_number: data.phone_number ?? null,
          last_four_of_ssn: data.last_four_of_ssn ?? null,
          dob: data.dob ?? null
        });
      }
    } catch (error) {
      console.error('Error fetching profile:', error instanceof Error ? error.message : 'Unknown error');
      toast.error('Failed to load profile');
    } finally {
      setIsLoading(false);
    }
  }, [user]); // Include user in dependencies

  // Simplified useEffect with proper dependencies
  useEffect(() => {
    if (user) {
      fetchProfile();
    }
  }, [user, fetchProfile]); // Include both user and fetchProfile

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = profileSchema.safeParse(profile);
    if (!result.success) {
      toast("Validation failed", { description: result.error.errors[0].message});
      return;
    }
    // Proceed with saving profile to Supabase or your backend
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
    if (profile.zip_code && !/^\d{5}(-\d{4})?$/.test(profile.zip_code)) {
      toast.error('Please enter a valid zip code');
      return;
    }

    setIsLoading(true);
    try {
      // Use the persistent profile hook to update the profile
      await updateProfile({
        first_name: profile.first_name,
        last_name: profile.last_name,
        address1: profile.address1 || null,
        address2: profile.address2 || null,
        city: profile.city || null,
        state: profile.state || null,
        zip_code: profile.zip_code || null,
        phone_number: profile.phone_number || null,
        last_four_of_ssn: profile.last_four_of_ssn || null,
        dob: profile.dob || null,
        avatar_url: avatarUrl || null
      });

      // Success toast is handled by the hook
    } catch (error) {
      console.error('Error updating profile:', error);
      // Error toast is handled by the hook
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof Profile, value: string) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !user) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      return;
    }

    setUploadingAvatar(true);
    try {
      // Upload to Supabase storage
      const fileExt = file.name.split('.').pop();
      const fileName = `${user.id}-${Date.now()}.${fileExt}`;
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('avatars')
        .upload(fileName, file, { upsert: true });

      if (uploadError) throw uploadError;

      // Get public URL
      const { data: urlData } = supabase.storage
        .from('avatars')
        .getPublicUrl(uploadData.path);

      const newAvatarUrl = urlData.publicUrl;

      // Update profile with new avatar URL
      const { error: updateError } = await supabase
        .from('profiles')
        .update({ 
          avatar_url: newAvatarUrl,
          updated_at: new Date().toISOString() 
        })
        .eq('user_id', user.id);

      if (updateError) throw updateError;

      setAvatarUrl(newAvatarUrl);
      toast.success('Avatar updated successfully!');
    } catch (error) {
      console.error('Avatar upload error:', error);
      toast.error('Failed to update avatar');
    } finally {
      setUploadingAvatar(false);
    }
  };

  return (
      <div className="container mx-auto py-10 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>
              Update your personal information and preferences
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Avatar Section */}
            <div className="flex flex-col items-center mb-6 p-4 border rounded-lg">
              <div className="relative mb-4">
                {/* Custom larger avatar for profile page */}
                <div 
                  className="relative w-24 h-24 rounded-full overflow-hidden border-2 border-gray-200 bg-gray-100 cursor-pointer transition-all duration-200 hover:border-primary hover:shadow-md group"
                  onClick={() => fileInputRef.current?.click()}
                  role="button"
                  tabIndex={0}
                  aria-label="Upload profile picture"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      fileInputRef.current?.click();
                    }
                  }}
                >
                  {avatarUrl ? (
                    <img 
                      src={avatarUrl} 
                      alt="Profile avatar" 
                      className="w-full h-full object-cover group-hover:brightness-75 transition-all duration-200"
                    />
                  ) : (
                    <div className="w-full h-full bg-primary/10 flex items-center justify-center text-2xl font-semibold text-primary group-hover:bg-primary/20 transition-colors duration-200">
                      {profile.first_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                    </div>
                  )}
                  
                  {/* Camera overlay that appears on hover */}
                  <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                    <Camera className="h-6 w-6 text-white" />
                  </div>
                  
                  {/* Camera button overlay */}
                  <Button
                    type="button"
                    size="icon"
                    variant="default"
                    className="absolute -bottom-1 -right-1 rounded-full w-8 h-8 shadow-lg z-10"
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent double-clicking
                      fileInputRef.current?.click();
                    }}
                    disabled={uploadingAvatar}
                    aria-label="Change profile picture"
                  >
                    {uploadingAvatar ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    ) : (
                      <Camera className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarUpload}
                className="hidden"
              />
              
              <p className="text-sm text-muted-foreground text-center">
                Click anywhere on the avatar or camera icon to update your profile picture
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">First Name *</Label>
                <Input
                id="firstName"
                value={profile.first_name || ''}
                onChange={(e) => handleInputChange('first_name', e.target.value)}
                placeholder="Enter your first name"
                required
                />
              </div>
              <div>
                <Label htmlFor="lastName">Last Name *</Label>
                <Input
                id="lastName"
                value={profile.last_name || ''}
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
                value={profile.dob || ''}
                onChange={(e) => handleInputChange('dob', e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="lastFourSSN">Last 4 digits of SSN</Label>
                <Input
                id="lastFourSSN"
                value={profile.last_four_of_ssn || ''}
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
                value={profile.address1 || ''}
                onChange={(e) => handleInputChange('address1', e.target.value)}
                placeholder="123 Main Street"
              />
              </div>

              <div>
              <Label htmlFor="address2">Address Line 2</Label>
              <Input
                id="address2"
                value={profile.address2 || ''}
                onChange={(e) => handleInputChange('address2', e.target.value)}
                placeholder="Apt 4B, Suite 100, etc."
              />
              </div>

              <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                id="city"
                value={profile.city || ''}
                onChange={(e) => handleInputChange('city', e.target.value)}
                placeholder="New York"
                />
              </div>
              <div>
                <Label htmlFor="state">State</Label>
                <Input
                id="state"
                value={profile.state || ''}
                onChange={(e) => handleInputChange('state', e.target.value.toUpperCase().slice(0, 2))}
                placeholder="NY"
                maxLength={2}
                />
              </div>
              <div>
                <Label htmlFor="zip">Zip Code</Label>
                <Input
                id="zip"
                value={profile.zip_code || ''}
                onChange={(e) => handleInputChange('zip_code', e.target.value)}
                placeholder="10001"
                />
              </div>
              </div>

              <div>
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                value={profile.phone_number || ''}
                onChange={(e) => handleInputChange('phone_number', e.target.value)}
                placeholder="(555) 123-4567"
              />
              </div>

              <Button type="submit" disabled={isLoading || profileLoading} className="w-full">
              {isLoading || profileLoading ? 'Updating...' : 'Update Profile'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
  );
}
>>>>>>> Stashed changes:frontend/src/pages/ProfilePage.tsx
