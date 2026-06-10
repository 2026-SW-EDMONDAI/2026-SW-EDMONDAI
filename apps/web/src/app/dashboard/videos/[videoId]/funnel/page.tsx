"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ApiError,
  FunnelResponse,
  SegmentSet,
  funnelApi,
  segmentApi,
} from "@/lib/api";
import SegmentSetVersionSelector from "@/components/SegmentSetVersionSelector";

const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID ?? "default-org-id";

type SignalFilter = "all" | "implicit" | "explicit";

const RISK_LABELS: Record<string, string> = {
  dropout_spike: "이탈 급증",
  rewatch_spike: "재시청 급증",
  low_explicit_signal: "명시신호 부족",
  transition_drop: "이동률 하락",
};

function formatMs(ms: number): string {
  const sec = Math.floor(ms / 1000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function pct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function heatColor(rate: number): string {
  // green (good) → red (risky). Uses dropout_rate as input.
  if (rate >= 0.3) return "bg-red-200";
  if (rate >= 0.2) return "bg-orange-200";
  if (rate >= 0.1) return "bg-yellow-200";
  return "bg-green-200";
}

export default function FunnelPage() {
  const params = useParams();
  const videoId = params.videoId as string;

  const [sets, setSets] = useState<SegmentSet[]>([]);
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null);
  const [funnel, setFunnel] = useState<FunnelResponse | null>(null);
  const [signalFilter, setSignalFilter] = useState<SignalFilter>("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load segment sets
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await segmentApi.listSets(ORG_ID, videoId);
        setSets(res.data);
        const finalized = res.data.find((s) => s.status === "finalized");
        const target = finalized ?? res.data.at(-1);
        if (target) setSelectedSetId(target.id);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "세그먼트 세트 조회 실패");
      } finally {
        setLoading(false);
      }
    })();
  }, [videoId]);

  // Load funnel for selected set
  const loadFunnel = useCallback(
    async (setId: string) => {
      setError(null);
      try {
        const res = await funnelApi.getVideoFunnel(ORG_ID, videoId, {
          segmentSetId: setId,
        });
        setFunnel(res.data);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "퍼널 조회 실패");
        setFunnel(null);
      }
    },
    [videoId],
  );

  useEffect(() => {
    if (selectedSetId) loadFunnel(selectedSetId);
  }, [selectedSetId, loadFunnel]);

  const summary = funnel?.videoSummary;
  const segments = funnel?.segments ?? [];

  const totalRisk = useMemo(
    () => segments.reduce((acc, s) => acc + (s.riskFlags.length > 0 ? 1 : 0), 0),
    [segments],
  );

  if (loading) {
    return <div className="p-6 text-gray-400">불러오는 중...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href={`/dashboard/videos/${videoId}`}
          className="text-sm text-blue-600 hover:underline"
        >
          ← 영상 상세
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">학습 퍼널</h1>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{error}</div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <SegmentSetVersionSelector
          sets={sets}
          selectedId={selectedSetId}
          onChange={setSelectedSetId}
        />
        <div className="flex items-center bg-gray-100 rounded-md p-1 text-sm">
          {(["all", "implicit", "explicit"] as SignalFilter[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setSignalFilter(mode)}
              className={`px-3 py-1 rounded ${
                signalFilter === mode
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {mode === "all" ? "전체" : mode === "implicit" ? "암묵" : "명시"}
            </button>
          ))}
        </div>
        {summary?.metricDate && (
          <span className="text-xs text-gray-500">기준일: {summary.metricDate}</span>
        )}
      </div>

      {/* Video KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          label="영상 완주율"
          value={pct(summary?.completionRate ?? 0)}
        />
        <KpiCard
          label="다음 세그먼트 이동률"
          value={pct(summary?.nextTransitionRate)}
        />
        <KpiCard
          label="명시 응답률"
          value={pct(summary?.explicitResponseRate)}
        />
        <KpiCard
          label="위험 세그먼트"
          value={`${totalRisk} / ${segments.length}`}
          warning={totalRisk > 0}
        />
      </div>

      {/* Funnel table */}
      <div className="bg-white border border-gray-200 rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="px-3 py-2 text-left">#</th>
              <th className="px-3 py-2 text-left">세그먼트</th>
              <th className="px-3 py-2 text-left">구간</th>
              <th className="px-3 py-2 text-right">진입</th>
              <th className="px-3 py-2 text-right">완료</th>
              <th className="px-3 py-2 text-right">완료율</th>
              <th className="px-3 py-2 text-right">이탈률</th>
              {signalFilter !== "explicit" && (
                <>
                  <th className="px-3 py-2 text-right">재시청</th>
                  <th className="px-3 py-2 text-right">이동률</th>
                </>
              )}
              {signalFilter !== "implicit" && (
                <>
                  <th className="px-3 py-2 text-right">명시응답</th>
                  <th className="px-3 py-2 text-right">이해함</th>
                </>
              )}
              <th className="px-3 py-2 text-left">위험</th>
            </tr>
          </thead>
          <tbody>
            {segments.length === 0 && (
              <tr>
                <td colSpan={12} className="px-3 py-6 text-center text-gray-400">
                  해당 세그먼트 세트의 집계 데이터가 없습니다.
                </td>
              </tr>
            )}
            {segments.map((entry) => {
              const m = entry.metrics;
              return (
                <tr
                  key={entry.segment.id}
                  className="border-t border-gray-100 hover:bg-gray-50"
                >
                  <td className="px-3 py-2 text-gray-500">
                    {entry.segment.seqNo}
                  </td>
                  <td className="px-3 py-2 text-gray-900">{entry.segment.title}</td>
                  <td className="px-3 py-2 text-gray-500">
                    {formatMs(entry.segment.startMs)}–{formatMs(entry.segment.endMs)}
                  </td>
                  <td className="px-3 py-2 text-right">{m.viewersStarted}</td>
                  <td className="px-3 py-2 text-right">{m.viewersCompleted}</td>
                  <td className="px-3 py-2 text-right">{pct(m.completionRate)}</td>
                  <td className={`px-3 py-2 text-right ${heatColor(m.dropoutRate)}`}>
                    {pct(m.dropoutRate)}
                  </td>
                  {signalFilter !== "explicit" && (
                    <>
                      <td className="px-3 py-2 text-right">{pct(m.rewatchRate)}</td>
                      <td className="px-3 py-2 text-right">
                        {pct(m.nextTransitionRate)}
                      </td>
                    </>
                  )}
                  {signalFilter !== "implicit" && (
                    <>
                      <td className="px-3 py-2 text-right">
                        {pct(m.explicitResponseRate)}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {pct(m.confidencePositiveRate)}
                      </td>
                    </>
                  )}
                  <td className="px-3 py-2">
                    <div className="flex gap-1 flex-wrap">
                      {entry.riskFlags.map((flag) => (
                        <span
                          key={flag}
                          className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700"
                        >
                          {RISK_LABELS[flag] ?? flag}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  warning,
}: {
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <div
      className={`border rounded-md p-4 ${
        warning ? "border-red-200 bg-red-50" : "border-gray-200 bg-white"
      }`}
    >
      <p className="text-xs text-gray-500">{label}</p>
      <p
        className={`text-2xl font-semibold mt-1 ${
          warning ? "text-red-700" : "text-gray-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
