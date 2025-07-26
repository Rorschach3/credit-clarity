<<<<<<< Updated upstream:src/components/disputes/UserInfoForm.tsx
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const userInfoSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  address: z.string().min(5, { message: "Address is required." }),
  city: z.string().min(2, { message: "City is required." }),
  state: z.string().min(2, { message: "State is required." }),
  zip: z
    .string()
    .regex(/^\d{5}$/, { message: "Zip code must be exactly 5 digits." }),
});

export type UserInfo = z.infer<typeof userInfoSchema>;

interface UserInfoFormProps {
  userInfo: UserInfo;
  onChange: (update: Partial<UserInfo>) => void;
}

export function UserInfoForm({ userInfo, onChange }: UserInfoFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
  } = useForm<UserInfo>({
    resolver: zodResolver(userInfoSchema),
    defaultValues: userInfo,
    mode: "onBlur",
  });

  const watchedFields = watch();

  const onSubmit = (update: Partial<UserInfo>) => {
    onChange(update);
  };

  return (
    <form onBlur={() => onSubmit(watchedFields)} className="grid gap-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Full Name</Label>
          <Input id="name" {...register("name")} />
          {errors.name && (
            <p className="text-sm text-red-500 mt-1">{errors.name.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="address">Street Address</Label>
          <Input id="address" {...register("address")} />
          {errors.address && (
            <p className="text-sm text-red-500 mt-1">{errors.address.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Label htmlFor="city">City</Label>
          <Input id="city" {...register("city")} />
          {errors.city && (
            <p className="text-sm text-red-500 mt-1">{errors.city.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="state">State</Label>
          <Input id="state" {...register("state")} />
          {errors.state && (
            <p className="text-sm text-red-500 mt-1">{errors.state.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="zip">Zip Code</Label>
          <Input id="zip" {...register("zip")} />
          {errors.zip && (
            <p className="text-sm text-red-500 mt-1">{errors.zip.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          type="submit"
          onClick={handleSubmit(onSubmit)}
          className={cn(!isDirty && "opacity-50 pointer-events-none")}
        >
          Save Info
        </Button>
      </div>
    </form>
  );
}
=======
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
>>>>>>> Stashed changes:frontend/src/components/disputes/UserInfoForm.tsx
