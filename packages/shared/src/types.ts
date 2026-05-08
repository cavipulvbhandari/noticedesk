// Shared domain types. Mirror the database schema in packages/db/migrations.
// Keep in sync; the API serializes these from Pydantic models on the Python
// side. UUIDs are typed as branded strings to keep call sites from mixing
// up identifiers across entity kinds.

export type Brand<T, K extends string> = T & { readonly __brand: K };

export type TenantId = Brand<string, "TenantId">;
export type UserId = Brand<string, "UserId">;
export type ClientId = Brand<string, "ClientId">;
export type RegistrationId = Brand<string, "RegistrationId">;
export type MatterId = Brand<string, "MatterId">;
export type NoticeId = Brand<string, "NoticeId">;

export type Law = "GST" | "IT";

export type RegistrationType = Law;

export type UserRole =
  | "partner"
  | "managing_partner"
  | "manager"
  | "staff"
  | "client";

export type PricingTier = "solo" | "midsize" | "boutique" | "enterprise";

export type RegistrationStatus =
  | "active"
  | "suspended"
  | "cancelled"
  | "surrendered";

export type NoticeLifecycleStatus =
  | "issued"
  | "in_progress"
  | "due"
  | "due_date_over"
  | "reply_submitted"
  | "acknowledged"
  | "order_received"
  | "appeal_filed"
  | "closed"
  | "on_hold";

export type PanGstinReconciliationStatus =
  | "reconciled"
  | "pending"
  | "mismatch_blocked";

export interface Tenant {
  tenant_id: TenantId;
  legal_name: string;
  gstin: string | null;
  pan: string | null;
  address: string | null;
  jurisdiction: string | null;
  pricing_tier: PricingTier | null;
  annual_prepaid_until: string | null;
  partner_count: number | null;
  staff_count: number | null;
  delegation_matrix: unknown;
  dpdp_consent_record: unknown;
  created_at: string;
  updated_at: string;
}

export interface User {
  user_id: UserId;
  tenant_id: TenantId;
  name: string;
  role: UserRole;
  email: string | null;
  phone: string | null;
  whatsapp_opt_in: boolean;
  mfa_enabled: boolean;
  last_login: string | null;
  created_at: string;
}

export interface Client {
  client_id: ClientId;
  tenant_id: TenantId;
  pan: string;
  legal_name: string;
  trade_name: string | null;
  entity_type: string | null;
  cin: string | null;
  date_of_incorporation_or_birth: string | null;
  primary_contact_user_id: UserId | null;
  industry: string | null;
  group_relationships: unknown;
  billing_profile: unknown;
  created_at: string;
  updated_at: string;
}

export interface ClientRegistration {
  registration_id: RegistrationId;
  tenant_id: TenantId;
  client_id: ClientId;
  registration_type: RegistrationType;
  identifier_value: string;
  state_code: string | null;
  state_name: string | null;
  jurisdiction_office: string | null;
  registration_status: RegistrationStatus | null;
  effective_from: string | null;
  effective_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionContext {
  user: Pick<User, "user_id" | "name" | "role" | "email">;
  tenant: Pick<Tenant, "tenant_id" | "legal_name">;
}
