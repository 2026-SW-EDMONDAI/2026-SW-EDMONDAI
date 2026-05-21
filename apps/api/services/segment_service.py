import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.exceptions import AppException
from models.segment import Segment, SegmentSet, SegmentSetStatus


class SegmentService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- SegmentSet ----------

    def _get_set(self, video_id: uuid.UUID, set_id: uuid.UUID) -> SegmentSet:
        ss = self.db.scalar(
            select(SegmentSet).where(SegmentSet.id == set_id, SegmentSet.video_id == video_id)
        )
        if not ss:
            raise AppException(code="NOT_FOUND", message="Segment set not found.", status_code=404)
        return ss

    def list_sets(self, video_id: uuid.UUID) -> list[SegmentSet]:
        return list(
            self.db.scalars(
                select(SegmentSet)
                .where(SegmentSet.video_id == video_id)
                .order_by(SegmentSet.version_no)
            ).all()
        )

    def get_latest_set(self, video_id: uuid.UUID) -> SegmentSet:
        ss = self.db.scalar(
            select(SegmentSet)
            .where(SegmentSet.video_id == video_id)
            .order_by(SegmentSet.version_no.desc())
        )
        if not ss:
            raise AppException(code="NOT_FOUND", message="No segment set found.", status_code=404)
        return ss

    def clone_set(
        self, video_id: uuid.UUID, set_id: uuid.UUID, created_by: uuid.UUID, notes: str | None
    ) -> SegmentSet:
        source = self._get_set(video_id, set_id)

        max_version = self.db.scalar(
            select(func.max(SegmentSet.version_no)).where(SegmentSet.video_id == video_id)
        ) or 0

        new_set = SegmentSet(
            id=uuid.uuid4(),
            video_id=video_id,
            version_no=max_version + 1,
            status=SegmentSetStatus.draft,
            created_by=created_by,
            source="hybrid",
            notes=notes,
        )
        self.db.add(new_set)
        self.db.flush()

        # Copy segments
        for seg in source.segments:
            new_seg = Segment(
                id=uuid.uuid4(),
                segment_set_id=new_set.id,
                seq_no=seg.seq_no,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                title=seg.title,
                topic=seg.topic,
                key_concepts=seg.key_concepts,
                summary=seg.summary,
                source_type=seg.source_type,
            )
            self.db.add(new_seg)

        self.db.commit()
        self.db.refresh(new_set)
        return new_set

    def finalize_set(self, video_id: uuid.UUID, set_id: uuid.UUID) -> SegmentSet:
        ss = self._get_set(video_id, set_id)
        if ss.status != SegmentSetStatus.draft:
            raise AppException(
                code="SEGMENT_SET_NOT_DRAFT",
                message="Only draft segment sets can be finalized.",
                status_code=409,
                details={"segmentSetId": str(set_id)},
            )
        ss.status = SegmentSetStatus.finalized
        self.db.commit()
        self.db.refresh(ss)
        return ss

    # ---------- Segments ----------

    def _get_segment(self, set_id: uuid.UUID, seg_id: uuid.UUID) -> Segment:
        seg = self.db.scalar(
            select(Segment).where(Segment.id == seg_id, Segment.segment_set_id == set_id)
        )
        if not seg:
            raise AppException(code="NOT_FOUND", message="Segment not found.", status_code=404)
        return seg

    def _require_draft(self, ss: SegmentSet) -> None:
        if ss.status != SegmentSetStatus.draft:
            raise AppException(
                code="SEGMENT_SET_NOT_DRAFT",
                message="Only draft segment sets can be edited.",
                status_code=409,
                details={"segmentSetId": str(ss.id)},
            )

    def list_segments(self, set_id: uuid.UUID) -> list[Segment]:
        return list(
            self.db.scalars(
                select(Segment)
                .where(Segment.segment_set_id == set_id)
                .order_by(Segment.seq_no)
            ).all()
        )

    def update_segment(
        self,
        video_id: uuid.UUID,
        set_id: uuid.UUID,
        seg_id: uuid.UUID,
        title: str | None,
        topic: str | None,
        key_concepts: list | None,
        summary: str | None,
    ) -> Segment:
        ss = self._get_set(video_id, set_id)
        self._require_draft(ss)
        seg = self._get_segment(set_id, seg_id)

        if title is not None:
            seg.title = title
        if topic is not None:
            seg.topic = topic
        if key_concepts is not None:
            seg.key_concepts = key_concepts
        if summary is not None:
            seg.summary = summary
        seg.source_type = "edited"
        self.db.commit()
        self.db.refresh(seg)
        return seg

    def split_segment(
        self, video_id: uuid.UUID, set_id: uuid.UUID, seg_id: uuid.UUID, split_at_ms: int
    ) -> tuple[Segment, Segment]:
        ss = self._get_set(video_id, set_id)
        self._require_draft(ss)
        seg = self._get_segment(set_id, seg_id)

        if not (seg.start_ms < split_at_ms < seg.end_ms):
            raise AppException(
                code="INVALID_SPLIT_POSITION",
                message="splitAtMs must be within the segment range.",
                status_code=422,
                details={"startMs": seg.start_ms, "endMs": seg.end_ms, "splitAtMs": split_at_ms},
            )

        # Shift seq_no for segments after this one
        later_segs = self.db.scalars(
            select(Segment)
            .where(Segment.segment_set_id == set_id, Segment.seq_no > seg.seq_no)
            .order_by(Segment.seq_no.desc())
        ).all()
        for later in later_segs:
            later.seq_no += 1

        original_end = seg.end_ms
        seg.end_ms = split_at_ms
        seg.source_type = "edited"

        new_seg = Segment(
            id=uuid.uuid4(),
            segment_set_id=set_id,
            seq_no=seg.seq_no + 1,
            start_ms=split_at_ms,
            end_ms=original_end,
            title=f"{seg.title} (2)",
            topic=seg.topic,
            key_concepts=seg.key_concepts,
            summary=None,
            source_type="edited",
        )
        self.db.add(new_seg)
        self.db.commit()
        self.db.refresh(seg)
        self.db.refresh(new_seg)
        return seg, new_seg

    def merge_segments(
        self, video_id: uuid.UUID, set_id: uuid.UUID, segment_ids: list[uuid.UUID]
    ) -> Segment:
        ss = self._get_set(video_id, set_id)
        self._require_draft(ss)

        if len(segment_ids) < 2:
            raise AppException(
                code="INVALID_MERGE",
                message="At least two segments are required to merge.",
                status_code=422,
            )

        segs = [self._get_segment(set_id, sid) for sid in segment_ids]
        segs.sort(key=lambda s: s.seq_no)

        # Validate contiguous
        for i in range(1, len(segs)):
            if segs[i].seq_no != segs[i - 1].seq_no + 1:
                raise AppException(
                    code="SEGMENT_MERGE_NOT_CONTIGUOUS",
                    message="Only contiguous segments can be merged.",
                    status_code=422,
                )

        first = segs[0]
        merged_end = segs[-1].end_ms
        first.end_ms = merged_end
        first.title = f"{first.title} (merged)"
        first.source_type = "edited"

        # Remove merged segments and shift seq_no
        for seg in segs[1:]:
            self.db.delete(seg)

        self.db.flush()

        # Re-number remaining segments after merge
        remaining = list(
            self.db.scalars(
                select(Segment)
                .where(Segment.segment_set_id == set_id)
                .order_by(Segment.seq_no)
            ).all()
        )
        for idx, seg in enumerate(remaining, start=1):
            seg.seq_no = idx

        self.db.commit()
        self.db.refresh(first)
        return first
