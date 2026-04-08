import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function login(username: string, password: string): Promise<string> {
  const params = new URLSearchParams({ username, password });
  const { data } = await api.post<{ access_token: string }>(
    "/api/auth/login",
    params.toString(),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  return data.access_token;
}

// ── Cases ─────────────────────────────────────────────────────────────────────
export interface Case {
  id: number;
  title: string;
  description: string | null;
  legal_basis: string | null;
  created_by: number;
  created_at: string;
  closed_at: string | null;
}

export async function listCases(): Promise<Case[]> {
  const { data } = await api.get<Case[]>("/api/cases/");
  return data;
}

export async function getCase(id: number): Promise<Case> {
  const { data } = await api.get<Case>(`/api/cases/${id}`);
  return data;
}

export async function createCase(payload: {
  title: string;
  description?: string;
  legal_basis?: string;
}): Promise<Case> {
  const { data } = await api.post<Case>("/api/cases/", payload);
  return data;
}

// ── Evidence ──────────────────────────────────────────────────────────────────
export interface EvidenceItem {
  id: number;
  case_id: number;
  original_filename: string;
  mime_type: string | null;
  size_bytes: number;
  sha256: string;
  source_description: string | null;
  tool_name: string | null;
  tool_version: string | null;
  uploaded_by: number;
  acquired_at: string;
}

export async function listEvidence(caseId: number): Promise<EvidenceItem[]> {
  const { data } = await api.get<EvidenceItem[]>(`/api/cases/${caseId}/evidence/`);
  return data;
}

export async function uploadEvidence(
  caseId: number,
  file: File,
  source_description: string,
  tool_name: string,
  tool_version: string
): Promise<EvidenceItem> {
  const form = new FormData();
  form.append("file", file);
  if (source_description) form.append("source_description", source_description);
  if (tool_name) form.append("tool_name", tool_name);
  if (tool_version) form.append("tool_version", tool_version);
  const { data } = await api.post<EvidenceItem>(
    `/api/cases/${caseId}/evidence/`,
    form
  );
  return data;
}

export function downloadEvidenceUrl(caseId: number, evidenceId: number): string {
  return `${API_BASE}/api/cases/${caseId}/evidence/${evidenceId}/download`;
}

// ── Custody ───────────────────────────────────────────────────────────────────
export interface CustodyEvent {
  id: number;
  case_id: number | null;
  evidence_item_id: number | null;
  action: string;
  actor_id: number;
  actor_role: string;
  timestamp_utc: string;
  source_ip: string | null;
  notes: string | null;
  prev_event_hash: string | null;
  event_hash: string;
}

export async function listCustodyEvents(): Promise<CustodyEvent[]> {
  const { data } = await api.get<CustodyEvent[]>("/api/custody/");
  return data;
}

export async function verifyCustodyChain(): Promise<{
  total_events: number;
  errors: string[];
  chain_intact: boolean;
}> {
  const { data } = await api.get("/api/custody/verify");
  return data;
}
