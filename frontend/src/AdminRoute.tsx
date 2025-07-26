import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { supabase } from "../../supabase/client";
import { Spinner } from "@/components/ui/spinner";

interface AdminRouteProps {
  children: JSX.Element;
}

export function AdminRoute({ children }: AdminRouteProps) {
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAdmin = async () => {
      const { data: session } = await supabase.auth.getUser();
      const user = session?.user;

      if (!user) {
        setIsAdmin(false);
        return;
      }

      type UserRole = { role: string };

      const { data } = await (supabase
        .from("user_roles" as any)
        .select("role")
        .eq("user_id", user.id)) as unknown as { data: UserRole[] };

      const hasAdmin = data?.some((r) => r.role === "admin");
      setIsAdmin(!!hasAdmin);
    };

    checkAdmin();
  }, []);

  if (isAdmin === null) return <Spinner />;
  if (!isAdmin) return <Navigate to="/" replace />;

  return children;
}
