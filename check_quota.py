from app.providers.gemini_provider import GeminiProvider

try:
    GeminiProvider().generate("Say hi", "gemini-3.6-flash")
    print("OK - quota available again")
except Exception as e:
    print(e)