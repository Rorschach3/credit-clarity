import React, { useState, useEffect } from 'react';
import { supabase } from "../../../supabase/client";

const AuditLog = () => {
  type AuditLogEntry = {
    id: number;
    performed_by: string | null;
    operation: string | null;
    performed_at: string | null;
  };
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const { data, error } = await supabase
          .from('audit_history')
          .select('id, performed_by, operation, performed_at');

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
            <th>User</th>
            <th>Action</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>{log.performed_by}</td>
              <td>{log.operation}</td>
              <td>{log.performed_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AuditLog;