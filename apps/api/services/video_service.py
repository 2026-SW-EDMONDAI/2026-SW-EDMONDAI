import os
import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import AppException
from models.core import Video, VideoStatus
from models.video import VideoAsset, VideoSignalConfig


class VideoService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- Video CRUD ----------

    def list_videos(
        self,
        org_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Video], int]:
        q = select(Video).where(Video.organization_id == org_id)
        if status:
            q = q.where(Video.status == status)
        if search:
            q = q.where(Video.title.ilike(f"%{search}%"))
        total = self.db.scalar(select(Video).where(Video.organization_id == org_id).with_only_columns(Video.id).correlate(None).subquery().count()) or 0

        from sqlalchemy import func
        count_q = select(func.count()).select_from(
            select(Video).where(Video.organization_id == org_id)
            .filter(Video.status == status if status else True)
        ).scalar_subquery()

        count_stmt = select(func.count(Video.id)).where(Video.organization_id == org_id)
        if status:
            count_stmt = count_stmt.where(Video.status == status)
        if search:
            count_stmt = count_stmt.where(Video.title.ilike(f"%{search}%"))
        total = self.db.scalar(count_stmt) or 0

        q = q.order_by(Video.created_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        videos = list(self.db.scalars(q).all())
        return videos, total

    def get_video(self, org_id: uuid.UUID, video_id: uuid.UUID) -> Video:
        video = self.db.scalar(
            select(Video).where(Video.id == video_id, Video.organization_id == org_id)
        )
        if not video:
            raise AppException(code="NOT_FOUND", message="Video not found.", status_code=404)
        return video

    def create_video(
        self,
        org_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        title: str,
        description: str | None,
        source_type: str,
        video_file: UploadFile | None = None,
        subtitle_file: UploadFile | None = None,
        confidence_check_enabled: bool = True,
        quiz_enabled: bool = False,
        concept_select_enabled: bool = False,
        summary_enabled: bool = False,
    ) -> tuple[Video, VideoSignalConfig]:
        video = Video(
            id=uuid.uuid4(),
            organization_id=org_id,
            title=title,
            description=description,
            status=VideoStatus.uploaded,
            source_type=source_type,
            uploaded_by=uploaded_by,
        )
        self.db.add(video)
        self.db.flush()

        # Store file assets (local storage for MVP)
        if video_file:
            storage_path = self._save_file(video_file, str(video.id), "video")
            asset = VideoAsset(
                id=uuid.uuid4(),
                video_id=video.id,
                asset_type="video_file",
                storage_path=storage_path,
                file_name=video_file.filename or "video",
                mime_type=video_file.content_type,
            )
            self.db.add(asset)

        if subtitle_file:
            storage_path = self._save_file(subtitle_file, str(video.id), "subtitle")
            asset = VideoAsset(
                id=uuid.uuid4(),
                video_id=video.id,
                asset_type="subtitle_file",
                storage_path=storage_path,
                file_name=subtitle_file.filename or "subtitle",
                mime_type=subtitle_file.content_type,
            )
            self.db.add(asset)

        # Signal config
        signal_config = VideoSignalConfig(
            id=uuid.uuid4(),
            video_id=video.id,
            confidence_check_enabled=confidence_check_enabled,
            quiz_enabled=quiz_enabled,
            concept_select_enabled=concept_select_enabled,
            summary_enabled=summary_enabled,
        )
        self.db.add(signal_config)
        self.db.commit()
        self.db.refresh(video)
        self.db.refresh(signal_config)
        return video, signal_config

    def update_video(
        self, org_id: uuid.UUID, video_id: uuid.UUID, title: str | None, description: str | None
    ) -> Video:
        video = self.get_video(org_id, video_id)
        if title is not None:
            video.title = title
        if description is not None:
            video.description = description
        self.db.commit()
        self.db.refresh(video)
        return video

    def trigger_analyze(self, org_id: uuid.UUID, video_id: uuid.UUID) -> None:
        video = self.get_video(org_id, video_id)
        if video.status not in (VideoStatus.uploaded, VideoStatus.analyzed, VideoStatus.failed):
            raise AppException(
                code="INVALID_STATUS",
                message="Video cannot be analyzed in its current status.",
                status_code=409,
            )
        video.status = VideoStatus.processing
        self.db.commit()

        # Publish Celery task (import here to avoid circular at module load)
        try:
            from worker_client import publish_analyze_video
            publish_analyze_video(str(video_id))
        except Exception:
            pass

    # ---------- Signal Config ----------

    def get_signal_config(self, org_id: uuid.UUID, video_id: uuid.UUID) -> VideoSignalConfig:
        self.get_video(org_id, video_id)
        config = self.db.scalar(
            select(VideoSignalConfig).where(VideoSignalConfig.video_id == video_id)
        )
        if not config:
            raise AppException(code="NOT_FOUND", message="Signal config not found.", status_code=404)
        return config

    def update_signal_config(
        self,
        org_id: uuid.UUID,
        video_id: uuid.UUID,
        confidence_check_enabled: bool | None,
        quiz_enabled: bool | None,
        concept_select_enabled: bool | None,
        summary_enabled: bool | None,
    ) -> VideoSignalConfig:
        config = self.get_signal_config(org_id, video_id)
        if confidence_check_enabled is not None:
            config.confidence_check_enabled = confidence_check_enabled
        if quiz_enabled is not None:
            config.quiz_enabled = quiz_enabled
        if concept_select_enabled is not None:
            config.concept_select_enabled = concept_select_enabled
        if summary_enabled is not None:
            config.summary_enabled = summary_enabled
        self.db.commit()
        self.db.refresh(config)
        return config

    # ---------- Captions ----------

    def get_caption_cues(
        self,
        org_id: uuid.UUID,
        video_id: uuid.UUID,
        start_ms: int | None = None,
        end_ms: int | None = None,
        language_code: str | None = None,
    ) -> list:
        from models.video import CaptionTrack, CaptionCue
        self.get_video(org_id, video_id)

        track_q = select(CaptionTrack).where(CaptionTrack.video_id == video_id)
        if language_code:
            track_q = track_q.where(CaptionTrack.language_code == language_code)
        else:
            track_q = track_q.where(CaptionTrack.is_default == True)

        track = self.db.scalar(track_q)
        if not track:
            # Fallback: any track for this video
            track = self.db.scalar(
                select(CaptionTrack).where(CaptionTrack.video_id == video_id)
            )
        if not track:
            return []

        cue_q = select(CaptionCue).where(CaptionCue.caption_track_id == track.id)
        if start_ms is not None:
            cue_q = cue_q.where(CaptionCue.end_ms >= start_ms)
        if end_ms is not None:
            cue_q = cue_q.where(CaptionCue.start_ms <= end_ms)
        cue_q = cue_q.order_by(CaptionCue.seq_no)
        return list(self.db.scalars(cue_q).all())

    # ---------- Helpers ----------

    def _save_file(self, upload_file: UploadFile, video_id: str, kind: str) -> str:
        upload_dir = os.getenv("UPLOAD_DIR", "/tmp/segmentflow_uploads")
        dest_dir = os.path.join(upload_dir, video_id)
        os.makedirs(dest_dir, exist_ok=True)
        file_name = upload_file.filename or f"{kind}_file"
        dest_path = os.path.join(dest_dir, file_name)
        with open(dest_path, "wb") as f:
            f.write(upload_file.file.read())
        return dest_path
