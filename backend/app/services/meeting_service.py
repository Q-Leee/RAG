import logging
from pathlib import Path

from app.config import settings
from app.models.schemas import ActionItem, MeetingSummaryResponse
from app.services import llm
from app.services.document_extract import SUPPORTED_EXTENSIONS, extract_text_from_file

logger = logging.getLogger(__name__)


def extract_text_from_upload(path: Path, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return extract_text_from_file(path, filename)
    raise ValueError(f"Unsupported file type: {ext}")


def summarize_meeting_text(text: str, *, use_llm: bool) -> MeetingSummaryResponse:
    cleaned = " ".join(text.split())
    if not cleaned:
        return MeetingSummaryResponse(
            summary="No text content found.",
            action_items=[],
            raw_transcript_length=0,
        )

    summary = cleaned[:800] + ("..." if len(cleaned) > 800 else "")
    action_items: list[ActionItem] = []

    if use_llm and settings.llm_enabled:
        raw = llm.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Summarize meeting notes. Respond with ONLY valid JSON: "
                        '{"summary": string (3-6 sentences), "action_items": '
                        '[{"task": string, "owner": string or null, "due": string or null}]}'
                    ),
                },
                {"role": "user", "content": cleaned[:12000]},
            ]
        )
        parsed = llm.extract_json_block(raw or "")
        if parsed:
            summary = parsed.get("summary") or summary
            for item in parsed.get("action_items") or []:
                if isinstance(item, dict) and item.get("task"):
                    action_items.append(
                        ActionItem(
                            task=str(item["task"]),
                            owner=item.get("owner"),
                            due=item.get("due"),
                        )
                    )

    return MeetingSummaryResponse(
        summary=summary,
        action_items=action_items,
        raw_transcript_length=len(cleaned),
    )
