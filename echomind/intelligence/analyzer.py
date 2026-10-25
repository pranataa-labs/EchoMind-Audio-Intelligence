"""Multimodal meeting intelligence analyzer supporting Gemini 2.5 Flash and offline fallback."""

import json
import logging
import re
from typing import Optional, Dict, Any, List

from echomind.schemas import MeetingInsight, ActionItem, SentimentMoment
from echomind.intelligence.prompts import INSIGHT_SYSTEM_PROMPT, QA_SYSTEM_PROMPT
from echomind.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


class MeetingAnalyzer:
    """Extracts executive summaries, action items, sentiment, and answers Q&A."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = GEMINI_MODEL):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")

    def analyze_meeting(self, transcript_text: str) -> MeetingInsight:
        """Generate structured insights from transcript text."""
        if self._client:
            try:
                return self._analyze_with_gemini(transcript_text)
            except Exception as e:
                logger.error(f"Gemini API analysis failed: {e}. Falling back to offline analyzer.")

        return self._analyze_offline(transcript_text)

    def _analyze_with_gemini(self, transcript_text: str) -> MeetingInsight:
        """Call Gemini 2.5 Flash to generate structured MeetingInsight."""
        prompt = f"""Berikut adalah transkrip lengkap pertemuan:

{transcript_text}

Silakan analisis transkrip di atas sesuai instruksi sistem dan berikan respons HANYA dalam format JSON."""

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "system_instruction": INSIGHT_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "temperature": 0.2,
            }
        )

        response_text = response.text.strip()
        # Clean json backticks if any
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        data = json.loads(response_text.strip())
        return MeetingInsight(**data)

    def _analyze_offline(self, transcript_text: str) -> MeetingInsight:
        """Smart rule-based & extractive fallback when API key is unavailable."""
        lines = [line.strip() for line in transcript_text.split("\n") if line.strip()]
        
        # 1. Extractive Summary
        summary_lines = lines[:min(5, len(lines))]
        clean_summary = " ".join([re.sub(r"^\[.*?\]\s*(\(.*?\))?:\s*", "", l) for l in summary_lines])
        executive_summary = f"Rangkuman Ekstraktif (Mode Offline):\nPertemuan membahas beberapa poin utama berikut:\n{clean_summary}"

        # 2. Heuristic Action Item Extraction (Supports Indonesian & English)
        action_keywords = [
            # Indonesian
            "harus", "perlu", "akan", "tolong", "deadline", "tugaskan", "disiapkan", "selesaikan", "kirim", "koordinasi",
            # English
            "must", "please", "coordinate", "responsible", "finalize", "submit", "prepare", "deliver", "review"
        ]
        action_items: List[ActionItem] = []

        for line in lines:
            lower = line.lower()
            # Skip pure greetings or wraps
            if any(skip in lower for skip in ["welcome to", "thank you", "good morning", "good afternoon", "selamat pagi", "terima kasih"]):
                continue

            if any(k in lower for k in action_keywords):
                # Guess speaker
                speaker_match = re.search(r"\[(Speaker \d+)\]", line)
                speaker = speaker_match.group(1) if speaker_match else "Tim"
                clean_task = re.sub(r"^\[.*?\]\s*(\(.*?\))?:\s*", "", line)
                
                # Try to extract name if mentioned e.g., "Sarah, please...", "John, you will..."
                pic_candidate = speaker
                name_match = re.match(r"^([A-Z][a-z]+)[,\s]+(please|must|will|you)", clean_task)
                if name_match:
                    pic_candidate = name_match.group(1)

                # Priority heuristic
                priority = "Medium"
                if any(w in lower for w in ["must", "urgent", "harus", "segera", "asap"]):
                    priority = "High"
                elif any(w in lower for w in ["optional", "bila sempat", "low"]):
                    priority = "Low"

                action_items.append(
                    ActionItem(
                        task=clean_task[:150],
                        pic=pic_candidate,
                        deadline="Next Milestone",
                        priority=priority,
                        context="Terdeteksi dari instruksi pembicara"
                    )
                )

        if not action_items:
            action_items.append(
                ActionItem(
                    task="Review berkala transkrip pertemuan",
                    pic="Seluruh Tim",
                    deadline="Akhir Pekan",
                    priority="Low",
                    context="Inisiatif tindak lanjut umum"
                )
            )

        # 3. Simple sentiment estimation
        positive_words = ["bagus", "setuju", "mantap", "hebat", "terima kasih", "sukses", "ok", "siap", "baik"]
        negative_words = ["masalah", "kendala", "sulit", "terlambat", "gagal", "kecewa", "bingung", "batal"]
        
        text_lower = transcript_text.lower()
        pos_count = sum(text_lower.count(w) for w in positive_words)
        neg_count = sum(text_lower.count(w) for w in negative_words)
        
        total = pos_count + neg_count + 1
        score = (pos_count - neg_count) / total

        overall_sentiment = "Positive" if score > 0.1 else ("Constructive/Tense" if score < -0.1 else "Neutral")

        return MeetingInsight(
            title="Analisis Rapat (Offline Mode)",
            executive_summary=executive_summary,
            key_topics=["Diskusi Tim", "Evaluasi Agenda", "Rencana Tindak Lanjut"],
            action_items=action_items[:8],
            overall_sentiment=overall_sentiment,
            sentiment_score=round(score, 2),
            key_moments=[
                SentimentMoment(timestamp="00:00", tone=overall_sentiment, quote="Awal diskusi rapat")
            ],
            decisions_made=[
                "Melanjutkan kesepakatan sesuai pembagian tugas di transkrip",
                "Koordinasi lanjutan via chat/email"
            ]
        )

    def answer_question(self, transcript_text: str, question: str) -> str:
        """Answer an interactive query about the meeting."""
        if self._client:
            try:
                prompt = f"""Transkrip Rapat:
{transcript_text}

Pertanyaan Pengguna:
{question}"""
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "system_instruction": QA_SYSTEM_PROMPT,
                        "temperature": 0.3,
                    }
                )
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini Q&A failed: {e}")

        # Offline fallback matching
        q_words = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 3]
        matches = []
        for line in transcript_text.split("\n"):
            if any(w in line.lower() for w in q_words):
                matches.append(line)

        if matches:
            return "Berdasarkan transkrip (Mode Offline), ditemukan bagian terkait:\n\n" + "\n\n".join(f"- {m}" for m in matches[:4])
        return "Mohon maaf, dalam mode offline saya tidak menemukan kecocokan kata kunci terkait pertanyaan tersebut dalam transkrip. Anda dapat mengaktifkan Gemini API Key untuk pemahaman kontekstual mendalam."
