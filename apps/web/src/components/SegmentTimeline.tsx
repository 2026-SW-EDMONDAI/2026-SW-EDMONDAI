"use client";

import { Segment } from "@/lib/api";

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

interface Props {
  segments: Segment[];
  totalDurationMs?: number;
  selectedId?: string | null;
  onSelect?: (segment: Segment) => void;
}

export default function SegmentTimeline({
  segments,
  totalDurationMs,
  selectedId,
  onSelect,
}: Props) {
  const duration = totalDurationMs ?? (segments.at(-1)?.endMs ?? 1);

  return (
    <div className="space-y-1">
      {/* Proportional timeline bar */}
      <div className="relative h-4 bg-gray-100 rounded overflow-hidden mb-3">
        {segments.map((seg) => {
          const left = (seg.startMs / duration) * 100;
          const width = ((seg.endMs - seg.startMs) / duration) * 100;
          return (
            <button
              key={seg.id}
              onClick={() => onSelect?.(seg)}
              title={seg.title}
              className={`absolute top-0 h-full border-r border-white transition-colors ${
                selectedId === seg.id
                  ? "bg-blue-500"
                  : "bg-blue-200 hover:bg-blue-300"
              }`}
              style={{ left: `${left}%`, width: `${width}%` }}
            />
          );
        })}
      </div>

      {/* Segment list */}
      <div className="space-y-1">
        {segments.map((seg) => (
          <button
            key={seg.id}
            onClick={() => onSelect?.(seg)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-left text-sm transition-colors ${
              selectedId === seg.id
                ? "bg-blue-50 border border-blue-300"
                : "bg-white border border-gray-200 hover:bg-gray-50"
            }`}
          >
            <span className="font-mono text-xs text-gray-400 w-24 shrink-0">
              {formatMs(seg.startMs)} – {formatMs(seg.endMs)}
            </span>
            <span className="flex-1 font-medium text-gray-900 truncate">{seg.title}</span>
            <span
              className={`shrink-0 text-xs px-1.5 py-0.5 rounded ${
                seg.sourceType === "edited"
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              {seg.sourceType}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
