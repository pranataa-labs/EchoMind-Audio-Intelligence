"""Helper utilities for time formatting, exports, and styling."""

import io
import pandas as pd
from typing import List
from echomind.schemas import TranscriptResult, MeetingInsight, ActionItem


def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def action_items_to_dataframe(action_items: List[ActionItem]) -> pd.DataFrame:
    """Convert action items to pandas DataFrame."""
    if not action_items:
        return pd.DataFrame(columns=["Tugas", "PIC", "Deadline", "Prioritas", "Konteks"])
    
    data = []
    for item in action_items:
        data.append({
            "Tugas": item.task,
            "PIC": item.pic,
            "Deadline": item.deadline,
            "Prioritas": item.priority,
            "Konteks": item.context or "-"
        })
    return pd.DataFrame(data)


def export_report_markdown(transcript: TranscriptResult, insight: MeetingInsight) -> str:
    """Generate a clean markdown report of the meeting."""
    md = [
        f"# {insight.title}",
        f"\n**Durasi:** {format_timestamp(transcript.duration_seconds)} | **Bahasa:** {transcript.language.upper()} | **Sentimen:** {insight.overall_sentiment}",
        "\n---",
        "\n## 📌 Ringkasan Eksekutif",
        f"{insight.executive_summary}",
        "\n## 🎯 Topik Utama",
    ]
    for topic in insight.key_topics:
        md.append(f"- {topic}")

    md.append("\n## ✅ Daftar Action Items")
    md.append("| No | Tugas | PIC | Deadline | Prioritas |")
    md.append("|---|---|---|---|---|")
    for i, item in enumerate(insight.action_items, 1):
        md.append(f"| {i} | {item.task} | {item.pic} | {item.deadline} | {item.priority} |")

    if insight.decisions_made:
        md.append("\n## 🤝 Keputusan yang Disepakati")
        for decision in insight.decisions_made:
            md.append(f"- {decision}")

    md.append("\n## 📝 Transkrip Lengkap")
    for seg in transcript.segments:
        start_fmt = format_timestamp(seg.start)
        end_fmt = format_timestamp(seg.end)
        md.append(f"**[{seg.speaker}]** `{start_fmt} - {end_fmt}`: {seg.text}\n")

    return "\n".join(md)
