#!/usr/bin/env python3
"""prepare-commit-msg hook to add duck answers to commit message."""

import json
import os
import sys
import tempfile


def main():
    commit_msg_file = sys.argv[1]
    
    # Check if we have saved answers from duck
    temp_dir = tempfile.gettempdir()
    answers_file = os.path.join(temp_dir, 'duck_answers.json')
    
    if not os.path.exists(answers_file):
        # No answers to add
        return 0
    
    try:
        with open(answers_file, 'r') as f:
            answers = json.load(f)
        
        # Read the current commit message
        with open(commit_msg_file, 'r') as f:
            original_msg = f.read()
        
        # Append Q&A to commit message
        with open(commit_msg_file, 'w') as f:
            f.write(original_msg)
            f.write("\n\n--- Duck Review Questions & Answers ---\n")
            for question, answer in answers.items():
                f.write(f"\nQ: {question}\n")
                f.write(f"A: {answer}\n")
        
        # Clean up the temp file
        os.remove(answers_file)
        
    except Exception as e:
        print(f"Warning: Could not append duck answers: {e}", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
