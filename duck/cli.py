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
        max_tokens=2000,
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
    import sys
    answers = {}
    
    # Open /dev/tty for both reading AND writing to bypass pre-commit's stdio capture
    try:
        with open('/dev/tty', 'r+') as tty:
            tty.write("\n" + "="*60 + "\n")
            tty.write("📝 PLEASE ANSWER THE FOLLOWING QUESTIONS\n")
            tty.write("="*60 + "\n\n")
            tty.write("(Type your answer and press Enter. Press Ctrl+C to skip)\n\n")
            tty.flush()
            
            for i, question in enumerate(questions, 1):
                tty.write(f"\n[Question {i}/{len(questions)}]\n")
                tty.write(f"Q: {question}\n")
                tty.write("A: ")
                tty.flush()
                
                answer = tty.readline().strip()
                if answer:
                    answers[question] = answer
                else:
                    answers[question] = "(no answer provided)"
            
            tty.write("\n" + "="*60 + "\n")
            tty.write(f"✅ Collected {len(answers)} answers!\n")
            tty.write("="*60 + "\n\n")
            tty.flush()
                    
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
        print("🤖 AI Response received!")
        print(f"📝 Response length: {len(questions_text)} characters")
    except Exception as e:
        print(f"❌ AI request failed: {e}")
        # Provide fallback questions
        print("📝 Using fallback questions...")
        questions_text = """1. What is the main purpose of this change?
2. How does this change improve the codebase?
3. Are there any potential risks or side effects?
4. How will you test this change?
5. Does this change require documentation updates?"""

    print("=========== AI Review Questions ===========")
    print(questions_text)
    print("===========================================")

    # Parse and collect answers
    questions = parse_questions(questions_text)
    print(f"📊 Parsed {len(questions)} questions from AI response")
    
    if not questions:
        print("⚠️ No questions could be parsed. Using fallback questions...")
        questions = [
            "What is the main purpose of this change?",
            "How does this change improve the codebase?", 
            "Are there any potential risks or side effects?",
            "How will you test this change?",
            "Does this change require documentation updates?"
        ]
    
    answers = collect_answers(questions)
    append_to_commit_message(answers)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
