"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { videoApi, ApiError } from "@/lib/api";

interface Props {
  orgId: string;
}

export default function VideoUploadForm({ orgId }: Props) {
  const router = useRouter();
  const videoInputRef = useRef<HTMLInputElement>(null);
  const subtitleInputRef = useRef<HTMLInputElement>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [confidenceCheck, setConfidenceCheck] = useState(true);
  const [quiz, setQuiz] = useState(false);
  const [conceptSelect, setConceptSelect] = useState(false);
  const [summary, setSummary] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("제목을 입력해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    if (description) formData.append("description", description);
    formData.append("sourceType", "upload");
    formData.append("confidenceCheckEnabled", String(confidenceCheck));
    formData.append("quizEnabled", String(quiz));
    formData.append("conceptSelectEnabled", String(conceptSelect));
    formData.append("summaryEnabled", String(summary));

    const videoFile = videoInputRef.current?.files?.[0];
    if (videoFile) formData.append("videoFile", videoFile);

    const subtitleFile = subtitleInputRef.current?.files?.[0];
    if (subtitleFile) formData.append("subtitleFile", subtitleFile);

    setLoading(true);
    setError(null);
    try {
      const res = await videoApi.create(orgId, formData);
      router.push(`/dashboard/videos/${res.data.video.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("업로드 중 오류가 발생했습니다.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{error}</div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          제목 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="영상 제목"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="영상 설명 (선택)"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">영상 파일</label>
        <input
          ref={videoInputRef}
          type="file"
          accept="video/*"
          className="w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700 file:text-sm hover:file:bg-blue-100"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          자막 파일 <span className="text-gray-400">(VTT/SRT)</span>
        </label>
        <input
          ref={subtitleInputRef}
          type="file"
          accept=".vtt,.srt"
          className="w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:bg-gray-50 file:text-gray-700 file:text-sm hover:file:bg-gray-100"
        />
      </div>

      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">명시적 신호 설정</p>
        <div className="space-y-2">
          {[
            { label: "이해도 체크", value: confidenceCheck, setter: setConfidenceCheck },
            { label: "퀴즈", value: quiz, setter: setQuiz },
            { label: "핵심 개념 선택", value: conceptSelect, setter: setConceptSelect },
            { label: "한 줄 요약", value: summary, setter: setSummary },
          ].map(({ label, value, setter }) => (
            <label key={label} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => setter(e.target.checked)}
                className="rounded border-gray-300"
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
      >
        {loading ? "업로드 중..." : "영상 등록"}
      </button>
    </form>
  );
}
