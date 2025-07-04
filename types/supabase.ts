export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      disputes: {
        Row: {
          id: string;
          user_id: string;
          credit_report_id?: string;
          created_at: Date;
          status?: string;
          mailing_address?: string;
          modified_by?: string | null;
          modified_at?: Date | null;
          retention_date?: Date | null;
          email: string | null;
          lob_id?: string | null;
        };
        Insert: {
          id: string;
          user_id: string;
          credit_report_id?: string;
          created_at: Date;
          status?: string;
          mailing_address?: string;
          modified_by?: string | null;
          modified_at?: Date | null;
          retention_date?: Date | null;
          email: string | null;
          lob_id?: string | null;
        };
        Update: {
          id: string;
          user_id: string;
          credit_report_id?: string;
          created_at: Date;
          status?: string;
          mailing_address?: string;
          modified_by?: string | null;
          modified_at?: Date | null;
          retention_date?: Date | null;
          email: string | null;
          lob_id?: string | null;
        };
        Relationships: [];
      };
      credit_reports: {
        Row: {
          id: string;
          user_id: string;
          encrypted_content: string;
          encryption_key: string;
          report_date?: Date;
          expires_at?: Date;
        };
        Insert: {
          id: string;
          user_id: string;
          encrypted_content: string;
          encryption_key: string;
          report_date?: Date;
          expires_at?: Date;
        };
        Update: {
          id: string;
          user_id: string;
          encrypted_content: string;
          encryption_key: string;
          report_date?: Date;
          expires_at?: Date;
        };
        Relationships: [
          {
            foreignKeyName: "credit_reports_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
      profiles: {
        Row: {
          id: string;
          created_at: Date;
          phone_number?: string | null;
          address1?: string | null;
          last_four_of_ssn?: string | null;
          city?: string | null;
          state?: string | null;
          zip_code?: number | null;
          first_name?: string;
          last_name?: string;
          user_id: string;
          address2?: string | null;
          dob?: string | null;
        };
        Insert: {
          id: string;
          created_at: Date;
          phone_number?: string | null;
          address1?: string | null;
          last_four_of_ssn?: string | null;
          city?: string | null;
          state?: string | null;
          zip_code?: number | null;
          first_name?: string;
          last_name?: string;
          user_id: string;
          address2?: string | null;
          dob?: string | null;
        };
        Update: {
          id: string;
          created_at: Date;
          phone_number?: string | null;
          address1?: string | null;
          last_four_of_ssn?: string | null;
          city?: string | null;
          state?: string | null;
          zip?: number | null;
          first_name?: string;
          last_name?: string;
          phone?: string | null;
          user_id: string;
          address2?: string | null;
          dob?: Date | null;
          is_super_admin: boolean | false;
          role: string | 'user';
        };
        Relationships: [
          {
            foreignKeyName: "profiles_id_fkey";
            columns: ["id"];
            referencedRelation: "users";
            referencedColumns: ["id"];
          }
        ];
      };
      tradelines: {
        Row: {
          id: string;
          user_id: string;
          creditor_name: string;
          account_balance?: string | "$0";
          account_type?: string;
          account_status?: string;
          created_at: Date;
          dispute_count: number | "$0";
          credit_limit?: string | "$0";
          monthly_payment?: string | "$0";
          account_number: string;
          credit_bureau: string | null;
          date_opened: string;
          is_negative: boolean | false;
        };
        Insert: {
          id: string;
          user_id: string;
          creditor_name: string;
          account_balance?: string | "$0";
          account_type?: string;
          account_status?: string;
          created_at: Date;
          dispute_count: number | "$0";
          credit_limit?: string | "$0";
          monthly_payment?: string | "$0";
          account_number: string;
          credit_bureau: string | null;
          date_opened: string;
          is_negative: boolean | false;
        };
        Update: {
          id: string;
          user_id: string;
          creditor_name: string;
          account_balance?: string | "$0";
          account_type?: string;
          account_status?: string;
          created_at: Date;
          dispute_count: number | "$0";
          credit_limit?: string | "$0";
          monthly_payment?: string | "$0";
          account_number: string;
          credit_bureau: string | null;
          date_opened: string;
          is_negative: boolean | false;
        };
        Relationships: [
          {
            foreignKeyName: "tradelines_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
      user_documents: {
        Row: {
          id: string;
          user_id: string;
          created_at?: Date;
          document_type?: string;
          file_path?: string;
        };
        Insert: {
          id: string;
          user_id: string;
          created_at?: Date;
          document_type?: string;
          file_path?: string;
        };
        Update: {
          id: string;
          user_id: string;
          created_at?: Date;
          document_type?: string;
          file_path?: string;
        };
        Relationships: [
          {
            foreignKeyName: "user_documents_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
      credit_bureau: {
        Row: {
          id: string;
          created_at: Date;
          name?: string;
          address?: string;
          city?: string;
          state?: string;
          zip?: string;
          phone_number?: string | null;
        };
        Insert: {
          id: string;
          created_at: Date;
          name?: string;
          address?: string;
          city?: string;
          state?: string;
          zip?: string;
          phone_number?: string | null;
        };
        Update: {
          id: string;
          created_at: Date;
          name?: string;
          address?: string;
          city?: string;
          state?: string;
          zip?: string;
          phone_number?: string | null;
        };
        Relationships: [];
      };
      dispute_letter: {
        Row: {
          id: string;
          first_name?: string;
          last_name?: string;
          address?: string;
          city?: string;
          state?: string;
          zip?: string;
          email: string;
          tradelines?: string;
          created_on: Date;
          user_id: string;
          lob_id?: string;
          delivery_status?: string;
        };
        Insert: {
          id: string;
          first_name?: string;
          last_name?: string;
          address?: string;
          city?: string;
          state?: string;
          zip?: string;
          email: string;
          tradelines?: string;
          created_on: Date;
          user_id: string;
          lob_id?: string;
          delivery_status?: string;
        };
        Update: {
          id: string;
          first_name?: string;
          last_name?: string;
          address?: string;
          city?: string;
          state?: string;
          zip?: string;
          email: string;
          tradelines?: string;
          created_on: Date;
          user_id: string;
          lob_id?: string;
          delivery_status?: string;
        };
        Relationships: [
          {
            foreignKeyName: "dispute_letter_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };

      documents: {
        Row: {
          id: string;
          content?: string;
          metadata?: string;
          embedding?: string
          user_id: string;
        };
        Insert: {
          id: string;
          content?: string;
          metadata?: string;
          embedding?: string
          user_id: string;
        };
        Update: {
          id: string;
          content?: string;
          metadata?: string;
          embedding?: string
          user_id: string;
        };
        Relationships: [
          {
            foreignKeyName: "documents_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };

      user_roles: {
        Row: {
          user_id: string;
          role: string;
          email: string;
          assigned_at: Date;
        };
        Insert: {
          user_id: string;
          role: string;
          email: string;
          assigned_at: Date;
        };
        Update: {
          user_id: string;
          role: string;
          email: string;
          assigned_at: Date;
        };
        Relationships: [
          {
            foreignKeyName: "user_roles_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type DefaultSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const