import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent } from "@/components/ui/card";
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
    refreshProfile,
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

  // Profile data comes from usePersistentProfile hook — no separate fetch needed

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
      // Refresh to ensure UI reflects saved data
      await refreshProfile();
    } catch (error) {
      console.error('Error updating profile:', error);
      // Error toast handled by hook — re-throw ensures finally still runs
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

      // Update via hook so cache is cleared and state stays in sync
      await updateProfile({ avatar_url: newAvatarUrl });

      // Immediately reflect in local avatar state
      setAvatarUrl(newAvatarUrl);
    } catch (error) {
      console.error('Avatar upload error:', error);
      toast.error('Failed to update avatar');
    } finally {
      setUploadingAvatar(false);
    }
  };

  return (
    <div className="has-navbar container mx-auto py-10 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Profile <span className="text-gold-gradient">Settings</span></h1>
        <p className="text-sm text-muted-foreground mt-1">
          Your name, address, and SSN last 4 are required to generate dispute letters.
        </p>
      </div>

      <Card className="card-midnight">
        <CardContent className="pt-6">
          {/* Avatar Section */}
          <div
            className="flex flex-col items-center mb-6 p-4 rounded-lg border"
            style={{ borderColor: '#1E2D47', background: 'rgba(26,35,64,0.4)' }}
          >
            <div className="relative mb-3">
              <div
                className="relative w-24 h-24 rounded-full overflow-hidden border-2 cursor-pointer transition-all duration-200 group"
                style={{ borderColor: '#1E2D47' }}
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
                  <div className="w-full h-full flex items-center justify-center text-2xl font-semibold text-[#D4A853]"
                    style={{ background: 'rgba(212,168,83,0.1)' }}>
                    {profile.first_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                  </div>
                )}
                <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                  <Camera className="h-6 w-6 text-white" />
                </div>
                <Button
                  type="button"
                  size="icon"
                  variant="default"
                  className="absolute -bottom-1 -right-1 rounded-full w-8 h-8 shadow-lg z-10 btn-gold"
                  onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                  disabled={uploadingAvatar}
                  aria-label="Change profile picture"
                >
                  {uploadingAvatar
                    ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    : <Camera className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleAvatarUpload} className="hidden" />
            <p className="text-xs text-muted-foreground text-center">Click avatar to update photo</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">First Name <span className="text-red-400">*</span></Label>
                <Input
                  id="firstName"
                  value={profile.first_name || ''}
                  onChange={(e) => handleInputChange('first_name', e.target.value)}
                  placeholder="Jane"
                  required
                />
              </div>
              <div>
                <Label htmlFor="lastName">Last Name <span className="text-red-400">*</span></Label>
                <Input
                  id="lastName"
                  value={profile.last_name || ''}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  placeholder="Smith"
                  required
                />
              </div>
            </div>

            {/* DOB + SSN */}
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
                <Label htmlFor="lastFourSSN">
                  Last 4 of SSN <span className="text-red-400">*</span>
                  <span className="ml-1 text-xs text-muted-foreground">(required for disputes)</span>
                </Label>
                <Input
                  id="lastFourSSN"
                  value={profile.last_four_of_ssn || ''}
                  onChange={(e) => handleInputChange('last_four_of_ssn', e.target.value.replace(/\D/g, '').slice(0, 4))}
                  placeholder="1234"
                  maxLength={4}
                  inputMode="numeric"
                />
              </div>
            </div>

            {/* Address */}
            <div>
              <Label htmlFor="address1">Address Line 1 <span className="text-red-400">*</span></Label>
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
                placeholder="Apt 4B (optional)"
              />
            </div>

            {/* City / State / Zip */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City <span className="text-red-400">*</span></Label>
                <Input
                  id="city"
                  value={profile.city || ''}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  placeholder="New York"
                />
              </div>
              <div>
                <Label htmlFor="state">State <span className="text-red-400">*</span></Label>
                <Input
                  id="state"
                  value={profile.state || ''}
                  onChange={(e) => handleInputChange('state', e.target.value.toUpperCase().slice(0, 2))}
                  placeholder="NY"
                  maxLength={2}
                />
              </div>
              <div>
                <Label htmlFor="zip">Zip Code <span className="text-red-400">*</span></Label>
                <Input
                  id="zip"
                  value={profile.zip_code || ''}
                  onChange={(e) => handleInputChange('zip_code', e.target.value)}
                  placeholder="10001"
                  inputMode="numeric"
                />
              </div>
            </div>

            {/* Phone */}
            <div>
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                value={profile.phone_number || ''}
                onChange={(e) => handleInputChange('phone_number', e.target.value)}
                placeholder="(555) 123-4567"
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading || profileLoading}
              className="btn-gold w-full rounded-md"
            >
              {isLoading || profileLoading ? 'Saving...' : 'Save Profile'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}