"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { segmentApi, Segment, SegmentSet, ApiError } from "@/lib/api";
import SegmentSetVersionSelector from "@/components/SegmentSetVersionSelector";
import SegmentTimeline from "@/components/SegmentTimeline";
import SegmentEditor from "@/components/SegmentEditor";

const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID ?? "default-org-id";

export default function SegmentsPage() {
  const params = useParams();
  const videoId = params.videoId as string;

  const [sets, setSets] = useState<SegmentSet[]>([]);
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [selectedSeg, setSelectedSeg] = useState<Segment | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Load segment sets
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await segmentApi.listSets(ORG_ID, videoId);
        setSets(res.data);
        if (res.data.length > 0) {
          const latest = res.data.at(-1)!;
          setSelectedSetId(latest.id);
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "세그먼트 세트 조회 실패");
      } finally {
        setLoading(false);
      }
    })();
  }, [videoId]);

  // Load segments for selected set
  const loadSegments = useCallback(async (setId: string) => {
    try {
      const res = await segmentApi.listSegments(ORG_ID, setId);
      setSegments(res.data);
      setSelectedSeg(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "세그먼트 조회 실패");
    }
  }, []);

  useEffect(() => {
    if (selectedSetId) loadSegments(selectedSetId);
  }, [selectedSetId, loadSegments]);

  const currentSet = sets.find((s) => s.id === selectedSetId);
  const isFinalized = currentSet?.status === "finalized";

  async function handleClone() {
    if (!selectedSetId) return;
    try {
      const res = await segmentApi.cloneSet(ORG_ID, videoId, selectedSetId, "수동 편집용");
      setSets((prev) => [...prev, res.data]);
      setSelectedSetId(res.data.id);
      setActionMsg("새 버전이 생성되었습니다.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "복제 실패");
    }
  }

  async function handleFinalize() {
    if (!selectedSetId) return;
    try {
      await segmentApi.finalizeSet(ORG_ID, videoId, selectedSetId);
      setSets((prev) =>
        prev.map((s) => (s.id === selectedSetId ? { ...s, status: "finalized" } : s)),
      );
      setActionMsg("세그먼트 세트가 확정되었습니다.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "확정 실패");
    }
  }

  function handleSegmentUpdated(updated: Segment) {
    setSegments((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    setSelectedSeg(updated);
    setActionMsg("세그먼트가 저장되었습니다.");
  }

  function handleSplit(newSegs: Segment[]) {
    if (!selectedSetId) return;
    loadSegments(selectedSetId);
    setSelectedSeg(null);
    setActionMsg("세그먼트가 분할되었습니다.");
  }

  if (loading) return <div className="p-6 text-gray-400">불러오는 중...</div>;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-4">
        <Link href={`/dashboard/videos/${videoId}`} className="text-sm text-blue-600 hover:underline">
          ← 영상 상세
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">세그먼트 검토</h1>
      </div>

      {error && <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{error}</div>}
      {actionMsg && (
        <div className="p-3 rounded-md bg-green-50 text-green-700 text-sm flex items-center justify-between">
          {actionMsg}
          <button onClick={() => setActionMsg(null)} className="text-green-500 hover:text-green-700">✕</button>
        </div>
      )}

      {/* Version selector + actions */}
      <div className="flex items-center gap-3 flex-wrap">
        <SegmentSetVersionSelector
          sets={sets}
          selectedId={selectedSetId}
          onChange={setSelectedSetId}
        />
        {!isFinalized && selectedSetId && (
          <>
            <button
              onClick={handleClone}
              className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              복제 (새 버전)
            </button>
            <button
              onClick={handleFinalize}
              className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200"
            >
              확정
            </button>
          </>
        )}
        {isFinalized && (
          <span className="text-xs text-green-700 bg-green-100 px-2 py-1 rounded">확정됨</span>
        )}
      </div>

      {/* Main content: timeline + editor */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            세그먼트 목록 ({segments.length}개)
          </p>
          {segments.length === 0 ? (
            <p className="text-sm text-gray-400">세그먼트가 없습니다.</p>
          ) : (
            <SegmentTimeline
              segments={segments}
              selectedId={selectedSeg?.id}
              onSelect={setSelectedSeg}
            />
          )}
        </div>

        <div>
          {selectedSeg && selectedSetId ? (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">세그먼트 편집</p>
              <SegmentEditor
                orgId={ORG_ID}
                setId={selectedSetId}
                segment={selectedSeg}
                isSetFinalized={isFinalized}
                onUpdated={handleSegmentUpdated}
                onSplit={handleSplit}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-gray-400 py-8">
              왼쪽에서 세그먼트를 선택하세요.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
