import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO", "")

PROMPT_RULES_FILE = Path("prompt_rules.txt")
USED_PROMPTS_FILE = Path("used_prompts.txt")


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def save_used_prompt(prompt_text: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with USED_PROMPTS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp} | {prompt_text}\n")


def generate_weekend_prompt() -> str:
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY in .env")

    rules = read_text_file(PROMPT_RULES_FILE)
    used_prompts = read_text_file(USED_PROMPTS_FILE)

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
{rules}

Previously used prompts:
{used_prompts}

Generate one fresh weekend prompt.
Avoid repeating previous prompts.
Keep it playful, simple, and usable across many mediums.
"""
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()


def format_email_body(prompt_text: str) -> str:
    return f"""🎬 Weekend Prompt Club

{prompt_text}

Starts: Friday, 8 a.m.
Submit by: Sunday, 8 p.m.

Any medium.
No critique.
Make something and have fun!
"""


def send_email(subject: str, body: str) -> None:
    if not EMAIL_FROM:
        raise ValueError("Missing EMAIL_FROM in .env")

    if not EMAIL_APP_PASSWORD:
        raise ValueError("Missing EMAIL_APP_PASSWORD in .env")

    recipients = [email.strip() for email in EMAIL_TO.split(",") if email.strip()]

    if not recipients:
        raise ValueError("Missing EMAIL_TO in .env")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
        smtp.send_message(message)


def main() -> None:
    prompt_text = generate_weekend_prompt()
    email_body = format_email_body(prompt_text)

    send_email(
        subject="Weekend Prompt Club",
        body=email_body
    )

    save_used_prompt(prompt_text)

    print("Email sent successfully.")
    print()
    print(email_body)


if __name__ == "__main__":
    main()