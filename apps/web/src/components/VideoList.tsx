"use client";

import Link from "next/link";
import { VideoListItem } from "@/lib/api";

function statusBadge(status: string) {
  const colors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    uploaded: "bg-blue-100 text-blue-700",
    processing: "bg-yellow-100 text-yellow-700",
    analyzed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    archived: "bg-gray-200 text-gray-500",
  };
  return colors[status] ?? "bg-gray-100 text-gray-700";
}

function formatDuration(ms: number | null): string {
  if (!ms) return "-";
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}

interface Props {
  orgId: string;
  videos: VideoListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function VideoList({ orgId, videos, total, page, pageSize, onPageChange }: Props) {
  const totalPages = Math.ceil(total / pageSize);

  if (videos.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-lg">등록된 영상이 없습니다.</p>
        <Link
          href={`/dashboard/videos/upload`}
          className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          첫 영상 업로드
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">제목</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">길이</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">분석 완료</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {videos.map((v) => (
              <tr key={v.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{v.title}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusBadge(v.status)}`}>
                    {v.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{formatDuration(v.durationMs)}</td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {v.analyzedAt ? new Date(v.analyzedAt).toLocaleString("ko-KR") : "-"}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/dashboard/videos/${v.id}`}
                    className="text-blue-600 hover:underline text-sm"
                  >
                    상세 보기
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-end gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
          >
            이전
          </button>
          <span className="text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}
