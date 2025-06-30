
import React, { useState, useEffect } from 'react';
import { supabase } from "@/integrations/supabase/client";

const AuditLog = () => {
  type AuditLogEntry = {
    id: string;
    admin_id: string | null;
    action: string | null;
    created_at: string | null;
  };
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const { data, error } = await supabase
          .from('admin_activity_logs')
          .select('id, admin_id, action, created_at');

        if (error) {
          console.error('Error fetching audit logs:', error);
        } else {
          if (data) {
            setLogs(data as AuditLogEntry[]);
          }
        }
      } catch (error) {
        console.error('Error fetching audit logs:', error);
      }
    };
    fetchLogs();
  }, []);

  return (
    <div>
      <h2>Audit Log</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Admin ID</th>
            <th>Action</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>{log.admin_id}</td>
              <td>{log.action}</td>
              <td>{log.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AuditLog;
