import assemblyai as aai
from groq import Groq
from django.conf import settings

def generate_lesson_summary(lesson):
    """
    Main utility to transcribe a video using AssemblyAI (Universal-3-Pro)
    and summarize the transcript using Groq (Llama-3.3-70b).
    """
    if not lesson.video_file:
        return {"transcript": "No video file provided.", "summary": "No content to summarize."}

    try:
        # --- PHASE 1: TRANSCRIPTION (AssemblyAI) ---
        aai.settings.api_key = settings.ASSEMBLY_AI_API_KEY
        
        # FIX: Explicitly set the speech_models as required by the API error
        config = aai.TranscriptionConfig(
            speech_models=["universal-3-pro", "universal-2"],
            language_detection=True
        )

        transcriber = aai.Transcriber()
        
        # Transcribe directly from the Cloudinary URL
        transcript_auth = transcriber.transcribe(
            lesson.video_file.url, 
            config=config
        )
        
        if transcript_auth.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI Error: {transcript_auth.error}")
            
        transcript_text = transcript_auth.text

        # --- PHASE 2: SUMMARIZATION (Groq) ---
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an expert educational assistant. "
                        "Summarize the provided lesson transcript into clear, "
                        "concise, and informative bullet points."
                    )
                },
                {
                    "role": "user", 
                    "content": f"Please summarize this transcript:\n\n{transcript_text}"
                }
            ],
            temperature=0.5,
            max_tokens=1024,
        )

        summary_text = completion.choices[0].message.content
        
        return {
            "transcript": transcript_text,
            "summary": summary_text
        }

    except Exception as e:
        # Raise a descriptive error for the Django view to catch
        raise Exception(f"AI Pipeline failed: {str(e)}")