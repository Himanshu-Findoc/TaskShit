import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_ai_task(selected_commits):
    """Return (title, description) generated from commits."""

    projects = sorted({c["repo"] for c in selected_commits})
    commit_messages = "\n".join(f"- {c['message']}" for c in selected_commits)

    prompt = f"""
Create a professional software development task.

Projects:
{", ".join(projects)}

Git Commits:
{commit_messages}

Rules:
- Title should be creative and distinct, capturing the real theme/impact of these commits
- Maximum 12 words, under 150 characters
- Description should summarize all commits professionally
- Suitable for managers and reporting, avoid excessive jargon
- Plain text only, no markdown

Output format:

Title:
Something

Description:
Summary here.
"""

    return _ask_ai(prompt, fallback=(
        selected_commits[0]["message"].splitlines()[0],
        "Worked on:\n" + commit_messages,
    ))


def generate_meeting_task(agenda):
    """Return (title, description) for a meeting from its agenda."""
    prompt = f"""
Create a professional task entry for a work meeting.

Meeting agenda (from the user):
{agenda}

Rules:
- Title: concise, captures the meeting's purpose, max 10 words, under 140 characters
- Do NOT start the title with "Meeting"
- Description: professional summary of the meeting's agenda and goals
- Suitable for managers and reporting
- Plain text only, no markdown

Output format:

Title:
Something

Description:
Summary here.
"""
    return _ask_ai(prompt, fallback=(agenda.splitlines()[0][:140], agenda))


def _ask_ai(prompt, fallback):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            reasoning_effort="low",
            messages=[
                {"role": "system", "content": "You are a professional software project reporting assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=500,
        )
        return extract_fields(response.choices[0].message.content)

    except Exception as e:
        print(f"⚠️ AI failed, using fallback: {e}")
        return fallback


def extract_fields(ai_result):
    title, description = "", ""
    if "Title:" in ai_result:
        title = ai_result.split("Title:")[1].split("Description:")[0].strip()
    if "Description:" in ai_result:
        description = ai_result.split("Description:")[1].strip()
    return title[:150], description
