export interface TenantCreate {
  name: string;
  admin_email: string;
}

export interface TenantResponse {
  tenant_id: number;
  tenant_db: string;
  admin_email: string;
  initial_password: string;
}

export interface TenantInfo {
  id: number;
  name: string;
  db_name: string;
  db_host: string;
  db_port: string;
  db_user: string;
  admin_email: string;
  status: string;
  created_at: string;
}

export interface ApiError {
  detail: string;
}

