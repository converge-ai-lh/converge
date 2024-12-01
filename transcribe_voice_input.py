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
    Process speech to text, either from bytes or from a Slack URL.

    Args:
        file_type (str): The audio file extension (e.g. 'mp3', 'wav')
        file_bytes (bytes, optional): Raw audio file bytes
        content_type (str, optional): MIME type of the audio file. Defaults to 'audio/mp4'
        lang (str, optional): Language code for transcription. Defaults to 'en'
        url (str, optional): URL to download audio file from Slack
        headers (dict, optional): Headers required for Slack API request

    Returns:
        str: Transcribed text from the audio

    Raises:
        Exception: If Slack file download fails
        ValueError: If neither file_bytes nor url+headers are provided
    """
    if url and headers:
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
