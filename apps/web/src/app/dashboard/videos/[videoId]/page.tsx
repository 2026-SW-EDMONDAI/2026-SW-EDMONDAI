"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { videoApi, Video, ApiError } from "@/lib/api";

const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID ?? "default-org-id";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    uploaded: "bg-blue-100 text-blue-700",
    processing: "bg-yellow-100 text-yellow-700",
    analyzed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-sm font-medium ${colors[status] ?? "bg-gray-100 text-gray-700"}`}>
      {status}
    </span>
  );
}

export default function VideoDetailPage() {
  const params = useParams();
  const videoId = params.videoId as string;

  const [video, setVideo] = useState<Video | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await videoApi.get(ORG_ID, videoId);
        setVideo(res.data.video);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "조회 실패");
      } finally {
        setLoading(false);
      }
    })();
  }, [videoId]);

  async function handleAnalyze() {
    setAnalyzing(true);
    try {
      await videoApi.analyze(ORG_ID, videoId);
      const res = await videoApi.get(ORG_ID, videoId);
      setVideo(res.data.video);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "분석 실행 실패");
    } finally {
      setAnalyzing(false);
    }
  }

  if (loading) return <div className="p-6 text-gray-400">불러오는 중...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!video) return null;

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/dashboard/videos" className="text-sm text-blue-600 hover:underline mb-2 inline-block">
            ← 목록으로
          </Link>
          <h1 className="text-xl font-semibold text-gray-900">{video.title}</h1>
          {video.description && (
            <p className="text-sm text-gray-600 mt-1">{video.description}</p>
          )}
        </div>
        <StatusBadge status={video.status} />
      </div>

      {/* Meta */}
      <div className="grid grid-cols-2 gap-4 bg-gray-50 rounded-lg p-4 text-sm">
        <div>
          <span className="text-gray-500">길이</span>
          <p className="font-medium">
            {video.durationMs
              ? `${Math.floor(video.durationMs / 60000)}분 ${Math.floor((video.durationMs % 60000) / 1000)}초`
              : "-"}
          </p>
        </div>
        <div>
          <span className="text-gray-500">분석 완료</span>
          <p className="font-medium">
            {video.analyzedAt ? new Date(video.analyzedAt).toLocaleString("ko-KR") : "-"}
          </p>
        </div>
        <div>
          <span className="text-gray-500">등록일</span>
          <p className="font-medium">{new Date(video.createdAt).toLocaleString("ko-KR")}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {(video.status === "uploaded" || video.status === "failed") && (
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
          >
            {analyzing ? "분석 요청 중..." : "분석 실행"}
          </button>
        )}
        {video.status === "analyzed" && (
          <Link
            href={`/dashboard/videos/${videoId}/segments`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
          >
            세그먼트 검토
          </Link>
        )}
      </div>
    </div>
  );
}
