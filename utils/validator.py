import os
import re
from PyPDF2 import PdfReader
from typing import List

class FileValidator:
    @staticmethod
    def validate_pdfs(file_paths):
        errors = []
        
        if not file_paths:
            errors.append("No PDF files found in selected directory")
            return errors
            
        for path in file_paths:
            if not path.lower().endswith('.pdf'):
                errors.append(f"File {path} is not a PDF")
            if os.path.getsize(path) == 0:
                errors.append(f"File {path} is empty")
                
        return errors
    
    @staticmethod
    def validate_pdf_structure(pdf_path):
        try:
            reader = PdfReader(pdf_path)
            if len(reader.pages) == 0:
                return f"PDF file {pdf_path} has no pages"
        except Exception as e:
            return f"Error reading {pdf_path}: {str(e)}"
        return None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize the filename by removing or replacing invalid characters.
        """
        # Replace invalid characters with an underscore or remove them
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots (Windows doesn't allow these at the end)
        sanitized = sanitized.strip('. ')
        return sanitized