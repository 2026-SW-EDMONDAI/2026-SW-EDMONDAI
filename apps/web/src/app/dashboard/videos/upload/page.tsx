import VideoUploadForm from "@/components/VideoUploadForm";

const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID ?? "default-org-id";

export default function VideoUploadPage() {
  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-semibold text-gray-900 mb-6">영상 등록</h1>
      <VideoUploadForm orgId={ORG_ID} />
    </div>
  );
}
