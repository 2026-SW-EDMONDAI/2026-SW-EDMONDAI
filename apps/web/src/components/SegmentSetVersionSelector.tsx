"use client";

import { SegmentSet } from "@/lib/api";

interface Props {
  sets: SegmentSet[];
  selectedId: string | null;
  onChange: (setId: string) => void;
}

export default function SegmentSetVersionSelector({ sets, selectedId, onChange }: Props) {
  if (sets.length === 0) return null;

  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-gray-600 whitespace-nowrap">버전</label>
      <select
        value={selectedId ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {sets.map((ss) => (
          <option key={ss.id} value={ss.id}>
            v{ss.versionNo} — {ss.status} ({ss.source})
          </option>
        ))}
      </select>
    </div>
  );
}
