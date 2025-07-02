
import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from 'sonner';
import { Eye, EyeOff } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import MainLayout from "@/components/layout/MainLayout";

interface UserRole {
  role: string;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Get the return URL from location state if it exists
  const returnTo = location.state?.returnTo || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw error;
      
      // Check if the user is an admin
      const { data: roleData, error: roleError } = await supabase
        .from("user_roles")
        .select('role')
        .eq("user_id", data.user?.id);

      if (roleError) {
        console.error("Error fetching user role:", roleError);
      }
      
      toast.success("Logged in successfully!");
      
      // Redirect based on user role
      if (roleData && Array.isArray(roleData) && roleData.length > 0 && roleData[0]?.role === 'admin') {
        navigate('/admin');
      } else {
        navigate(returnTo);
      }
    } catch (error: any) {
      setIsLoading(false);
      
      if (error instanceof Error && error.message === "Invalid login credentials") {
        toast.error("Invalid email or password. Please try again.");
      } else {
        toast.error("Login failed. Please try again later.");
      }
      console.error("Login error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
   <MainLayout>
    <div className="flex min-h-screen items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
     <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
       <CardTitle className="text-2xl font-bold text-center">Log in to your account</CardTitle>
       <CardDescription className="text-center">
        Enter your email and password to access your account
       </CardDescription>
      </CardHeader>
      <CardContent>
       <form onSubmit={handleSubmit}>
        <div className="space-y-2">
         <Label htmlFor="email">Email</Label>
         <Input 
          id="email" 
          type="email" 
          placeholder="john.doe@example.com" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required 
         />
        </div>
        <div className="space-y-2 mt-4">
         <div className="flex items-center justify-between">
          <Label htmlFor="password">Password</Label>
          <Link to="/forgot-password" className="text-sm text-brand-600 hover:text-brand-500">
           Forgot password?
          </Link>
         </div>
         <div className="relative">
          <Input 
           id="password" 
           type={showPassword ? "text" : "password"} 
           placeholder="••••••••" 
           value={password}
           onChange={(e) => setPassword(e.target.value)}
           required 
          />
          <button 
           type="button"
           className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
           onClick={() => setShowPassword(!showPassword)}
          >
           {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
         </div>
        </div>

        <Button disabled={isLoading} className="w-full mt-6" type="submit">
         {isLoading ? "Logging in..." : "Log in"}
        </Button>
       </form>
      </CardContent>
      <CardFooter className="flex justify-center">
       <div className="text-sm text-gray-500">
        Don't have an account?{" "}
        <Link to="/signup" className="font-medium text-brand-600 hover:text-brand-500">
         Sign up
        </Link>
       </div>
      </CardFooter>
     </Card>
    </div>
   </MainLayout>
  );
}
