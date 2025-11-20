import subprocess
import sys
import json
import os
import tempfile
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
{diff}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
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

    return completion.choices[0].message.content.strip()


def parse_questions(questions_text: str) -> list[str]:
    """Parse the AI-generated questions into a list."""
    lines = questions_text.strip().split('\n')
    parsed = []
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-')):
            # Remove leading numbers/bullets
            question = line.lstrip('0123456789.-) ').strip()
            if question:
                parsed.append(question)
    return parsed


def collect_answers(questions: list[str]) -> dict[str, str]:
    """Prompt the user to answer each question."""
    answers = {}
    print("\n" + "="*60, flush=True)
    print("📝 PLEASE ANSWER THE FOLLOWING QUESTIONS", flush=True)
    print("="*60 + "\n", flush=True)
    print("(Type your answer and press Enter. Press Ctrl+C to skip)\n", flush=True)
    
    # Open /dev/tty to read from the terminal even in a hook
    try:
        with open('/dev/tty', 'r') as tty:
            for i, question in enumerate(questions, 1):
                print(f"\n[Question {i}/{len(questions)}]", flush=True)
                print(f"Q: {question}", flush=True)
                print("A: ", end='', flush=True)
                sys.stdout.flush()  # Extra flush
                answer = tty.readline().strip()
                if answer:
                    answers[question] = answer
                else:
                    answers[question] = "(no answer provided)"
        
        print("\n" + "="*60, flush=True)
        print(f"✅ Collected {len(answers)} answers!", flush=True)
        print("="*60 + "\n", flush=True)
                    
    except KeyboardInterrupt:
        print("\n\n⚠️  Q&A cancelled by user. Continuing without answers.")
        return {}
    except Exception as e:
        print(f"Error reading input: {e}")
        print("Skipping Q&A collection.")
        return {}
    
    return answers


def append_to_commit_message(answers: dict[str, str]) -> None:
    """Append the Q&A to the commit message via prepare-commit-msg hook."""
    # Git provides the commit message file path via environment variable
    commit_msg_file = os.environ.get('GIT_COMMIT_MSG_FILE')
    
    if not commit_msg_file:
        # We're in pre-commit, so we'll save answers to a temp file
        # that prepare-commit-msg can read
        temp_dir = tempfile.gettempdir()
        answers_file = os.path.join(temp_dir, 'duck_answers.json')
        with open(answers_file, 'w') as f:
            json.dump(answers, f, indent=2)
        print(f"\n✅ Answers saved. They will be added to your commit message.")
    else:
        # We're in prepare-commit-msg, append to the commit message
        with open(commit_msg_file, 'a') as f:
            f.write("\n\n--- Duck Review Questions & Answers ---\n")
            for question, answer in answers.items():
                f.write(f"\nQ: {question}\n")
                f.write(f"A: {answer}\n")


def main() -> int:
    print("🔍 Collecting staged diff...")
    diff = get_staged_diff()

    if not diff.strip():
        print("No staged changes detected. Skipping AI questions.")
        return 0

    print("🤖 Generating review questions using AI...\n")

    try:
        questions_text = ask_ai_for_review_questions(diff)
    except Exception as e:
        print(f"AI request failed: {e}")
        # You may choose to block commit on failure; for now, allow commit.
        return 0

    print("=========== AI Review Questions ===========")
    print(questions_text)
    print("===========================================")

    # Parse and collect answers
    questions = parse_questions(questions_text)
    if not questions:
        print("\nNo questions parsed. Continuing commit.")
        return 0
    
    answers = collect_answers(questions)
    append_to_commit_message(answers)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
