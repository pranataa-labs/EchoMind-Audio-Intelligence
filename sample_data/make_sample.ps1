Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile("sample_data\sample_meeting.wav")
$text = "Good morning team, welcome to the weekly sprint review meeting. First agenda: our machine learning model deployment is currently on track. However, we must finalize the budget allocation proposal before tomorrow afternoon. Sarah, please coordinate with the finance department to get their approval by Friday. John, you will be responsible for setting up the API endpoint monitoring by next Monday. Overall, the progress this week has been great and the client feedback is very positive. Let us wrap up this meeting and execute our respective tasks. Thank you everyone."
$synth.Speak($text)
$synth.Dispose()
Write-Host "Success: Generated sample_data\sample_meeting.wav"
