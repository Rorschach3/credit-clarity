export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      admin_activity_logs: {
        Row: {
          action: string
          admin_id: string
          created_at: string | null
          details: Json | null
          id: string
        }
        Insert: {
          action: string
          admin_id: string
          created_at?: string | null
          details?: Json | null
          id?: string
        }
        Update: {
          action?: string
          admin_id?: string
          created_at?: string | null
          details?: Json | null
          id?: string
        }
        Relationships: []
      }
      apps: {
        Row: {
          id: number
          name: string | null
        }
        Insert: {
          id?: number
          name?: string | null
        }
        Update: {
          id?: number
          name?: string | null
        }
        Relationships: []
      }
      audit_history: {
        Row: {
          created_at: string
          id: string
          new_values: Json | null
          old_values: Json | null
          operation: string
          performed_by: string | null
          record_id: string
          table_name: string
        }
        Insert: {
          created_at?: string
          id?: string
          new_values?: Json | null
          old_values?: Json | null
          operation: string
          performed_by?: string | null
          record_id: string
          table_name: string
        }
        Update: {
          created_at?: string
          id?: string
          new_values?: Json | null
          old_values?: Json | null
          operation?: string
          performed_by?: string | null
          record_id?: string
          table_name?: string
        }
        Relationships: []
      }
      credit_reports: {
        Row: {
          created_at: string
          encrypted_content: string | null
          encryption_key_id: string | null
          id: string
          report_date: string
          user_id: string
        }
        Insert: {
          created_at?: string
          encrypted_content?: string | null
          encryption_key_id?: string | null
          id?: string
          report_date?: string
          user_id: string
        }
        Update: {
          created_at?: string
          encrypted_content?: string | null
          encryption_key_id?: string | null
          id?: string
          report_date?: string
          user_id?: string
        }
        Relationships: []
      }
      credit_transactions: {
        Row: {
          amount: number
          created_at: string | null
          id: string
          letter_id: string | null
          type: string
          user_id: string
        }
        Insert: {
          amount: number
          created_at?: string | null
          id?: string
          letter_id?: string | null
          type: string
          user_id: string
        }
        Update: {
          amount?: number
          created_at?: string | null
          id?: string
          letter_id?: string | null
          type?: string
          user_id?: string
        }
        Relationships: []
      }
      dispute_letter: {
        Row: {
          address: string | null
          city: string | null
          created_on: string
          delivery_status: string | null
          email: string | null
          fist_name: string | null
          id: string
          last_name: string | null
          lob_id: string | null
          state: string | null
          tradelines: Json | null
          user_id: string
          zip: string | null
        }
        Insert: {
          address?: string | null
          city?: string | null
          created_on?: string
          delivery_status?: string | null
          email?: string | null
          fist_name?: string | null
          id?: string
          last_name?: string | null
          lob_id?: string | null
          state?: string | null
          tradelines?: Json | null
          user_id: string
          zip?: string | null
        }
        Update: {
          address?: string | null
          city?: string | null
          created_on?: string
          delivery_status?: string | null
          email?: string | null
          fist_name?: string | null
          id?: string
          last_name?: string | null
          lob_id?: string | null
          state?: string | null
          tradelines?: Json | null
          user_id?: string
          zip?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "dispute_letter_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "user_personal_info"
            referencedColumns: ["user_id"]
          },
        ]
      }
      dispute_log: {
        Row: {
          changed_at: string | null
          dispute_id: string | null
          id: string
          new_data: Json | null
          old_data: Json | null
          operation: string
          user_id: string | null
        }
        Insert: {
          changed_at?: string | null
          dispute_id?: string | null
          id?: string
          new_data?: Json | null
          old_data?: Json | null
          operation: string
          user_id?: string | null
        }
        Update: {
          changed_at?: string | null
          dispute_id?: string | null
          id?: string
          new_data?: Json | null
          old_data?: Json | null
          operation?: string
          user_id?: string | null
        }
        Relationships: []
      }
      disputes: {
        Row: {
          created_at: string | null
          credit_report_id: string
          email: string | null
          id: string
          lob_id: string | null
          mailing_address: string
          modified_at: string | null
          modified_by: string | null
          retention_date: string | null
          status: string
          user_id: string
        }
        Insert: {
          created_at?: string | null
          credit_report_id: string
          email?: string | null
          id?: string
          lob_id?: string | null
          mailing_address: string
          modified_at?: string | null
          modified_by?: string | null
          retention_date?: string | null
          status: string
          user_id: string
        }
        Update: {
          created_at?: string | null
          credit_report_id?: string
          email?: string | null
          id?: string
          lob_id?: string | null
          mailing_address?: string
          modified_at?: string | null
          modified_by?: string | null
          retention_date?: string | null
          status?: string
          user_id?: string
        }
        Relationships: []
      }
      encrypted_report_content: {
        Row: {
          content_id: string | null
          created_at: string
          id: number
          user_id: string | null
        }
        Insert: {
          content_id?: string | null
          created_at?: string
          id?: number
          user_id?: string | null
        }
        Update: {
          content_id?: string | null
          created_at?: string
          id?: number
          user_id?: string | null
        }
        Relationships: []
      }
      letters: {
        Row: {
          cost_cents: number
          created_at: string | null
          file_path: string
          id: string
          lob_id: string | null
          sent_at: string | null
          status: string
          to_address: string
          to_name: string
          user_id: string
        }
        Insert: {
          cost_cents?: number
          created_at?: string | null
          file_path: string
          id?: string
          lob_id?: string | null
          sent_at?: string | null
          status?: string
          to_address: string
          to_name: string
          user_id: string
        }
        Update: {
          cost_cents?: number
          created_at?: string | null
          file_path?: string
          id?: string
          lob_id?: string | null
          sent_at?: string | null
          status?: string
          to_address?: string
          to_name?: string
          user_id?: string
        }
        Relationships: []
      }
      mail_queue: {
        Row: {
          id: string
          last_update: string | null
          letter_id: string
          queue_status: string
          user_id: string
        }
        Insert: {
          id?: string
          last_update?: string | null
          letter_id: string
          queue_status?: string
          user_id: string
        }
        Update: {
          id?: string
          last_update?: string | null
          letter_id?: string
          queue_status?: string
          user_id?: string
        }
        Relationships: []
      }
      payments: {
        Row: {
          amount_cents: number
          created_at: string | null
          id: string
          status: string
          stripe_payment_id: string
          user_id: string
        }
        Insert: {
          amount_cents: number
          created_at?: string | null
          id?: string
          status: string
          stripe_payment_id: string
          user_id: string
        }
        Update: {
          amount_cents?: number
          created_at?: string | null
          id?: string
          status?: string
          stripe_payment_id?: string
          user_id?: string
        }
        Relationships: []
      }
      profiles: {
        Row: {
          address: string | null
          avatar_url: string | null
          city: string | null
          email: string | null
          first_name: string | null
          id: number
          last_name: string | null
          phone: string | null
          ssnlastfour: string | null
          state: string | null
          updated_at: string | null
          user_id: string
          username: string | null
          website: string | null
          zip: string | null
        }
        Insert: {
          address?: string | null
          avatar_url?: string | null
          city?: string | null
          email?: string | null
          first_name?: string | null
          id?: never
          last_name?: string | null
          phone?: string | null
          ssnlastfour?: string | null
          state?: string | null
          updated_at?: string | null
          user_id: string
          username?: string | null
          website?: string | null
          zip?: string | null
        }
        Update: {
          address?: string | null
          avatar_url?: string | null
          city?: string | null
          email?: string | null
          first_name?: string | null
          id?: never
          last_name?: string | null
          phone?: string | null
          ssnlastfour?: string | null
          state?: string | null
          updated_at?: string | null
          user_id?: string
          username?: string | null
          website?: string | null
          zip?: string | null
        }
        Relationships: []
      }
      subscription_plans: {
        Row: {
          credits_per_month: number
          id: string
          is_active: boolean | null
          name: string
          price_cents: number
          stripe_price_id: string | null
          user_id: string
        }
        Insert: {
          credits_per_month: number
          id?: string
          is_active?: boolean | null
          name: string
          price_cents: number
          stripe_price_id?: string | null
          user_id?: string
        }
        Update: {
          credits_per_month?: number
          id?: string
          is_active?: boolean | null
          name?: string
          price_cents?: number
          stripe_price_id?: string | null
          user_id?: string
        }
        Relationships: []
      }
      tradelines: {
        Row: {
          account_balance: string | null
          account_number: string | null
          account_status: string | null
          account_type: string | null
          created_at: string | null
          credit_bureau: string | null
          credit_limit: string | null
          creditor_name: string | null
          date_opened: string | null
          dispute_count: number | null
          id: string
          is_negative: boolean | null
          monthly_payment: string | null
          raw_text: string | null
          user_id: string | null
        }
        Insert: {
          account_balance?: string | null
          account_number?: string | null
          account_status?: string | null
          account_type?: string | null
          created_at?: string | null
          credit_bureau?: string | null
          credit_limit?: string | null
          creditor_name?: string | null
          date_opened?: string | null
          dispute_count?: number | null
          id?: string
          is_negative?: boolean | null
          monthly_payment?: string | null
          raw_text?: string | null
          user_id?: string | null
        }
        Update: {
          account_balance?: string | null
          account_number?: string | null
          account_status?: string | null
          account_type?: string | null
          created_at?: string | null
          credit_bureau?: string | null
          credit_limit?: string | null
          creditor_name?: string | null
          date_opened?: string | null
          dispute_count?: number | null
          id?: string
          is_negative?: boolean | null
          monthly_payment?: string | null
          raw_text?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      user_documents: {
        Row: {
          created_at: string | null
          document_type: string | null
          file_path: string | null
          id: number
          user_id: string
        }
        Insert: {
          created_at?: string | null
          document_type?: string | null
          file_path?: string | null
          id?: number
          user_id?: string
        }
        Update: {
          created_at?: string | null
          document_type?: string | null
          file_path?: string | null
          id?: number
          user_id?: string
        }
        Relationships: []
      }
      user_personal_info: {
        Row: {
          address: string | null
          city: string | null
          email: string
          first_Name: string | null
          last_Name: string | null
          phone: string | null
          ssn_last_four: string | null
          state: string | null
          updated_at: string | null
          user_id: string
          zip: string | null
        }
        Insert: {
          address?: string | null
          city?: string | null
          email: string
          first_Name?: string | null
          last_Name?: string | null
          phone?: string | null
          ssn_last_four?: string | null
          state?: string | null
          updated_at?: string | null
          user_id: string
          zip?: string | null
        }
        Update: {
          address?: string | null
          city?: string | null
          email?: string
          first_Name?: string | null
          last_Name?: string | null
          phone?: string | null
          ssn_last_four?: string | null
          state?: string | null
          updated_at?: string | null
          user_id?: string
          zip?: string | null
        }
        Relationships: []
      }
      user_roles: {
        Row: {
          assigned_at: string
          email: string
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          assigned_at?: string
          email: string
          id?: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          assigned_at?: string
          email?: string
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
      user_subscriptions: {
        Row: {
          ended_at: string | null
          id: string
          plan_id: string
          started_at: string | null
          status: string
          stripe_subscription_id: string | null
          user_id: string
        }
        Insert: {
          ended_at?: string | null
          id?: string
          plan_id: string
          started_at?: string | null
          status?: string
          stripe_subscription_id?: string | null
          user_id: string
        }
        Update: {
          ended_at?: string | null
          id?: string
          plan_id?: string
          started_at?: string | null
          status?: string
          stripe_subscription_id?: string | null
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      authorize: {
        Args: {
          requested_permission: Database["public"]["Enums"]["app_permission"]
        }
        Returns: boolean
      }
      binary_quantize: {
        Args: { "": string } | { "": unknown }
        Returns: unknown
      }
      custom_access_token_hook: {
        Args: { event: Json }
        Returns: Json
      }
      fetch_tradelines: {
        Args: Record<PropertyKey, never>
        Returns: undefined
      }
      halfvec_avg: {
        Args: { "": number[] }
        Returns: unknown
      }
      halfvec_out: {
        Args: { "": unknown }
        Returns: unknown
      }
      halfvec_send: {
        Args: { "": unknown }
        Returns: string
      }
      halfvec_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
      has_role: {
        Args: {
          _user_id: string
          _role: Database["public"]["Enums"]["app_role"]
        }
        Returns: boolean
      }
      hnsw_bit_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnsw_halfvec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnsw_sparsevec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnswhandler: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflat_bit_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflat_halfvec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflathandler: {
        Args: { "": unknown }
        Returns: unknown
      }
      l2_norm: {
        Args: { "": unknown } | { "": unknown }
        Returns: number
      }
      l2_normalize: {
        Args: { "": string } | { "": unknown } | { "": unknown }
        Returns: unknown
      }
      match_documents: {
        Args:
          | Record<PropertyKey, never>
          | { query_embedding: string; match_count?: number; filter?: Json }
        Returns: undefined
      }
      sparsevec_out: {
        Args: { "": unknown }
        Returns: unknown
      }
      sparsevec_send: {
        Args: { "": unknown }
        Returns: string
      }
      sparsevec_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
      update_user_profile_timestamp: {
        Args: Record<PropertyKey, never>
        Returns: undefined
      }
      vector_avg: {
        Args: { "": number[] }
        Returns: string
      }
      vector_dims: {
        Args: { "": string } | { "": unknown }
        Returns: number
      }
      vector_norm: {
        Args: { "": string }
        Returns: number
      }
      vector_out: {
        Args: { "": string }
        Returns: unknown
      }
      vector_send: {
        Args: { "": string }
        Returns: string
      }
      vector_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
    }
    Enums: {
      app_permission: "channels.delete" | "messages.delete"
      app_role: "admin" | "moderator" | "user"
      bureau: "equifax" | "transunion" | "experian" | "'" | "null"
      tradeline_status:
        | "open"
        | "closed"
        | "in_collection"
        | "charged_off"
        | "disputed"
        | "late"
        | "collections"
        | "paid-closed"
        | "current-account"
        | "never-late"
        | "null"
      tradeline_type:
        | "credit_card"
        | "loan"
        | "mortgage"
        | "auto_loan"
        | "student_loan"
        | "collection"
        | "null"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

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
    Enums: {
      app_permission: ["channels.delete", "messages.delete"],
      app_role: ["admin", "moderator", "user"],
      bureau: ["equifax", "transunion", "experian", "'", "null"],
      tradeline_status: [
        "open",
        "closed",
        "in_collection",
        "charged_off",
        "disputed",
        "late",
        "collections",
        "paid-closed",
        "current-account",
        "never-late",
        "null",
      ],
      tradeline_type: [
        "credit_card",
        "loan",
        "mortgage",
        "auto_loan",
        "student_loan",
        "collection",
        "null",
      ],
    },
  },
} as const
