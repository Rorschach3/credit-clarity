import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface UserInfo {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

interface UserInfoFormProps {
  userInfo: UserInfo;
  onChange: (info: UserInfo) => void;
}

export const UserInfoForm: React.FC<UserInfoFormProps> = ({ userInfo, onChange }) => {
  const handleChange = (field: keyof UserInfo) => (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...userInfo, [field]: e.target.value });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <Label htmlFor="your-name">Your Name</Label>
        <Input id="your-name" value={userInfo.name} onChange={handleChange("name")} />
      </div>
      <div>
        <Label htmlFor="your-address">Address</Label>
        <Input id="your-address" value={userInfo.address} onChange={handleChange("address")} />
      </div>
      <div>
        <Label htmlFor="your-city">City</Label>
        <Input id="your-city" value={userInfo.city} onChange={handleChange("city")} />
      </div>
      <div>
        <Label htmlFor="your-state">State</Label>
        <Input id="your-state" value={userInfo.state} onChange={handleChange("state")} />
      </div>
      <div>
        <Label htmlFor="your-zip">Zip</Label>
        <Input id="your-zip" value={userInfo.zip} onChange={handleChange("zip")} />
      </div>
    </div>
  );
};
