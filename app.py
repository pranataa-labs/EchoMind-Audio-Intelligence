"""EchoMind - End-to-End Meeting & Audio Intelligence Platform UI."""

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
    page_title="EchoMind - Audio Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Shadcn Slate Aesthetic)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Metric Cards */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 0.625rem;
    padding: 1.25rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    margin-bottom: 1rem;
}
.metric-title {
    font-size: 0.8125rem;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.025em;
    margin-bottom: 0.25rem;
}
.metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
}
.metric-sub {
    font-size: 0.8125rem;
    color: #94a3b8;
    margin-top: 0.25rem;
}

/* Speaker Badge & Pills */
.speaker-pill {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    margin-right: 0.5rem;
}
.speaker-1 {
    background-color: #e0e7ff;
    color: #4338ca;
}
.speaker-2 {
    background-color: #fce7f3;
    color: #be185d;
}
.speaker-3 {
    background-color: #dcfce7;
    color: #15803d;
}

/* Transcript Row */
.transcript-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.625rem;
    padding: 0.875rem 1.125rem;
    margin-bottom: 0.625rem;
}
.timestamp-tag {
    font-size: 0.75rem;
    font-family: monospace;
    color: #64748b;
    margin-left: 0.5rem;
}

/* Badges for priority */
.badge-high {
    background: #ffe4e6;
    color: #e11d48;
    padding: 0.2rem 0.5rem;
    border-radius: 0.375rem;
    font-weight: 600;
    font-size: 0.75rem;
}
.badge-medium {
    background: #fef3c7;
    color: #d97706;
    padding: 0.2rem 0.5rem;
    border-radius: 0.375rem;
    font-weight: 600;
    font-size: 0.75rem;
}
.badge-low {
    background: #dcfce7;
    color: #16a34a;
    padding: 0.2rem 0.5rem;
    border-radius: 0.375rem;
    font-weight: 600;
    font-size: 0.75rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session State Initialization
if "transcript_result" not in st.session_state:
    st.session_state.transcript_result = None
if "meeting_insight" not in st.session_state:
    st.session_state.meeting_insight = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

# Sidebar Configuration
with st.sidebar:
    st.title("🎙️ EchoMind")
    st.caption("Meeting & Audio Intelligence")
    st.divider()

    st.subheader("⚙️ Konfigurasi Model")
    model_size = st.selectbox(
        "Whisper STT Model",
        ["tiny", "base", "small", "medium"],
        index=1,
        help="Model 'base' seimbang antara kecepatan dan akurasi di CPU. Gunakan 'tiny' untuk kecepatan maksimal."
    )
    
    num_speakers = st.slider("Estimasi Jumlah Pembicara", min_value=1, max_value=4, value=2)
    
    language_choice = st.selectbox(
        "Bahasa Audio",
        ["auto", "id", "en"],
        format_func=lambda x: "Otomatis (Auto-Detect)" if x == "auto" else ("Bahasa Indonesia" if x == "id" else "English"),
        index=0
    )

    st.divider()
    st.subheader("🔑 Multimodal Reasoning")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=GEMINI_API_KEY,
        type="password",
        help="Dapatkan gratis di aistudio.google.com. Jika kosong, EchoMind menggunakan Offline Heuristic Engine."
    )

    if api_key_input:
        st.success("🟢 Gemini 2.5 Flash Aktif", icon="✅")
    else:
        st.info("⚪ Mode Offline Heuristik Aktif", icon="ℹ️")

    st.divider()
    st.caption("Dibuat untuk Pranataa Lab • Machine Learning")

# Main Content Header
col_header, col_sample = st.columns([4, 1.2])
with col_header:
    st.markdown("## 🎙️ **EchoMind** Platform")
    st.write("Transkripsi percakapan super cepat, ekstraksi action items otomatis, dan analisis rapat berbasis AI.")

sample_audio_file = SAMPLES_DIR / "sample_meeting.wav"
with col_sample:
    if sample_audio_file.exists():
        if st.button("▶️ Pakai Sample Audio Demo", use_container_width=True):
            st.session_state.audio_path = str(sample_audio_file)
            st.session_state.transcript_result = None
            st.session_state.meeting_insight = None
            st.session_state.chat_history = []
            st.rerun()

# Audio Upload Section
uploaded_file = st.file_uploader(
    "Unggah rekaman audio pertemuan (.mp3, .wav, .m4a, .ogg)",
    type=["mp3", "wav", "m4a", "ogg", "flac"]
)

if uploaded_file is not None:
    # Save to temp
    suffix = Path(uploaded_file.name).suffix or ".wav"
    temp_path = AudioProcessor.save_upload_to_temp(uploaded_file, suffix=suffix)
    if st.session_state.audio_path != temp_path:
        st.session_state.audio_path = temp_path
        st.session_state.transcript_result = None
        st.session_state.meeting_insight = None
        st.session_state.chat_history = []

# If Audio is Ready
if st.session_state.audio_path:
    st.audio(st.session_state.audio_path)
    
    # Process Button
    if st.session_state.transcript_result is None:
        if st.button("🚀 Mulai Transkripsi & Analisis Cerdas", type="primary"):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(pct: float, msg: str):
                progress_bar.progress(pct)
                status_text.text(msg)

            # Step 1: STT
            transcriber = AudioTranscriber(model_size=model_size, device="cpu", compute_type="int8")
            transcript_res = transcriber.transcribe(
                st.session_state.audio_path,
                language=language_choice,
                progress_callback=update_progress,
                num_speakers=num_speakers
            )
            st.session_state.transcript_result = transcript_res

            # Step 2: Intelligence Analysis
            status_text.text("Menjalankan analisis meeting intelligence...")
            analyzer = MeetingAnalyzer(api_key=api_key_input)
            insight = analyzer.analyze_meeting(transcript_res.full_text)
            st.session_state.meeting_insight = insight

            status_text.empty()
            progress_bar.empty()
            st.rerun()

# Display Results if Available
if st.session_state.transcript_result and st.session_state.meeting_insight:
    res = st.session_state.transcript_result
    insight = st.session_state.meeting_insight

    st.divider()

    # KPI Metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Durasi Audio</div>
            <div class="metric-value">{format_timestamp(res.duration_seconds)}</div>
            <div class="metric-sub">{res.duration_seconds:.1f} detik total</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        words = sum(len(seg.text.split()) for seg in res.segments)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Jumlah Kata</div>
            <div class="metric-value">{words}</div>
            <div class="metric-sub">{len(res.segments)} segmen tuturan</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Bahasa Terdeteksi</div>
            <div class="metric-value">{res.language.upper()}</div>
            <div class="metric-sub">Confidence: {res.language_probability:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Action Items</div>
            <div class="metric-value">{len(insight.action_items)}</div>
            <div class="metric-sub">Sentimen: {insight.overall_sentiment}</div>
        </div>
        """, unsafe_allow_html=True)

    # Tabs Interface
    tab_summary, tab_actions, tab_transcript, tab_qa, tab_sentiment = st.tabs([
        "📌 Ringkasan Eksekutif",
        "✅ Action Items",
        "🎙️ Transkrip Percakapan",
        "💬 Tanya Rapat (Q&A)",
        "📊 Analisis Sentimen & Topik"
    ])

    # Tab 1: Summary
    with tab_summary:
        st.markdown(f"### {insight.title}")
        st.markdown(insight.executive_summary)
        
        if insight.decisions_made:
            st.markdown("#### 🤝 Keputusan Utama yang Disepakati")
            for dec in insight.decisions_made:
                st.markdown(f"- **{dec}**")

        st.divider()
        report_md = export_report_markdown(res, insight)
        st.download_button(
            label="📥 Unduh Laporan Lengkap (.md)",
            data=report_md,
            file_name="laporan_rapat_echomind.md",
            mime="text/markdown"
        )

    # Tab 2: Action Items
    with tab_actions:
        st.markdown("### 📋 Daftar Tugas & Tindak Lanjut")
        if insight.action_items:
            df = action_items_to_dataframe(insight.action_items)
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Action Items (.csv)",
                data=csv,
                file_name="action_items.csv",
                mime="text/csv"
            )
        else:
            st.info("Tidak ada action item spesifik yang terdeteksi.")

    # Tab 3: Transcript Viewer
    with tab_transcript:
        st.markdown("### 📜 Transkrip Tersinkronisasi")
        for seg in res.segments:
            speaker_class = "speaker-1" if "1" in seg.speaker else ("speaker-2" if "2" in seg.speaker else "speaker-3")
            start_fmt = format_timestamp(seg.start)
            end_fmt = format_timestamp(seg.end)
            
            st.markdown(f"""
            <div class="transcript-box">
                <span class="speaker-pill {speaker_class}">{seg.speaker}</span>
                <span class="timestamp-tag">{start_fmt} - {end_fmt}</span>
                <div style="margin-top: 0.35rem; color: #1e293b; font-size: 0.9375rem;">
                    {seg.text}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 4: Interactive Q&A
    with tab_qa:
        st.markdown("### 💬 Tanya Jawab Mengenai Rapat Ini")
        st.caption("Ajukan pertanyaan bebas tentang keputusan, siapa yang ditugaskan, atau poin spesifik.")

        for q, a in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant"):
                st.write(a)

        user_query = st.chat_input("Contoh: Apa tugas yang diberikan kepada Sarah?")
        if user_query:
            with st.chat_message("user"):
                st.write(user_query)
            
            analyzer = MeetingAnalyzer(api_key=api_key_input)
            with st.spinner("Mencari jawaban dari rekaman..."):
                answer = analyzer.answer_question(res.full_text, user_query)
            
            with st.chat_message("assistant"):
                st.write(answer)
            st.session_state.chat_history.append((user_query, answer))

    # Tab 5: Sentiment & Topics
    with tab_sentiment:
        st.markdown("### 📊 Analisis Nada & Topik Pertemuan")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("#### Topik Utama")
            for t in insight.key_topics:
                st.markdown(f"- {t}")

        with col_s2:
            st.markdown("#### Indikator Emosi & Suasana")
            st.metric("Skor Sentimen Keseluruhan", f"{insight.sentiment_score:+0.2f}", insight.overall_sentiment)
            
            if insight.key_moments:
                st.markdown("##### Momen Kunci")
                for m in insight.key_moments:
                    st.markdown(f"⏱️ `{m.timestamp}`: **{m.tone}** — *\"{m.quote}\"*")
