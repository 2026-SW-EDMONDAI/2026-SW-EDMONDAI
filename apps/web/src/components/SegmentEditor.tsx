"use client";

import { useState } from "react";
import { Segment, segmentApi, ApiError } from "@/lib/api";

interface Props {
  orgId: string;
  setId: string;
  segment: Segment;
  isSetFinalized: boolean;
  onUpdated: (updated: Segment) => void;
  onSplit: (segments: Segment[]) => void;
}

export default function SegmentEditor({
  orgId,
  setId,
  segment,
  isSetFinalized,
  onUpdated,
  onSplit,
}: Props) {
  const [title, setTitle] = useState(segment.title);
  const [topic, setTopic] = useState(segment.topic ?? "");
  const [keyConcepts, setKeyConcepts] = useState(
    (segment.keyConcepts ?? []).join(", "),
  );
  const [summary, setSummary] = useState(segment.summary ?? "");
  const [splitAtMs, setSplitAtMs] = useState("");

  const [saving, setSaving] = useState(false);
  const [splitting, setSplitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await segmentApi.updateSegment(orgId, setId, segment.id, {
        title,
        topic: topic || undefined,
        keyConcepts: keyConcepts ? keyConcepts.split(",").map((s) => s.trim()) : [],
        summary: summary || undefined,
      });
      onUpdated(res.data);
      setSuccess("저장되었습니다.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  }

  async function handleSplit() {
    const ms = parseInt(splitAtMs, 10);
    if (isNaN(ms)) {
      setError("분할 위치(ms)를 입력하세요.");
      return;
    }
    setSplitting(true);
    setError(null);
    try {
      const res = await segmentApi.splitSegment(orgId, setId, segment.id, ms);
      onSplit(res.data.newSegments);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "분할 실패");
    } finally {
      setSplitting(false);
    }
  }

  if (isSetFinalized) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
        이 세그먼트 세트는 확정(finalized) 상태입니다. 편집하려면 복제 후 수정하세요.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-green-600">{success}</p>}

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">제목</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">주제</label>
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          핵심 개념 <span className="text-gray-400">(쉼표로 구분)</span>
        </label>
        <input
          value={keyConcepts}
          onChange={(e) => setKeyConcepts(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">요약</label>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={2}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
      >
        {saving ? "저장 중..." : "저장"}
      </button>

      <hr className="my-4" />

      <div>
        <p className="text-xs font-medium text-gray-500 mb-2">세그먼트 분할</p>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={splitAtMs}
            onChange={(e) => setSplitAtMs(e.target.value)}
            placeholder="분할 위치 (ms)"
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSplit}
            disabled={splitting}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 text-sm"
          >
            {splitting ? "분할 중..." : "분할"}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-1">
          범위: {segment.startMs}ms – {segment.endMs}ms
        </p>
      </div>
    </div>
  );
}
