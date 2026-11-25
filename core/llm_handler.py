
import os
import json
import urllib.request
import urllib.error

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class LLMHandler:
    """
    Handles AI responses using Gemini as the primary provider
    and Groq as the fallback provider.
    """

    def __init__(self, model_name="gemini-3.5-flash-lite"):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        self.model_name = model_name
        self.groq_model = "openai/gpt-oss-120b"

        self.client = None

        if self.gemini_api_key:
            self.client = genai.Client(
                api_key=self.gemini_api_key,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1)
                )
            )

        if not self.gemini_api_key and not self.groq_api_key:
            raise ValueError(
                "No AI API keys found. Add GEMINI_API_KEY or GROQ_API_KEY "
                "to your .env file."
            )

    def _build_prompt(self, query, retrieved_chunks):

        context_parts = []

        for index, chunk in enumerate(retrieved_chunks, start=1):
            metadata = chunk.get("metadata", {})

            context_parts.append(
                f"""
Source {index}
File: {metadata.get('file_path', 'Unknown file')}
Function/Class: {metadata.get('name', 'Unknown')}

Code:
{chunk.get('code', '')}
"""
            )

        context = "\n".join(context_parts)

        return f"""
You are RepoMind, an AI assistant that helps developers
understand software repositories.

Answer the user's question using the repository code provided.

Instructions:
1. Base your answer on the supplied code.
2. Do not invent functions, files, or implementation details.
3. Explain the code in simple language.
4. Mention relevant file names and function names.
5. If the code does not contain enough information,
   clearly mention that limitation.

Repository Context:
{context}

User Question:
{query}

Answer:
"""

    def _generate_gemini(self, prompt):

        if not self.client:
            raise RuntimeError("Gemini API key is not configured.")

        response = self.client.interactions.create(
            model=self.model_name,
            input=prompt
        )

        if not response.output_text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.output_text.strip()

    def _generate_groq(self, prompt):

        if not self.groq_api_key:
            raise RuntimeError("Groq API key is not configured.")

        url = "https://api.groq.com/openai/v1/chat/completions"

        payload = {
            "model": self.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are RepoMind, a software repository assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "RepoMind/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))

            answer = result["choices"][0]["message"]["content"]

            if not answer:
                raise RuntimeError("Groq returned an empty response.")

            return answer.strip()

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Groq API error ({error.code}): {details}"
            ) from error

        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Could not connect to Groq: {error.reason}"
            ) from error

    def generate_answer(self, query, retrieved_chunks):

        if not query or not query.strip():
            raise ValueError("Question cannot be empty.")

        if not retrieved_chunks:
            return (
                "I could not find relevant code in the repository "
                "to answer this question."
            )

        prompt = self._build_prompt(query, retrieved_chunks)

        # Try Gemini first
        if self.client:
            try:
                print("Trying Gemini...")
                answer = self._generate_gemini(prompt)
                print("Answer generated using Gemini.")
                return answer

            except Exception as gemini_error:
                print(f"Gemini failed: {gemini_error}")
                print("Switching to Groq...")

        # Use Groq as fallback
        if self.groq_api_key:
            try:
                answer = self._generate_groq(prompt)
                print("Answer generated using Groq.")
                return answer

            except Exception as groq_error:
                raise RuntimeError(
                    "Both AI providers failed.\n"
                    f"Gemini error: {gemini_error if self.client else 'Not configured'}\n"
                    f"Groq error: {groq_error}"
                ) from groq_error

        raise RuntimeError(
            "Gemini is unavailable and no Groq API key is configured."
        )
