from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",#"gemini-2.5-pro",
    contents="solve x^2 + 4x + 4 = 0",
)
print(response.text)
