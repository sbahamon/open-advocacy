export enum ProjectStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ARCHIVED = 'archived',
}

export enum EntityStatus {
  SOLID_APPROVAL = 'solid_approval',
  LEANING_APPROVAL = 'leaning_approval',
  NEUTRAL = 'neutral',
  LEANING_DISAPPROVAL = 'leaning_disapproval',
  SOLID_DISAPPROVAL = 'solid_disapproval',
  UNKNOWN = 'unknown',
}

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  GROUP_ADMIN = 'group_admin',
  EDITOR = 'editor',
  VIEWER = 'viewer',
}
export interface Jurisdiction {
  id: string;
  name: string;
  description?: string;
  level: string; // city, state, federal
  created_at: string;
}

export interface Entity {
  id: string;
  name: string;
  title?: string;
  entity_type: string;
  email?: string;
  phone?: string;
  website?: string;
  address?: string;
  district_name?: string;
  jurisdiction_id: string;
  image_url?: string;
}

export interface EntityStatusRecord {
  id: string;
  entity_id: string;
  project_id: string;
  status: EntityStatus;
  notes?: string;
  record_metadata?: Record<string, unknown>;
  updated_at: string;
  updated_by: string;
}

export interface StatusDistribution {
  solid_approval: number;
  leaning_approval: number;
  neutral: number;
  leaning_disapproval: number;
  solid_disapproval: number;
  unknown: number;
  total: number;
}

export interface MetricDisplayConfig {
  key: string;
  label: string;
  description?: string;
  format?: string;
  show_in_table?: boolean;
  show_in_tooltip?: boolean;
  /** Per-metric data vintage (ISO date); falls back to the group-level metrics_as_of. */
  as_of?: string | null;
  /** Attribution line for metrics from a non-default data source. */
  source?: string | null;
}

export interface DashboardConfig {
  representative_title?: string;
  status_labels?: Record<string, string>;
  metrics?: MetricDisplayConfig[];
}

export interface ZoningAuditMatter {
  record_number: string;
  matter_guid: string;
  title?: string | null;
  address?: string | null;
  introduction_date?: string | null;
  final_action_date?: string | null;
  status?: string | null;
  sub_status?: string | null;
  lat?: number | null;
  lon?: number | null;
  near_boundary: boolean;
  span_days?: number | null;
  stalled: boolean;
  pending: boolean;
  withdrawn: boolean;
}

export interface WardAffordability {
  neighborhoods?: string | null;
  affordable_share_pct?: number | null;
  affordable_share_pct_2025?: number | null;
  affordable_listings_2025?: number | null;
  affordable_listings_2026?: number | null;
  total_listings_2025?: number | null;
  total_listings_2026?: number | null;
  affordability_rank_2025?: number | null;
  affordability_rank_2026?: number | null;
  affordability_rank_change?: number | null;
  median_rent_2025?: number | null;
  median_rent_2026?: number | null;
  median_sale_price_2025?: number | null;
  median_sale_price_2026?: number | null;
}

export interface ZoningAuditWard {
  ward: number;
  alder_name?: string | null;
  zoning_median_days?: number | null;
  zoning_matter_count: number;
  zoning_stalled_count: number;
  n_resolved: number;
  n_pending: number;
  matters: ZoningAuditMatter[];
  affordability?: WardAffordability | null;
}

export interface ZoningAuditResponse {
  group_name: string;
  jurisdiction_id?: string | null;
  meta: Record<string, unknown>;
  affordability_meta?: Record<string, unknown>;
  wards: ZoningAuditWard[];
  unassigned_matters: ZoningAuditMatter[];
}

export interface Project {
  id: string;
  title: string;
  description?: string;
  status: ProjectStatus;
  active: boolean;
  link?: string;
  preferred_status: EntityStatus;
  template_response?: string;
  jurisdiction_id: string;
  jurisdiction_name?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  group_id: string;
  status_distribution?: StatusDistribution;
  slug?: string;
  dashboard_config?: DashboardConfig;
}

export interface ProjectCreateData {
  title: string;
  description?: string;
  status?: ProjectStatus;
  active?: boolean;
  link?: string;
  preferred_status?: EntityStatus;
  template_response?: string;
  jurisdiction_id?: string;
  group_id?: string;
}

export interface ProjectFilterParams {
  status?: ProjectStatus;
  group_id?: string;
  skip?: number;
  limit?: number;
  include_archived?: boolean;
}

export interface Group {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  projects?: Project[];
}

export interface AddressLookupRequest {
  address: string;
}

// Auth interfaces
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface UserRegisterData {
  email: string;
  name?: string;
  password: string;
  group_id: string;
  role?: string;
  is_active?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name?: string;
  role: string;
  group_id: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface PasswordChangeData {
  user_id: string;
  new_password: string;
}

export interface ScorecardProject {
  id: string;
  title: string;
  slug?: string;
  description?: string;
  preferred_status: EntityStatus;
  status_labels?: Record<string, string>;
  position?: number | null;
}

export interface ScorecardEntityStatus {
  status: EntityStatus;
  label: string;
}

export interface ScorecardEntityRow {
  entity: Entity;
  statuses: Record<string, ScorecardEntityStatus>; // keyed by project_id
  aligned_count: number;
  total_scoreable: number;
  metrics?: Record<string, number | string | null>; // keyed by metric key
}

export interface ScorecardResponse {
  group_name: string;
  representative_title: string;
  projects: ScorecardProject[];
  entities: ScorecardEntityRow[];
  metrics?: MetricDisplayConfig[];
  metrics_as_of?: string | null;
}

export interface UserRoleChangeData {
  user_id: string;
  new_role: string;
}
