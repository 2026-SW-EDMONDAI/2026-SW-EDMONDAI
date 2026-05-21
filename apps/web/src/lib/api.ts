const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const json = await res.json();

  if (!res.ok) {
    throw new ApiError(res.status, json?.error?.code ?? "UNKNOWN", json?.error?.message ?? "Request failed");
  }
  return json as T;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface Video {
  id: string;
  organizationId: string;
  title: string;
  description: string | null;
  status: string;
  durationMs: number | null;
  sourceType: string;
  uploadedBy: string;
  analyzedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface VideoListItem {
  id: string;
  title: string;
  status: string;
  durationMs: number | null;
  analyzedAt: string | null;
  latestSegmentCount: number;
}

export interface SignalConfig {
  videoId: string;
  confidenceCheckEnabled: boolean;
  quizEnabled: boolean;
  conceptSelectEnabled: boolean;
  summaryEnabled: boolean;
}

export interface SegmentSet {
  id: string;
  videoId: string;
  versionNo: number;
  status: string;
  source: string;
  createdBy: string | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Segment {
  id: string;
  segmentSetId: string;
  seqNo: number;
  startMs: number;
  endMs: number;
  title: string;
  topic: string | null;
  keyConcepts: string[] | null;
  summary: string | null;
  sourceType: string;
}

export interface CaptionCue {
  seqNo: number;
  startMs: number;
  endMs: number;
  text: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: { page: number; pageSize: number; total: number };
}

// ── API calls ──────────────────────────────────────────────────────────────

export const videoApi = {
  list(orgId: string, params?: { status?: string; search?: string; page?: number; pageSize?: number }) {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.search) q.set("search", params.search);
    if (params?.page) q.set("page", String(params.page));
    if (params?.pageSize) q.set("pageSize", String(params.pageSize));
    return request<PaginatedResponse<VideoListItem>>(`/orgs/${orgId}/videos?${q}`);
  },

  get(orgId: string, videoId: string) {
    return request<{ data: { video: Video } }>(`/orgs/${orgId}/videos/${videoId}`);
  },

  create(orgId: string, formData: FormData) {
    return request<{ data: { video: Video; signalConfig: SignalConfig } }>(`/orgs/${orgId}/videos`, {
      method: "POST",
      body: formData,
    });
  },

  update(orgId: string, videoId: string, body: { title?: string; description?: string }) {
    return request<{ data: Video }>(`/orgs/${orgId}/videos/${videoId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  analyze(orgId: string, videoId: string) {
    return request<{ data: { status: string } }>(`/orgs/${orgId}/videos/${videoId}/analyze`, {
      method: "POST",
      body: JSON.stringify({ regenerateSegments: true }),
    });
  },

  getSignalConfig(orgId: string, videoId: string) {
    return request<{ data: SignalConfig }>(`/orgs/${orgId}/videos/${videoId}/signal-config`);
  },

  updateSignalConfig(orgId: string, videoId: string, body: Partial<SignalConfig>) {
    return request<{ data: SignalConfig }>(`/orgs/${orgId}/videos/${videoId}/signal-config`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },
};

export const segmentApi = {
  listSets(orgId: string, videoId: string) {
    return request<{ data: SegmentSet[] }>(`/orgs/${orgId}/videos/${videoId}/segment-sets`);
  },

  latestSet(orgId: string, videoId: string) {
    return request<{ data: SegmentSet }>(`/orgs/${orgId}/videos/${videoId}/segment-sets/latest`);
  },

  cloneSet(orgId: string, videoId: string, setId: string, notes?: string) {
    return request<{ data: SegmentSet }>(
      `/orgs/${orgId}/videos/${videoId}/segment-sets/${setId}/clone`,
      { method: "POST", body: JSON.stringify({ notes }) },
    );
  },

  finalizeSet(orgId: string, videoId: string, setId: string) {
    return request<{ data: { segmentSetId: string; status: string } }>(
      `/orgs/${orgId}/videos/${videoId}/segment-sets/${setId}/finalize`,
      { method: "POST", body: JSON.stringify({}) },
    );
  },

  listSegments(orgId: string, setId: string) {
    return request<{ data: Segment[] }>(`/orgs/${orgId}/segment-sets/${setId}/segments`);
  },

  updateSegment(orgId: string, setId: string, segId: string, body: Partial<Segment>) {
    return request<{ data: Segment }>(
      `/orgs/${orgId}/segment-sets/${setId}/segments/${segId}`,
      { method: "PATCH", body: JSON.stringify(body) },
    );
  },

  splitSegment(orgId: string, setId: string, segId: string, splitAtMs: number) {
    return request<{ data: { newSegments: Segment[] } }>(
      `/orgs/${orgId}/segment-sets/${setId}/segments/${segId}/split`,
      { method: "POST", body: JSON.stringify({ splitAtMs }) },
    );
  },

  mergeSegments(orgId: string, setId: string, segmentIds: string[]) {
    return request<{ data: { mergedSegment: Segment } }>(
      `/orgs/${orgId}/segment-sets/${setId}/segments/merge`,
      { method: "POST", body: JSON.stringify({ segmentIds }) },
    );
  },
};

export const captionApi = {
  getCues(orgId: string, videoId: string, params?: { startMs?: number; endMs?: number }) {
    const q = new URLSearchParams();
    if (params?.startMs != null) q.set("startMs", String(params.startMs));
    if (params?.endMs != null) q.set("endMs", String(params.endMs));
    return request<{ data: CaptionCue[] }>(
      `/orgs/${orgId}/videos/${videoId}/captions/cues?${q}`,
    );
  },
};
