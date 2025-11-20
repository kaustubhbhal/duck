import subprocess
import sys
import json
from openai import OpenAI


def get_staged_diff() -> str:
    """Return the staged diff as a string."""
    result = subprocess.run(
        ["git", "diff", "--cached"], capture_output=True, text=True, check=False
    )
    return result.stdout


def ask_ai_for_review_questions(diff: str) -> str:
    """
    Send the diff to an AI model and get back several short
    questions asking the developer about their intent.
    """
    client = OpenAI()  # assumes OPENAI_API_KEY is set

    prompt = f"""
You are a code review assistant. A developer is attempting a commit.
Given the following git diff, generate 3–5 short, sharp questions that
probe the *reasoning* behind the changes. Avoid generic questions.
Focus on intent, assumptions, and consequences.

Diff:
    
"""

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You generate thoughtful code-review questions.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0.4,
    )

    return completion.choices[0].message["content"].strip()


def main() -> int:
    print("🔍 Collecting staged diff...")
    diff = get_staged_diff()

    if not diff.strip():
        print("No staged changes detected. Skipping AI questions.")
        return 0

    print("🤖 Generating review questions using AI...\n")

    try:
        questions = ask_ai_for_review_questions(diff)
    except Exception as e:
        print(f"AI request failed: {e}")
        # You may choose to block commit on failure; for now, allow commit.
        return 0

    print("=========== AI Review Questions ===========")
    print(questions)
    print("===========================================\n")

    # By default, do NOT block the commit.
    # To block: return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
