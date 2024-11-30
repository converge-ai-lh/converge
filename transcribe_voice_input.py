from openai import OpenAI
import os
from dotenv import load_dotenv
import requests

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def process_speech_bytes_to_text(file_type, file_bytes=None, content_type=None, lang="en", url=None, headers=None):
    """
    Process speech to text, either from bytes or from a Slack URL
    """
    if url and headers:
        # Download the file from Slack
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download audio file: {response.status_code}")
        file_bytes = response.content
    
    if not file_bytes:
        raise ValueError("Either file_bytes or url+headers must be provided")

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=("temp." + file_type, file_bytes, content_type or "audio/mp4"),
        response_format="text",
        language=lang,
    )
    return transcript


# if __name__ == "__main__":
#     transcript = process_speech_bytes_to_text(
#         file_type='m4a',
#         url='https://files.slack.com/files-tmb/T08336M9URG-F0830VB3YJZ-a444ce43c3/audio_message_audio.mp4',
#         headers={
#             'Authorization': f'Bearer {os.getenv("SLACK_BOT_TOKEN")}'
#         }
#     )
#     print(transcript)
