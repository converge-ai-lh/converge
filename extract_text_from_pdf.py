import requests
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.remote import RemoteReader
import os
import dotenv

dotenv.load_dotenv()

def extract_text_from_pdf_url(pdf_url, headers=None):
    parser = LlamaParse(result_type="text", api_key=os.getenv("LLAMA_CLOUD_API_KEY"))

    file_extractor = {".pdf": parser}
    # DEBUG: Use local file for now
    documents = SimpleDirectoryReader(input_files=['kylian_bezos_internship_review.pdf'], file_extractor=file_extractor).load_data()
    # print(documents)
    
    return documents[0].text

# # Example usage
# pdf_url = "https://files.slack.com/files-pri/T08336M9URG-F082PB0GDGX/kylian_bezos_internship_review.pdf"
# try:
#     headers = {
#         'Authorization': f'Bearer {os.getenv("SLACK_BOT_TOKEN")}'
#     }
#     text = extract_text_from_pdf_url(pdf_url, headers)
#     print("Extracted Text:", text)
# except Exception as e:
#     print("Error:", e)
