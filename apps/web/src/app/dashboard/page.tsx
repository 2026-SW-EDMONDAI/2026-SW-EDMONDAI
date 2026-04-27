export default function DashboardPage() {
  return (
    <div>
      <h1 className="mb-4 text-xl font-bold text-gray-800">대시보드</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {["등록 영상", "분석 완료", "추천 대기", "적용 완료"].map((label) => (
          <div
            key={label}
            className="rounded-lg border border-gray-200 bg-white p-5"
          >
            <p className="text-sm text-gray-500">{label}</p>
            <p className="mt-1 text-2xl font-bold text-gray-800">—</p>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6">
        <p className="text-sm text-gray-400">
          데이터가 연결되면 여기에 최근 활동과 주요 지표가 표시됩니다.
        </p>
      </div>
    </div>
  );
}
