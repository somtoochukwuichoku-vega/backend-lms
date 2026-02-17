import google.generativeai as genai
from django.conf import settings
def generate_lesson_summary(content):
    if not content:
        return "No content available to summarize."
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"Please provide a concise, bullet-pointed summary of the following educational content:\n\n{content}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Summary generation failed: {str(e)}"