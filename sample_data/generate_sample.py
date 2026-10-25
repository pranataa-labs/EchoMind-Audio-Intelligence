"""Generate a realistic meeting audio sample using Windows SAPI TTS."""

import os
from pathlib import Path

SAMPLE_PATH = Path(__file__).resolve().parent / "sample_meeting.wav"

def generate_sample_audio(output_path: str = str(SAMPLE_PATH)):
    """Generate sample meeting wav file using Windows SAPI voice."""
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
        
        # Audio format constant: 39 = 44kHz 16Bit Stereo, 22 = 22kHz 16Bit Mono
        file_stream.Open(output_path, 3, False)
        speaker.AudioOutputStream = file_stream
        
        meeting_script = (
            "Good morning team, welcome to the sprint review meeting. "
            "First agenda: our machine learning model deployment is currently on track. "
            "However, we must finalize the budget allocation proposal before tomorrow at 5 PM. "
            "Sarah, please coordinate with the finance department to get their approval by Friday. "
            "John, you will be responsible for setting up the API endpoint monitoring by next Monday. "
            "Overall, the progress this week has been great and the client feedback is very positive. "
            "Let's wrap up this meeting and execute our respective tasks. Thank you everyone."
        )
        
        speaker.Speak(meeting_script)
        file_stream.Close()
        print(f"Sample audio created at: {output_path}")
        return True
    except Exception as e:
        print(f"Failed to generate TTS via SAPI: {e}")
        return False

if __name__ == "__main__":
    generate_sample_audio()
