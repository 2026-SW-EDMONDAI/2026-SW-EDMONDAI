"""
Video processing Celery task.

Flow:
  1. Load video record from DB
  2. Find subtitle file asset
  3. Parse VTT/SRT → CaptionTrack + CaptionCues
  4. Auto-generate SegmentSet (version 1, draft, source=auto) from cues
  5. Update video.status → analyzed | failed
"""
import logging
import os
import re
import uuid
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def _get_db_session():
    db_url = (
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER', 'segmentflow')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'segmentflow_dev')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'segmentflow')}"
    )
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


# ── VTT/SRT parsers ────────────────────────────────────────────────────────

def _ms(time_str: str) -> int:
    """Convert HH:MM:SS.mmm or HH:MM:SS,mmm to milliseconds."""
    time_str = time_str.strip().replace(",", ".")
    parts = time_str.split(":")
    hours, minutes, rest = int(parts[0]), int(parts[1]), parts[2]
    secs, millis = rest.split(".")
    return (hours * 3600 + minutes * 60 + int(secs)) * 1000 + int(millis[:3].ljust(3, "0"))


def parse_vtt(content: str) -> list[dict]:
    """Return list of {seq_no, start_ms, end_ms, text}."""
    cues = []
    lines = content.splitlines()
    i = 0
    seq = 1
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            times = re.split(r"\s+-->\s+", line)
            start_ms = _ms(times[0])
            end_ms = _ms(times[1].split()[0])  # strip position hints
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            cues.append({"seq_no": seq, "start_ms": start_ms, "end_ms": end_ms, "text": " ".join(text_lines)})
            seq += 1
        else:
            i += 1
    return cues


def parse_srt(content: str) -> list[dict]:
    """Return list of {seq_no, start_ms, end_ms, text}."""
    cues = []
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        block_lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if len(block_lines) < 3:
            continue
        try:
            seq_no = int(block_lines[0])
        except ValueError:
            continue
        if "-->" not in block_lines[1]:
            continue
        times = re.split(r"\s+-->\s+", block_lines[1])
        start_ms = _ms(times[0])
        end_ms = _ms(times[1])
        text = " ".join(block_lines[2:])
        cues.append({"seq_no": seq_no, "start_ms": start_ms, "end_ms": end_ms, "text": text})
    return cues


def _parse_subtitle(file_path: str) -> list[dict]:
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    if file_path.lower().endswith(".vtt"):
        return parse_vtt(content)
    return parse_srt(content)


# ── Segment auto-generation ────────────────────────────────────────────────

_SEGMENT_DURATION_MS = 5 * 60 * 1000  # 5-minute chunks by default


def _generate_segments_from_cues(cues: list[dict]) -> list[dict]:
    """Group cues into ~5-minute segments."""
    if not cues:
        return []

    segments = []
    seg_start = cues[0]["start_ms"]
    seg_cues: list[dict] = []
    seq = 1

    for cue in cues:
        seg_cues.append(cue)
        if cue["end_ms"] - seg_start >= _SEGMENT_DURATION_MS:
            segments.append({
                "seq_no": seq,
                "start_ms": seg_start,
                "end_ms": cue["end_ms"],
                "title": f"Segment {seq}",
                "source_type": "auto",
            })
            seq += 1
            seg_start = cue["end_ms"]
            seg_cues = []

    # Remaining cues → last segment
    if seg_cues:
        segments.append({
            "seq_no": seq,
            "start_ms": seg_start,
            "end_ms": seg_cues[-1]["end_ms"],
            "title": f"Segment {seq}",
            "source_type": "auto",
        })

    return segments


# ── Celery task ────────────────────────────────────────────────────────────

@shared_task(
    name="worker.tasks.video_processing.analyze_video",
    queue="video-processing",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def analyze_video(self, video_id: str) -> dict:
    """
    Celery task: parse subtitle + auto-generate segments for a video.

    Idempotent: if a segment_set with version=1 and source=auto already
    exists for this video, the task skips re-generation.
    """
    db = None
    try:
        # Import models here (worker process may not have full app context)
        from models.core import Video, VideoStatus
        from models.video import CaptionCue, CaptionTrack, VideoAsset
        from models.segment import Segment, SegmentSet, SegmentSetStatus

        db = _get_db_session()
        vid_uuid = uuid.UUID(video_id)

        video = db.scalar(select(Video).where(Video.id == vid_uuid))
        if not video:
            logger.error("Video %s not found", video_id)
            return {"status": "failed", "reason": "video_not_found"}

        # Idempotency check
        existing_set = db.scalar(
            select(SegmentSet).where(
                SegmentSet.video_id == vid_uuid,
                SegmentSet.version_no == 1,
            )
        )
        if existing_set and video.status == VideoStatus.analyzed:
            logger.info("Video %s already analyzed – skipping", video_id)
            return {"status": "skipped"}

        # Find subtitle asset
        subtitle_asset = db.scalar(
            select(VideoAsset).where(
                VideoAsset.video_id == vid_uuid,
                VideoAsset.asset_type == "subtitle_file",
            )
        )
        if not subtitle_asset or not os.path.exists(subtitle_asset.storage_path):
            logger.warning("No subtitle file for video %s", video_id)
            video.status = VideoStatus.failed
            db.commit()
            return {"status": "failed", "reason": "no_subtitle"}

        # Parse subtitle
        cues = _parse_subtitle(subtitle_asset.storage_path)

        # Persist caption track + cues
        track = CaptionTrack(
            id=uuid.uuid4(),
            video_id=vid_uuid,
            language_code="ko",
            source="uploaded",
            is_default=True,
        )
        db.add(track)
        db.flush()

        for cue_data in cues:
            cue = CaptionCue(
                id=uuid.uuid4(),
                caption_track_id=track.id,
                seq_no=cue_data["seq_no"],
                start_ms=cue_data["start_ms"],
                end_ms=cue_data["end_ms"],
                text=cue_data["text"],
            )
            db.add(cue)

        # Auto-generate segment set
        seg_data_list = _generate_segments_from_cues(cues)
        segment_set = SegmentSet(
            id=uuid.uuid4(),
            video_id=vid_uuid,
            version_no=1,
            status=SegmentSetStatus.draft,
            source="auto",
            created_by=None,
        )
        db.add(segment_set)
        db.flush()

        for seg_data in seg_data_list:
            seg = Segment(
                id=uuid.uuid4(),
                segment_set_id=segment_set.id,
                seq_no=seg_data["seq_no"],
                start_ms=seg_data["start_ms"],
                end_ms=seg_data["end_ms"],
                title=seg_data["title"],
                source_type=seg_data["source_type"],
            )
            db.add(seg)

        # Update video status
        video.status = VideoStatus.analyzed
        video.analyzed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Video %s analyzed: %d cues → %d segments",
            video_id,
            len(cues),
            len(seg_data_list),
        )
        return {"status": "success", "segment_count": len(seg_data_list)}

    except Exception as exc:
        logger.exception("Error analyzing video %s: %s", video_id, exc)
        if db:
            try:
                from models.core import Video, VideoStatus
                video = db.scalar(select(Video).where(Video.id == uuid.UUID(video_id)))
                if video:
                    video.status = VideoStatus.failed
                    db.commit()
            except Exception:
                pass
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()
