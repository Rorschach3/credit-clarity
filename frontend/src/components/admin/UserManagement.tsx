
import { useState } from 'react'
import { useToast } from "@/hooks/use-toast"
import { supabase } from "../../../supabase/client"
import { Users } from "../../../supabase/types/supabase"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, ShieldCheck, ShieldOff } from "lucide-react"

interface User {
  id: string
  email: string
  subscription_tier?: string
  active?: boolean
  is_admin?: boolean
  tfa_enabled?: boolean
  last_login?: string
}

interface UserManagementProps {
  isLoading: boolean
  users: User[]
  fetchUsers: () => Promise<void>
}

export function UserManagement({ isLoading, users, fetchUsers }: UserManagementProps) {
  const { toast } = useToast()
  const [processingUsers, setProcessingUsers] = useState<{[key: string]: boolean}>({})

  async function grantAdminAccess(userId: string) {
    try {
      setProcessingUsers(prev => ({ ...prev, [userId]: true }))
      
      // Check if user already has an entry in user_roles
      const { data: existingRole } = await supabase
        .from('user_roles')
        .select('*')
        .eq('user_id', userId)
        .eq('role', 'admin')
        .single()

      if (!existingRole) {
        // Add user to admin role
        // First check if 2FA is enabled
        const { data: securitySettings } = await supabase
          .from('user_security_settings')
          .select('tfa_enabled')
          .eq('user_id', userId)
          .single()

        if (!securitySettings?.tfa_enabled) {
          toast({
            title: "2FA Required",
            description: "Admin access requires two-factor authentication",
            variant: "destructive",
          })
          return
        }

        // Add user to admin role
        const { error } = await supabase
          .from('user_roles')
          .insert({
            user_id: userId,
            role: 'admin'
          } as Users)

        // Log admin access grant
        await supabase
          .from('audit_logs')
          .insert({
            user_id: userId,
            action: 'admin_access_granted',
            details: { granted_by: supabase.auth.user()?.id }
          })

        if (error) {
          console.error("Error granting admin access:", error)
          throw error
        }

        toast({
          title: "Success",
          description: "Admin access granted",
        })
      } else {
        toast({
          title: "Info",
          description: "User already has admin access",
        })
      }

      // Refresh users list
      fetchUsers()
    } catch (error: SupabaseError) {
      console.error("Error in grantAdminAccess:", error)
      toast({
        title: "Error",
        description: `Failed to grant admin access: ${error.message}`,
        variant: "destructive",
      })
    } finally {
      setProcessingUsers(prev => ({ ...prev, [userId]: false }))
    }
  }

  async function revokeAdminAccess(userId: string) {
    try {
      setProcessingUsers(prev => ({ ...prev, [userId]: true }))
      
      // Log admin access revocation
      await supabase
        .from('audit_logs')
        .insert({
          user_id: userId,
          action: 'admin_access_revoked',
          details: { revoked_by: supabase.auth.user()?.id }
        })

      const { error } = await supabase
        .from('user_roles')
        .delete()
        .eq('user_id', userId)
        .eq('role', 'admin')

      if (error) {
        console.error("Error revoking admin access:", error)
        throw error
      }

      toast({
        title: "Success",
        description: "Admin access revoked",
      })

      // Refresh users list
      fetchUsers()
    } catch (error: SupabaseError) {
      console.error("Error in revokeAdminAccess:", error)
      toast({
        title: "Error",
        description: `Failed to revoke admin access: ${error.message}`,
        variant: "destructive",
      })
    } finally {
      setProcessingUsers(prev => ({ ...prev, [userId]: false }))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Management</CardTitle>
        <CardDescription>Manage users and subscription status</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Subscription</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>2FA</TableHead>
                <TableHead>Admin</TableHead>
                <TableHead>Last Login</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">Loading users...</TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">No users found</TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.subscription_tier || 'None'}</TableCell>
                    <TableCell>
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </TableCell>
                    <TableCell>
                      {user.active ? (
                        <Badge className="bg-green-500 text-white">Active</Badge>
                      ) : (
                        <Badge variant="outline">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.tfa_enabled ? (
                        <Badge className="bg-green-500 text-white">Enabled</Badge>
                      ) : (
                        <Badge variant="outline">Disabled</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.is_admin ? (
                        <Badge className="bg-blue-500 text-white flex items-center gap-1">
                          <ShieldCheck className="h-3 w-3" /> Admin
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <ShieldOff className="h-3 w-3" /> Not Admin
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-4">
                        {user.is_admin ? (
                          <Button
                            onClick={() => revokeAdminAccess(user.id)}
                            size="sm"
                            variant="outline"
                            className="border-red-200 text-red-600 hover:bg-red-50"
                            disabled={processingUsers[user.id]}
                          >
                            {processingUsers[user.id] ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <ShieldOff className="h-4 w-4 mr-2" />
                            )}
                            Revoke Admin
                          </Button>
                        ) : (
                          <Button
                            onClick={() => grantAdminAccess(user.id)}
                            size="sm"
                            variant="outline"
                            disabled={processingUsers[user.id]}
                          >
                            {processingUsers[user.id] ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <ShieldCheck className="h-4 w-4 mr-2" />
                            )}
                            Grant Admin
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
