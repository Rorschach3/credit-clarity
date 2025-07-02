
import { useEffect, useState } from 'react';
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import useActivityMonitoring from "@/hooks/use-activity-monitoring";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Shield, Package, Mail } from "lucide-react"
import { DisputeManagement } from "@/components/admin/DisputeManagement"
import UserManagement from "@/components/admin/UserManagement"
import PostageManagement from "@/components/admin/PostageManagement"
import AuditLog from "@/components/admin/AuditLog"
import MainLayout from "@/components/layout/MainLayout";
import AdminRoute from "@/components/auth/AdminRoute";

interface User {
  id: string;
  email: string;
  subscription_tier?: string;
  active?: boolean;
  is_admin?: boolean;
}

interface Dispute {
  id: string;
  created_at: string;
  status: string;
  user_id: string;
}

export default function AdminPage() {
  const [disputes, setDisputes] = useState<Dispute[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('disputes');
  useActivityMonitoring(`Admin page tab changed to: ${activeTab}`);

  useEffect(() => {
    if (activeTab === 'disputes') {
      fetchDisputes()
    } else if (activeTab === 'users') {
      fetchUsers()
    }
  }, [activeTab]);

  async function fetchDisputes() {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('disputes')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) {
        console.error("Error fetching disputes:", error);
        toast({
          title: "Error",
          description: `Failed to fetch disputes: ${error.message}`,
          variant: "destructive",
        });
      } else {
        console.log("Disputes fetched:", data);
        setDisputes(data as Dispute[] || []);
      }
    } catch (e) {
      console.error("Exception in fetchDisputes:", e);
      toast({
        title: "Error",
        description: "An unexpected error occurred when fetching disputes",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function fetchUsers() {
    console.log("Fetching users...");
    setIsLoading(true);
    try {
      // Fetch users from user_subscriptions table instead
      const { data: subscriptionsData, error: subscriptionsError } = await supabase
        .from('user_subscriptions')
        .select('*');

      if (subscriptionsError) {
        console.error("Error fetching user subscriptions:", subscriptionsError);
        toast({
          title: "Error",
          description: `Failed to fetch users: ${subscriptionsError.message}`,
          variant: "destructive",
        });
        setUsers([]);
        return;
      }

      console.log("User subscriptions data:", subscriptionsData);
      
      // Convert subscriptions to user format
      const usersFromSubscriptions = subscriptionsData ? subscriptionsData.map((sub: any) => ({
        id: sub.user_id || '',
        email: sub.email || '',
        subscription_tier: sub.tier,
        active: sub.active,
      })) : [];

      // Fetch admin roles for these users
      if (usersFromSubscriptions.length > 0) {
        const { data: rolesData, error: rolesError } = await supabase
          .from('user_roles')
          .select('user_id, role');

        if (rolesError) {
          console.error("Error fetching roles:", rolesError);
        } else {
          console.log("Roles data:", rolesData);
          
          // Create a map of user_id to admin status
          const adminMap = new Map<string, boolean>();
          if (rolesData && Array.isArray(rolesData)) {
            rolesData.forEach((role: any) => {
              adminMap.set(role.user_id, true);
            });
          }

          // Update users with admin status
          const usersWithAdminStatus = usersFromSubscriptions.map((user: User) => ({
            ...user,
            is_admin: adminMap.has(user.id)
          }));

          setUsers(usersWithAdminStatus);
        }
      } else {
        setUsers(usersFromSubscriptions);
      }
    } catch (e) {
      console.error("Exception in fetchUsers:", e);
      toast({
        title: "Error",
        description: "An unexpected error occurred when fetching users",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <MainLayout>
      <AdminRoute>
        <div className="container mx-auto py-10">
          <div className="flex items-center gap-4 mb-6">
            <Shield className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold">Admin Portal</h1>
          </div>
          
          <Tabs defaultValue="disputes" className="mb-8" onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="disputes" className="flex items-center gap-2">
                <Package className="h-4 w-4" /> Disputes
              </TabsTrigger>
              <TabsTrigger value="users" className="flex items-center gap-2">
                <Mail className="h-4 w-4" /> Users & Subscriptions
              </TabsTrigger>
              <TabsTrigger value="postage" className="flex items-center gap-2">
                <Package className="h-4 w-4" /> Postage Management
              </TabsTrigger>
              <TabsTrigger value="audit" className="flex items-center gap-2">
                <Shield className="h-4 w-4" /> Audit Log
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="disputes">
              <DisputeManagement
                isLoading={isLoading} 
                disputes={disputes} 
                fetchDisputes={fetchDisputes}
              />
            </TabsContent>
            
            <TabsContent value="users">
              <UserManagement 
                isLoading={isLoading} 
                users={users} 
                fetchUsers={fetchUsers}
              />
            </TabsContent>
            
            <TabsContent value="postage">
              <PostageManagement />
            </TabsContent>
            
            <TabsContent value="audit">
              <AuditLog />
            </TabsContent>
          </Tabs>
        </div>
      </AdminRoute>
    </MainLayout>
  );
}
