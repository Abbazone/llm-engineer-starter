import mimetypes
import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
import dotenv

from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from google.cloud.documentai_v1 import Document

from src.extractors import extract_encounter_indices, extract_info_from_encounter_chunk
from src.utils import read_yaml, has_numbers

# Load Env Files.
# This will return True if your env vars are loaded successfully
dotenv.load_dotenv()


class DocumentAI:
    """Wrapper class around GCP's DocumentAI API."""
    def __init__(self) -> None:

        self.client_options = ClientOptions(  # type: ignore
            api_endpoint=f"{os.getenv('GCP_REGION')}-documentai.googleapis.com",
            credentials_file=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        )
        self.client = documentai.DocumentProcessorServiceClient(client_options=self.client_options)
        self.processor_name = self.client.processor_path(
            os.getenv("GCP_PROJECT_ID"),
            os.getenv("GCP_REGION"),
            os.getenv("GCP_PROCESSOR_ID")
        )

    def __call__(self, file_path: Path) -> Document:
        """Convert a local PDF into a GCP document. Performs full OCR extraction and layout parsing."""

        # Read the file into memory
        with open(file_path, "rb") as file:
            content = file.read()

        mime_type = mimetypes.guess_type(file_path)[0]
        raw_document = documentai.RawDocument(content=content, mime_type=mime_type)

        # Configure the process request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=raw_document
        )

        result = self.client.process_document(request=request)
        document = result.document

        return document


def split_pdfs(input_file_path, pdf_split_pages=10):
    """
    Split PDF file into multiple files.
    """
    inputpdf = PdfReader(open(input_file_path, "rb"))
    fname = input_file_path.split('/')[-1]

    out_paths = []
    if not os.path.exists("data/output"):
        os.makedirs("data/output")

    number_of_pages = len(inputpdf.pages)
    number_of_chunks = number_of_pages // pdf_split_pages

    chunk = 0
    while chunk <= number_of_chunks:
        start_page = chunk * pdf_split_pages
        end_page = (chunk + 1) * pdf_split_pages
        if start_page >= number_of_pages:
            break
        pages = inputpdf.pages[start_page: end_page]

        output = PdfWriter()
        for page in pages:
            output.add_page(page)

        out_file_path = f"data/output/{fname[:-4]}_{chunk}.pdf"
        with open(out_file_path, "wb") as output_stream:
            output.write(output_stream)

        out_paths.append(out_file_path)
        chunk += 1

    return out_paths


def read_pdf_text(paths: list):
    """ Uses DocumentAI to obtain text from PDF"""
    document_ai = DocumentAI()
    all_text = ""
    for path in paths:
        doc = document_ai(path)
        all_text += doc.text

    return all_text


def process_pdf(filepath) -> list[dict]:
    """
    An entry point. Takes the filepath of a PDF document and return list of dictionaries of medical encounters.
    """

    config = read_yaml('./src/config.yaml')

    pdf_paths = split_pdfs(filepath, config['pdf_split_pages'])
    doc_text = read_pdf_text(pdf_paths)
    doc_lines = doc_text.splitlines()

    # number text lines and filter-out lines not likely to indicate an encounter
    numbered_doc_lines = [f"{i:04} {doc_lines[i]}" for i in range(len(doc_lines))]
    numbered_doc_lines = [line for line in numbered_doc_lines if has_numbers(line[5:]) and len(line[5:]) > 6]

    # extract indices of lines indicating an encounter
    encounter_indices = extract_encounter_indices(numbered_doc_lines, config['chunk_size'])

    # extract information from encounter based chunks
    encounters = []
    for i in range(len(encounter_indices) - 1):
        start = encounter_indices[i]
        end = encounter_indices[i + 1]
        encounter = extract_info_from_encounter_chunk(doc_lines[start:end])
        encounters.append(encounter)

    return encounters


if __name__ == '__main__':

    # Example Usage
    document_ai = DocumentAI()
    document = document_ai(Path("data/sample.pdf"))
