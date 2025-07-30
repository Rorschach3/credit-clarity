
import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";

interface AdminRouteProps {
  children: React.ReactNode;
}

const AdminRoute = ({ children }: AdminRouteProps) => {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
  const [checkingRole, setCheckingRole] = useState(true);

  useEffect(() => {
    const checkAdminStatus = async () => {
      console.log("AdminRoute: checkAdminStatus initiated");
      if (!user) {
        console.log("AdminRoute: No user found, setting isAdmin to false");
        setIsAdmin(false);
        setCheckingRole(false);
        return;
      }
      console.log("AdminRoute: User found:", user);

      try {
        // Call the edge function to check admin status
        const { data, error } = await supabase.functions.invoke('check-admin-status', {
          body: { userId: user.id }
        });
        console.log("AdminRoute: Supabase function invoke result:", { data, error });

        if (error) {
          console.error("AdminRoute: Error checking admin status:", error);
          setIsAdmin(false);
        } else {
          setIsAdmin(data?.isAdmin || false);
        }
        console.log("AdminRoute: isAdmin state set to:", data?.isAdmin || false);
      } catch (error) {
        console.error("Admin check failed:", error);
        setIsAdmin(false);
      } finally {
        setCheckingRole(false);
      }
    };

    if (user) {
      checkAdminStatus();
    }
  }, [user]);

  if (checkingRole) {
    return <div className="flex items-center justify-center min-h-screen">Checking permissions...</div>;
  }

  if (!isAdmin) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default AdminRoute;
