import requests
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.remote import RemoteReader
import os
import dotenv

dotenv.load_dotenv()

def extract_text_from_pdf_url(pdf_url, headers=None):
    """
    Extract text content from a PDF file using LlamaParse.
    
    Args:
        pdf_url (str): URL of the PDF file to process
        headers (dict, optional): Headers to use for the request, e.g. for authentication
        
    Returns:
        str: Extracted text content from the PDF
        
    Note:
        Currently uses a local test file. TODO: Implement remote PDF fetching.
    """
    parser = LlamaParse(result_type="text", api_key=os.getenv("LLAMA_CLOUD_API_KEY"))

    file_extractor = {".pdf": parser}
    documents = SimpleDirectoryReader(input_files=['kylian_bezos_internship_review.pdf'], file_extractor=file_extractor).load_data()
    
    return documents[0].text
