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
                        "You are a professional meeting assistant. Analyze the transcript and extract a high-quality summary and action items.\n"
                        "CRITICAL: Write the summary and action items in the EXACT SAME language as the input transcript. If the transcript is in Korean, write in Korean (한국어). If the transcript is in English, write in English.\n"
                        "WARNING: NEVER output in Chinese (중국어) unless the input transcript is in Chinese. Under no circumstances should you summarize a Korean/English transcript in Chinese.\n"
                        "Respond ONLY with a valid JSON object of this structure (no markdown text outside the JSON):\n"
                        "{\n"
                        '  "summary": "Concise summary in the same language as the transcript.",\n'
                        '  "action_items": [\n'
                        '    {"task": "Task description in the same language as the transcript", "owner": "Name or null", "due": "Due date or null"}\n'
                        '  ]\n'
                        "}"
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
                            owner=str(item["owner"]) if item.get("owner") else None,
                            due=str(item["due"]) if item.get("due") else None,
                        )
                    )

    return MeetingSummaryResponse(
        summary=summary,
        action_items=action_items,
        raw_transcript_length=len(cleaned),
    )
