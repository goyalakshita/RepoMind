
from core.llm_handler import LLMHandler


def main():
    handler = LLMHandler()

    # Temporarily disable Gemini to test Groq fallback
    handler.client = None

    sample_chunks = [
        {
            "code": "def authenticate(username, password):\n    return username == 'admin'",
            "metadata": {
                "file_path": "auth.py",
                "name": "authenticate"
            }
        }
    ]

    print("\nTesting Groq fallback...\n")

    answer = handler.generate_answer(
        "Explain the authenticate function.",
        sample_chunks
    )

    print("\nGenerated Answer:\n")
    print(answer)


if __name__ == "__main__":
    main()
