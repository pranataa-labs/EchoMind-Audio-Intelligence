"""EchoMind - End-to-End Meeting & Audio Intelligence Platform.
Designed with Pranataa's Shadcn-Admin Design System (Slate palette, Inter, 0.625rem radius).
Fully adaptive for both Light and Dark modes.
"""

import os
import streamlit as st
import pandas as pd
from pathlib import Path

from echomind.config import DEFAULT_WHISPER_MODEL, GEMINI_API_KEY, SAMPLES_DIR
from echomind.audio import AudioProcessor
from echomind.stt import AudioTranscriber
from echomind.intelligence import MeetingAnalyzer
from echomind.utils import format_timestamp, action_items_to_dataframe, export_report_markdown

# Page configuration
st.set_page_config(
    page_title="EchoMind | Audio Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Shadcn-Admin Slate Design System - Dark & Light Adaptive)
SHADCN_SLATE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --card-bg: rgba(255, 255, 255, 0.95);
    --card-border: #e2e8f0;
    --text-title: #0f172a;
    --text-body: #1e293b;
    --text-muted: #64748b;
    --pill-bg: #f1f5f9;
    --pill-text: #0f172a;
    --pill-border: #cbd5e1;
    --radius: 0.625rem;
}

/* Dark Mode detection via media query & Streamlit theme */
@media (prefers-color-scheme: dark) {
    :root {
        --card-bg: #0b1120;
        --card-border: #1e293b;
        --text-title: #f8fafc;
        --text-body: #e2e8f0;
        --text-muted: #94a3b8;
        --pill-bg: #1e293b;
        --pill-text: #f8fafc;
        --pill-border: #334155;
    }
}

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: var(--font-sans) !important;
}

/* Header styling */
.header-wrapper {
    padding-bottom: 1.25rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--card-border);
}
.header-breadcrumb {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.375rem;
}
.header-title {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: var(--text-title);
    margin: 0;
    line-height: 1.2;
}
.header-subtitle {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

/* KPI Metric Cards (Satnaing / Shadcn-Admin Pattern) */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
@media (max-width: 900px) {
    .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 600px) {
    .kpi-grid {
        grid-template-columns: 1fr;
    }
}

.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 1.25rem 1.25rem 1rem 1.25rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    transition: border-color 0.15s ease;
}
.kpi-card:hover {
    border-color: #94a3b8;
}
.kpi-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.5rem;
}
.kpi-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}
.kpi-icon {
    font-size: 1.1rem;
}
.kpi-value {
    font-size: 1.625rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-title);
    line-height: 1.2;
}
.kpi-desc {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.35rem;
}

/* Audio Preview Box */
.audio-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    margin-bottom: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
.audio-meta-row {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    font-size: 0.8125rem;
    color: var(--text-muted);
    flex-wrap: wrap;
}
.audio-meta-item strong {
    color: var(--text-title);
    font-weight: 600;
}

/* Transcript Dialog Rows */
.transcript-item {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    margin-bottom: 0.625rem;
    transition: background-color 0.1s ease;
}
.transcript-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.35rem;
}
.speaker-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.15rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    letter-spacing: 0.02em;
}
.speaker-1 {
    background: var(--pill-bg);
    color: var(--pill-text);
    border: 1px solid var(--pill-border);
}
.speaker-2 {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}
.speaker-3 {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.timestamp-pill {
    font-size: 0.75rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: var(--text-muted);
    background: var(--pill-bg);
    padding: 0.15rem 0.5rem;
    border-radius: 0.375rem;
}
.transcript-text {
    font-size: 0.9375rem;
    line-height: 1.6;
    color: var(--text-body);
}

/* Priority Badges (Outline Badge + Subtle Tint) */
.badge-priority-high {
    display: inline-block;
    background: rgba(244, 63, 94, 0.12);
    color: #f43f5e;
    border: 1px solid rgba(244, 63, 94, 0.3);
    border-radius: 0.375rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-priority-medium {
    display: inline-block;
    background: rgba(245, 158, 11, 0.12);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 0.375rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-priority-low {
    display: inline-block;
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 0.375rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Clean Button Styling */
div.stButton > button {
    border-radius: 0.5rem !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
}

/* Tab Headers */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--card-border);
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-muted);
    padding: 0.5rem 0.875rem;
    border-radius: 0.375rem 0.375rem 0 0;
}
.stTabs [aria-selected="true"] {
    color: var(--text-title) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #3b82f6 !important;
}
</style>
"""
st.markdown(SHADCN_SLATE_CSS, unsafe_allow_html=True)

# Session State Keys Initialization
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "current_file_signature" not in st.session_state:
    st.session_state.current_file_signature = None
if "audio_info" not in st.session_state:
    st.session_state.audio_info = None
if "transcript_result" not in st.session_state:
    st.session_state.transcript_result = None
if "meeting_insight" not in st.session_state:
    st.session_state.meeting_insight = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar Configuration
with st.sidebar:
    st.markdown("### 🎙️ **EchoMind**")
    st.caption("Meeting & Conversation Intelligence")
    st.markdown("---")

    st.markdown("#### ⚙️ Pengaturan Engine")
    
    model_size = st.selectbox(
        "Whisper STT Model",
        ["tiny", "base", "small", "medium"],
        index=0,  # Default to 'tiny' for blazing fast CPU inference (<3s)
        help="'tiny': Sangat cepat (~2s, akurasi baik). 'base': Seimbang. 'small': Akurasi lebih tinggi."
    )
    
    num_speakers = st.slider("Estimasi Jumlah Pembicara", min_value=1, max_value=4, value=2)
    
    language_choice = st.selectbox(
        "Bahasa Audio",
        ["auto", "id", "en"],
        format_func=lambda x: "Otomatis (Auto-Detect)" if x == "auto" else ("Bahasa Indonesia" if x == "id" else "English"),
        index=0
    )

    st.markdown("---")
    st.markdown("#### 🔑 Multimodal Reasoning")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=GEMINI_API_KEY,
        type="password",
        help="Opsional. Jika kosong, sistem otomatis beralih ke Offline Heuristic Engine."
    )

    if api_key_input:
        st.success("🟢 Gemini 2.5 Flash Aktif", icon="✅")
    else:
        st.info("⚪ Offline Heuristic Engine Aktif", icon="ℹ️")

    st.markdown("---")
    st.caption("Pranataa Lab • Machine Learning v1.0.0")

# Header Section
st.markdown("""
<div class="header-wrapper">
    <div class="header-breadcrumb">
        <span>pranataa-lab</span>
        <span>/</span>
        <span>machine-learning</span>
        <span>/</span>
        <span style="font-weight: 600;">echomind</span>
    </div>
    <div>
        <h1 class="header-title">EchoMind Audio Intelligence</h1>
        <p class="header-subtitle">Transkripsi percakapan super cepat, deteksi pembicara, dan ekstraksi action items otomatis.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Action Toolbar (Upload & Demo Sample)
col_upload, col_demo = st.columns([3.2, 1.3])

sample_audio_file = SAMPLES_DIR / "sample_meeting.wav"

with col_demo:
    st.markdown("<div style='height: 1.6rem;'></div>", unsafe_allow_html=True)
    if sample_audio_file.exists():
        if st.button("▶️ Gunakan Sample Demo", use_container_width=True):
            st.session_state.audio_path = str(sample_audio_file)
            st.session_state.current_file_signature = "sample_meeting_demo"
            st.session_state.audio_info = AudioProcessor.get_audio_info(str(sample_audio_file))
            st.session_state.transcript_result = None
            st.session_state.meeting_insight = None
            st.session_state.chat_history = []
            st.rerun()

with col_upload:
    uploaded_file = st.file_uploader(
        "Pilih file audio rapat (.mp3, .wav, .m4a, .ogg, .flac)",
        type=["mp3", "wav", "m4a", "ogg", "flac"]
    )

# Robust Upload Handler (Avoids resetting on rerun)
if uploaded_file is not None:
    file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.current_file_signature != file_sig:
        suffix = Path(uploaded_file.name).suffix or ".wav"
        temp_path = AudioProcessor.save_upload_to_temp(
            uploaded_file,
            file_signature=file_sig,
            suffix=suffix
        )
        st.session_state.audio_path = temp_path
        st.session_state.current_file_signature = file_sig
        st.session_state.audio_info = AudioProcessor.get_audio_info(temp_path)
        st.session_state.transcript_result = None
        st.session_state.meeting_insight = None
        st.session_state.chat_history = []
        st.rerun()

# Audio Preview and Execution Trigger
if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
    info = st.session_state.audio_info or AudioProcessor.get_audio_info(st.session_state.audio_path)
    file_name = Path(st.session_state.audio_path).name
    dur_label = f"{format_timestamp(info.get('duration', 0.0))} ({info.get('duration', 0.0)}s)" if info.get('duration', 0.0) > 0 else "Dihitung saat proses"

    st.markdown(f"""
    <div class="audio-card">
        <div class="audio-meta-row">
            <span class="audio-meta-item">📁 File: <strong>{file_name}</strong></span>
            <span class="audio-meta-item">⏱️ Durasi: <strong>{dur_label}</strong></span>
            <span class="audio-meta-item">📦 Ukuran: <strong>{info.get('size_mb', 0.0)} MB</strong></span>
            <span class="audio-meta-item">🔊 Sample Rate: <strong>{info.get('sample_rate', 16000)} Hz</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Audio player
    st.audio(st.session_state.audio_path)

    # Trigger Process Button
    btn_col1, btn_col2 = st.columns([1.8, 3])
    with btn_col1:
        start_process = st.button("⚡ Proses Transkripsi & Analisis", type="primary", use_container_width=True)

    if start_process:
        progress_placeholder = st.empty()
        status_box = st.empty()

        def update_progress(pct: float, msg: str):
            progress_placeholder.progress(pct)
            status_box.caption(f"⏳ {msg}")

        try:
            update_progress(0.1, "Memuat engine Whisper STT...")
            transcriber = AudioTranscriber(model_size=model_size, device="cpu", compute_type="int8")
            
            transcript_res = transcriber.transcribe(
                st.session_state.audio_path,
                language=language_choice,
                progress_callback=update_progress,
                num_speakers=num_speakers
            )
            st.session_state.transcript_result = transcript_res

            update_progress(0.85, "Mengekstrak Action Items, Ringkasan & Sentimen...")
            analyzer = MeetingAnalyzer(api_key=api_key_input)
            insight = analyzer.analyze_meeting(transcript_res.full_text)
            st.session_state.meeting_insight = insight

            update_progress(1.0, "Proses selesai!")
            progress_placeholder.empty()
            status_box.empty()
            st.toast("Transkripsi dan analisis selesai!", icon="✅")
            st.rerun()

        except Exception as e:
            progress_placeholder.empty()
            status_box.empty()
            st.error(f"Terjadi kesalahan saat memproses audio: {e}")

# Display Intelligence Results
if st.session_state.transcript_result and st.session_state.meeting_insight:
    res = st.session_state.transcript_result
    insight = st.session_state.meeting_insight

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # KPI Metrics Section (Shadcn-Admin 4-Card Layout)
    total_words = sum(len(seg.text.split()) for seg in res.segments)
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Durasi Rekaman</span>
                <span class="kpi-icon">⏱️</span>
            </div>
            <div class="kpi-value">{format_timestamp(res.duration_seconds)}</div>
            <div class="kpi-desc">{res.duration_seconds:.1f} detik percakapan</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Total Kata</span>
                <span class="kpi-icon">📝</span>
            </div>
            <div class="kpi-value">{total_words}</div>
            <div class="kpi-desc">{len(res.segments)} giliran bicara terdeteksi</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Bahasa Utama</span>
                <span class="kpi-icon">🌐</span>
            </div>
            <div class="kpi-value">{res.language.upper()}</div>
            <div class="kpi-desc">Confidence score: {res.language_probability:.0%}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Action Items</span>
                <span class="kpi-icon">🎯</span>
            </div>
            <div class="kpi-value">{len(insight.action_items)} Tugas</div>
            <div class="kpi-desc">Sentimen: {insight.overall_sentiment}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabbed Interface
    tab_actions, tab_summary, tab_transcript, tab_qa, tab_sentiment = st.tabs([
        "📋 Action Items",
        "📌 Ringkasan Eksekutif",
        "🎙️ Transkrip Tersinkronisasi",
        "💬 Tanya Rapat (Q&A)",
        "📊 Sentimen & Analitik"
    ])

    # TAB 1: Action Items
    with tab_actions:
        st.markdown("#### 📋 Daftar Tugas & Tindak Lanjut")
        st.caption("Action items terdeteksi secara otomatis dari komitmen lisan pembicara.")

        if insight.action_items:
            table_rows = []
            for idx, item in enumerate(insight.action_items, 1):
                p_badge = "badge-priority-medium"
                if item.priority.lower() == "high":
                    p_badge = "badge-priority-high"
                elif item.priority.lower() == "low":
                    p_badge = "badge-priority-low"

                table_rows.append(f"""
                <tr style="border-bottom: 1px solid var(--card-border); font-size: 0.875rem;">
                    <td style="padding: 0.75rem 0.5rem; color: var(--text-muted); font-weight: 500;">{idx}</td>
                    <td style="padding: 0.75rem 0.5rem; color: var(--text-title); font-weight: 500;">{item.task}</td>
                    <td style="padding: 0.75rem 0.5rem;"><span style="background: var(--pill-bg); border: 1px solid var(--pill-border); padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; color: var(--text-body);">{item.pic}</span></td>
                    <td style="padding: 0.75rem 0.5rem; color: var(--text-muted);">{item.deadline}</td>
                    <td style="padding: 0.75rem 0.5rem;"><span class="{p_badge}">{item.priority}</span></td>
                </tr>
                """)

            st.markdown(f"""
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 1rem; text-align: left;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--card-border); font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">
                        <th style="padding: 0.5rem;">#</th>
                        <th style="padding: 0.5rem;">Tugas</th>
                        <th style="padding: 0.5rem;">PIC / Penanggung Jawab</th>
                        <th style="padding: 0.5rem;">Deadline</th>
                        <th style="padding: 0.5rem;">Prioritas</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(table_rows)}
                </tbody>
            </table>
            """, unsafe_allow_html=True)

            df = action_items_to_dataframe(insight.action_items)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Action Items (.csv)",
                data=csv,
                file_name="echomind_action_items.csv",
                mime="text/csv"
            )
        else:
            st.info("Tidak ada action items spesifik yang terdeteksi.")

    # TAB 2: Summary & Decisions
    with tab_summary:
        st.markdown(f"### {insight.title}")
        st.write(insight.executive_summary)

        if insight.decisions_made:
            st.markdown("#### 🤝 Kesepakatan Utama")
            for dec in insight.decisions_made:
                st.markdown(f"- **{dec}**")

        st.markdown("---")
        report_md = export_report_markdown(res, insight)
        st.download_button(
            label="📥 Unduh Laporan Eksekutif (.md)",
            data=report_md,
            file_name="laporan_rapat_echomind.md",
            mime="text/markdown"
        )

    # TAB 3: Synchronized Transcript Viewer
    with tab_transcript:
        st.markdown("#### 📜 Transkrip Tersinkronisasi")
        st.caption("Klik segmen untuk membaca dialog per penutur.")

        for seg in res.segments:
            speaker_cls = "speaker-1" if "1" in seg.speaker else ("speaker-2" if "2" in seg.speaker else "speaker-3")
            start_fmt = format_timestamp(seg.start)
            end_fmt = format_timestamp(seg.end)

            st.markdown(f"""
            <div class="transcript-item">
                <div class="transcript-meta">
                    <span class="speaker-pill {speaker_cls}">{seg.speaker}</span>
                    <span class="timestamp-pill">{start_fmt} - {end_fmt}</span>
                </div>
                <div class="transcript-text">{seg.text}</div>
            </div>
            """, unsafe_allow_html=True)

    # TAB 4: Q&A Chat
    with tab_qa:
        st.markdown("#### 💬 Asisten Tanya Jawab Rapat")
        st.caption("Ajukan pertanyaan apa pun seputar apa yang dibicarakan dalam rekaman.")

        for q, a in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant"):
                st.write(a)

        user_query = st.chat_input("Tanyakan sesuatu, misal: Apa deadline untuk Sarah?")
        if user_query:
            with st.chat_message("user"):
                st.write(user_query)

            analyzer = MeetingAnalyzer(api_key=api_key_input)
            with st.spinner("Mencari jawaban di transkrip..."):
                answer = analyzer.answer_question(res.full_text, user_query)

            with st.chat_message("assistant"):
                st.write(answer)
            st.session_state.chat_history.append((user_query, answer))

    # TAB 5: Sentiment & Topics
    with tab_sentiment:
        st.markdown("#### 📊 Analisis Sentimen & Topik Pembahasan")
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.markdown("##### 📌 Topik Utama")
            for t in insight.key_topics:
                st.markdown(f"- {t}")

        with col_t2:
            st.markdown("##### 🎭 Indikator Sentimen")
            st.metric(
                label="Skor Sentimen Rapat",
                value=f"{insight.sentiment_score:+0.2f}",
                delta=insight.overall_sentiment
            )

            if insight.key_moments:
                st.markdown("##### 🔍 Momen Kunci")
                for km in insight.key_moments:
                    st.markdown(f"⏱️ `{km.timestamp}`: **{km.tone}** — *\"{km.quote}\"*")
