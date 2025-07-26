import { z } from "zod";

const AuditOperation = z.enum(["INSERT", "UPDATE", "DELETE"]);

export const AuditHistorySchema = z.object({
  id: z.bigint(),                                        // bigint identity PK
  table_name: z.string(),                                // text NOT NULL
  record_id: z.string().uuid(),                          // uuid NOT NULL
  operation: AuditOperation.nullable(),                  // text NULL with CHECK(... IN [...])
  old_values: z.record(z.string(), z.unknown()).nullable(), // jsonb NULL
  new_values: z.record(z.string(), z.unknown()).nullable(), // jsonb NULL
  performed_by: z.string().uuid().nullable(),            // uuid NULL → FK to auth.users
  performed_at: z.date().nullable(),                     // timestamptz NULL DEFAULT now()
  user_id: z.string().uuid().nullable(),                 // uuid NULL DEFAULT gen_random_uuid()
});

export const CreditBureauSchema = z.object({
  id: z.bigint(),                       // bigint identity PK
  created_at: z.date(),                 // timestamptz NOT NULL DEFAULT now()
  name: z.string().nullable(),          // text NULL
  address: z.string().nullable(),       // text NULL
  city: z.string().nullable(),          // text NULL
  state: z.string().nullable(),         // text NULL
  zip: z.string().nullable(),           // text NULL
  phone_number: z.string().nullable(),  // text NULL
});

export type CreditBureau = z.infer<typeof CreditBureauSchema>;


// credit_reports
export const CreditReportsSchema = z.object({
  id:             z.string().uuid(),        // uuid PK
  user_id:        z.string().uuid(),        // uuid FK → auth.users
  encrypted_content: z.instanceof(Uint8Array), // bytea → Node Buffer or Uint8Array
  encryption_key_id: z.string(),            // text
  report_date:    z.date(),                 // timestamptz NOT NULL
  expires_at:     z.date(),                 // timestamptz NOT NULL
});
export type CreditReport = z.infer<typeof CreditReportsSchema>;

// dispute_letter
export const DisputeLetterSchema = z.object({
  first_name:     z.string().nullable(),    // text NULL DEFAULT
  last_name:      z.string().nullable(),    // text NULL DEFAULT
  address:        z.string().nullable(),    // text NULL DEFAULT
  city:           z.string().nullable(),    // text NULL DEFAULT
  state:          z.string().nullable(),    // text NULL DEFAULT
  zip:            z.string().nullable(),    // text NULL DEFAULT
  email:          z.string().nullable(),    // text NULL DEFAULT
  tradelines:     z.record(z.string(), z.unknown()).nullable(), // jsonb
  created_on:     z.date(),                 // date NOT NULL
  user_id:        z.string().uuid(),        // uuid FK → user_personal_info
  id:             z.string().uuid(),        // uuid PK
  lob_id:         z.string().nullable(),    // text NULL
  delivery_status: z.string().nullable(),   // text NULL
});
export type DisputeLetter = z.infer<typeof DisputeLetterSchema>;

// disputes
export const DisputeSchema = z.object({
  id:             z.string().uuid(),                       // uuid PK
  user_id:        z.string().uuid(),                       // uuid FK → auth.users
  credit_report_id: z.string(),                            // text
  created_at:     z.date().nullable(),                     // timestamptz NULL
  status:         z.enum(["pending", "under_review", "resolved"]), // text NOT NULL
  mailing_address: z.string(),                             // text NOT NULL
  modified_by:    z.string().uuid().nullable(),            // uuid FK → auth.users
  modified_at:    z.date(),                                // timestamptz NOT NULL
  retention_date: z.date().nullable(),                     // date NULL
  email:          z.string().nullable(),                   // text NULL
  lob_id:         z.string().nullable(),                   // text NULL
});
export type Dispute = z.infer<typeof DisputeSchema>;

// documents
export const DocumentsSchema = z.object({
  id:             z.number(),                              // bigserial PK
  content:        z.string().nullable(),                   // text NULL
  metadata:       z.record(z.string(), z.unknown()).nullable(), // jsonb
  embedding:      z.array(z.number()).nullable(),          // public.vector NULL
  user_id:        z.string().uuid(),                       // uuid NOT NULL
});
export type Document = z.infer<typeof DocumentsSchema>;

// profiles
export const ProfilesSchema = z.object({
  id:             z.string().uuid(),        // NOT NULL DEFAULT gen_random_uuid
  email:          z.string().nullable(),    // text NULL DEFAULT ''
  created_at:     z.date().nullable(),      // timestamptz NULL DEFAULT now()
  phone_number:   z.string().nullable(),    // text NULL DEFAULT ''
  address1:       z.string().nullable(),    // text NULL DEFAULT ''
  ssn:            z.string().nullable(),    // text NULL DEFAULT ''
  city:           z.string().nullable(),    // text NULL DEFAULT ''
  state:          z.string().nullable(),    // text NULL DEFAULT ''
  zip:            z.string().nullable(),    // text NULL DEFAULT ''
  first_name:     z.string().nullable(),    // text NULL DEFAULT ''
  last_name:      z.string().nullable(),    // text NULL DEFAULT ''
  phone:          z.string().nullable(),    // text NULL DEFAULT ''
  user_id:        z.string().uuid(),        // uuid PK/FK → auth.users
  address2:       z.string().nullable(),    // text NULL DEFAULT ''
  dob:            z.date().nullable(),      // date NULL
  is_super_admin: z.union([z.literal("False"), z.string()]).nullable(), // text 'False'
  role:           z.string(),               // text NOT NULL DEFAULT 'user'
});
export type Profile = z.infer<typeof ProfilesSchema>;

// tradelines
export const TradelinesSchema = z.object({
  id:             z.string().uuid(),        // uuid PK
  user_id:        z.string().uuid(),        // uuid FK → auth.users
  creditor_name:  z.string().nullable(),    // text NULL
  account_balance: z.string().nullable(),   // text NULL DEFAULT '0'
  account_type:   z.string().nullable(),    // text NULL
  account_status: z.string().nullable(),    // text NULL
  created_at:     z.date(),                 // timestamptz NOT NULL
  dispute_count:  z.number().int().nullable(), // integer NULL DEFAULT 0
  credit_limit:   z.string().nullable(),    // text NULL DEFAULT '0'
  monthly_payment: z.string().nullable(),   // text NULL DEFAULT '0'
  account_number: z.string().nullable(),    // text NULL
  credit_bureau:  z.string().nullable(),    // text NULL
  date_opened:    z.string().nullable(),    // text NULL
  isNegative:     z.boolean(),              // boolean NOT NULL DEFAULT false
});
export type Tradeline = z.infer<typeof TradelinesSchema>;

// user_documents
export const UserDocumentsSchema = z.object({
  id:             z.number(),               // bigint identity PK
  user_id:        z.string().uuid(),        // uuid NOT NULL
  created_at:     z.date().nullable(),      // timestamptz NULL DEFAULT now()
  document_type:  z.string().nullable(),    // text NULL
  file_path:      z.string().nullable(),    // text NULL
});
export type UserDocument = z.infer<typeof UserDocumentsSchema>;

// user_personal_info
export const UserPersonalInfoSchema = z.object({
  user_id:        z.string().uuid(),        // uuid PK/FK → auth.users
  first_Name:     z.string().nullable(),    // text NULL
  address:        z.string().nullable(),    // text NULL
  city:           z.string().nullable(),    // text NULL
  state:          z.string().nullable(),    // text NULL
  zip:            z.string().nullable(),    // text NULL
  phone:          z.string().nullable(),    // text NULL
  email:          z.string(),               // text NOT NULL
  ssn_last_four:  z.string().nullable(),    // text NULL
  updated_at:     z.date().nullable(),      // timestamptz NULL DEFAULT now()
  last_Name:      z.string().nullable(),    // text NULL
});
export type UserPersonalInfo = z.infer<typeof UserPersonalInfoSchema>;

// user_roles
export const UserRolesSchema = z.object({
  user_id:        z.string().uuid(),        // uuid PK/FK → auth.users
  role:           z.string(),               // text NOT NULL DEFAULT 'user'
  email:          z.string().nullable(),    // text NULL DEFAULT ''
  assigned_at:    z.date(),                 // timestamptz NOT NULL DEFAULT now()
});
export type UserRole = z.infer<typeof UserRolesSchema>;


export const ParsedTradelineSchema = z.object({
  accountName: z.string(),
  accountNumber: z.string(),
  creditorName: z.string(),
  originalCreditor: z.string().optional(),
  dateOpened: z.string(),
  dateLastReported: z.string(),
  creditLimit: z.string().optional(),
  highestBalance: z.string().optional(),
  currentBalance: z.string(),
  monthlyPayment: z.string().optional(),
  accountStatus: z.string(),
  paymentRating: z.string().optional(),
  isNegative: z.boolean(),
  bureaus: z.array(z.enum(["Equifax", "Experian", "TransUnion"])),
});

// New Tradeline schema for TradelinesPage editing form validation
export const TradelineSchema = z.object({
  id: z.string().min(1),
  creditor: z.string().min(1, { message: "Creditor is required" }),
  account_number: z.string().min(1, { message: "Account Number is required" }),
  status: z.string().min(1, { message: "Status is required" }),
  balance: z.number().nonnegative({ message: "Balance must be non-negative" }).optional(),
  date_opened: z.string().min(1, { message: "Date Opened is required" }),
  account_condition: z.string().min(1, { message: "Account Condition is required" }),
});

export const UserInfoSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  address: z.string().min(1, { message: "Address is required" }),
  city: z.string().min(1, { message: "City is required" }),
  state: z.string().min(2, { message: "State is required" }).max(2, { message: "State must be 2 characters" }),
  zip: z.string().min(5, { message: "Zip code is required" }).max(5, { message: "Zip code must be 5 characters" }),
});

export const NegativeItemSchema = z.object({
  creditorName: z.string(),
  accountNumber: z.string(),
  bureaus: z.array(z.enum(["Equifax", "Experian", "TransUnion"])),
});


export const LetterStateSchema = z.record(z.enum(["Equifax", "Experian", "TransUnion"]), z.string().nullable());

export const QualityStateSchema = z.record(z.enum(["Equifax", "Experian", "TransUnion"]), z.number());

export const SuggestionsStateSchema = z.record(z.enum(["Equifax", "Experian", "TransUnion"]), z.array(z.string()));

export const PersonalInfoSchema = z.record(z.string(), z.string().optional()).optional();