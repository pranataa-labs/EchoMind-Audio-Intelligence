"""Test script to verify Whisper transcription and Intelligence pipeline."""

from echomind.audio import AudioProcessor
from echomind.stt import AudioTranscriber
from echomind.intelligence import MeetingAnalyzer

def test():
    audio_path = "sample_data/sample_meeting.wav"
    print("1. Checking audio info...")
    info = AudioProcessor.get_audio_info(audio_path)
    print(f"   Audio Duration: {info['duration']:.2f}s, Sample Rate: {info['sample_rate']}Hz")

    print("\n2. Initializing Whisper Transcriber ('tiny' model for fast test)...")
    transcriber = AudioTranscriber(model_size="tiny", device="cpu", compute_type="int8")
    
    print("3. Transcribing...")
    result = transcriber.transcribe(audio_path, language="en")
    print(f"   Detected language: {result.language} ({result.language_probability:.1%})")
    print(f"   Full text: {result.full_text}")

    print("\n4. Running Meeting Intelligence Analysis (Offline Mode)...")
    analyzer = MeetingAnalyzer()
    insight = analyzer.analyze_meeting(result.full_text)
    print(f"   Title: {insight.title}")
    print(f"   Executive Summary: {insight.executive_summary[:100]}...")
    print(f"   Action Items found: {len(insight.action_items)}")
    for item in insight.action_items:
        print(f"     - [{item.priority}] {item.task} (PIC: {item.pic}, Deadline: {item.deadline})")

    print("\nPipeline test passed successfully!")

if __name__ == "__main__":
    test()
