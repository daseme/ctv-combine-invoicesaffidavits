import os
from PyPDF2 import PdfReader, PdfWriter
import re
import logging
from tqdm import tqdm
from typing import Dict, List, Tuple
from utils.validator import FileValidator

class PDFProcessor:
    def __init__(self, input_dir: str = None, ignore_mismatches: bool = False):
        self.input_dir = input_dir or 'input'
        self.ignore_mismatches = ignore_mismatches
        self.found_files = self._find_input_files()
        self.stats = {
            'invoice_count': 0,
            'affidavit_count': 0,
            'processed_count': 0,
            'total_invoice_balance': 0.0  # Initialize total_invoice_balance
        }

    def _find_input_files(self) -> Tuple[str, str]:
        """Find invoice and affidavit PDFs in input directory."""
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
            raise FileNotFoundError(f"Created input directory at {self.input_dir}. Please place your PDF files there.")

        files = os.listdir(self.input_dir)
        invoice_file = next((f for f in files if 'invoice' in f.lower()), None)
        affidavit_file = next((f for f in files if 'affidavit' in f.lower()), None)

        if not (invoice_file and affidavit_file):
            raise FileNotFoundError(
                "Please ensure both invoice and affidavit PDFs are in the input directory.\n"
                "Files should have 'invoice' and 'affidavit' in their names."
            )

        # Validate the PDF files
        file_paths = [
            os.path.join(self.input_dir, invoice_file),
            os.path.join(self.input_dir, affidavit_file)
        ]
        
        validation_errors = FileValidator.validate_pdfs(file_paths)
        if validation_errors:
            raise ValueError("\n".join(validation_errors))

        for file_path in file_paths:
            structure_error = FileValidator.validate_pdf_structure(file_path)
            if structure_error:
                raise ValueError(structure_error)

        return (
            os.path.join(self.input_dir, invoice_file),
            os.path.join(self.input_dir, affidavit_file)
        )

    def extract_customer_info_from_invoice(self, text: str) -> str:
        """
        Extract customer information from invoice PDF text.
        The customer name is the first line after "Bill To".
        """
        # Split the text into lines
        lines = text.splitlines()
        
        # Find the line containing "Bill To"
        bill_to_index = -1
        for i, line in enumerate(lines):
            if "Bill To" in line:
                bill_to_index = i
                break
        
        # If "Bill To" is found, get the next line (customer name)
        if bill_to_index != -1 and bill_to_index + 1 < len(lines):
            customer_name = lines[bill_to_index + 1].strip()
            return customer_name
        
        # Fallback if "Bill To" or customer name is not found
        return "UNKNOWN"

    def extract_customer_info(self, text: str) -> str:
        """Extract customer information from PDF text."""
        match = re.search(r'AFFIDAVIT OF PERFORMANCE - CROSSINGS TV\n(.*?)\n', text)
        return match.group(1).strip() if match else "UNKNOWN"
    
    def extract_invoice_balance(self, text: str) -> float:
        """
        Extract the invoice balance or total from the invoice text.
        Returns the value as a float. If not found, returns 0.0.
        """
        print("Extracted text from invoice:\n", text)  # Debugging: Print the extracted text

        # Look for "Invoice Balance", "Total", or "Balance Due"
        lines = text.splitlines()
        for line in lines:
            if "Invoice Balance" in line or "Total" in line or "Balance Due" in line:
                print("Found line with balance/total:", line)  # Debugging: Print the line

                # Extract the number after the keyword
                # Example: "Invoice Balance $1,372.75" -> "1,372.75"
                parts = line.split()
                for part in parts:
                    # Remove any non-numeric characters (e.g., "$", ",")
                    cleaned = re.sub(r'[^0-9.]', '', part)
                    if cleaned.replace('.', '').isdigit():  # Check if it's a valid number
                        print("Extracted balance:", cleaned)  # Debugging: Print the extracted balance
                        return float(cleaned)

        # Fallback if no balance or total is found
        print("No balance or total found in the text.")  # Debugging: Print if no balance is found
        return 0.0

    def extract_info_from_pdf(self, pdf_path: str, debug_doc_num: str = None) -> Dict[str, List]:
        reader = PdfReader(pdf_path)
        documents = {}
        current_doc = None
        current_pages = []
        doc_numbers = []  # Track all document numbers found
        
        for page in tqdm(reader.pages, desc=f"Processing {os.path.basename(pdf_path)}", unit="page"):
            text = page.extract_text()
            doc_match = re.search(r'(?:Invoice #|Affidavit)\s*(\d{4}-\d{3})', text)
            
            if doc_match:
                if current_doc:
                    documents[current_doc] = current_pages
                current_doc = doc_match.group(1)
                current_pages = [page]
                doc_numbers.append(current_doc)  # Store found document number
            elif current_doc:
                current_pages.append(page)
                
        if current_doc:
            documents[current_doc] = current_pages

        # Log found document numbers
        logging.info(f"Found documents in {os.path.basename(pdf_path)}: {sorted(doc_numbers)}")
        
        return documents

    def process_pdfs(self):
        """Process PDFs and merge them with progress tracking."""
        invoice_file, affidavit_file = self.found_files
        
        # Extract YM code from filename
        ym_match = re.search(r'(\d{4})', os.path.basename(invoice_file))
        ym_code = ym_match.group(1) if ym_match else "0000"
        
        output_dir = f"{ym_code}_output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        logging.info("Extracting document information from invoices...")
        invoice_docs = self.extract_info_from_pdf(invoice_file)
        logging.info(f"Found {len(invoice_docs)} invoices.")

        logging.info("Extracting document information from affidavits...")
        affidavit_docs = self.extract_info_from_pdf(affidavit_file)
        logging.info(f"Found {len(affidavit_docs)} affidavits.")

        self.stats['invoice_count'] = len(invoice_docs)
        self.stats['affidavit_count'] = len(affidavit_docs)

        # Check for mismatching document numbers
        invoice_doc_numbers = set(invoice_docs.keys())
        affidavit_doc_numbers = set(affidavit_docs.keys())
        missing_invoices = affidavit_doc_numbers - invoice_doc_numbers
        missing_affidavits = invoice_doc_numbers - affidavit_doc_numbers

        mismatch_details = []
        if missing_invoices or missing_affidavits:
            if missing_invoices:
                mismatch_details.append(f"Missing invoices: {', '.join(sorted(missing_invoices))}")
            if missing_affidavits:
                mismatch_details.append(f"Missing affidavits: {', '.join(sorted(missing_affidavits))}")
            
            if not self.ignore_mismatches:
                raise ValueError("Document count mismatch:\n" + "\n".join(mismatch_details))
            
            # If ignoring mismatches, only process documents that have both invoice and affidavit
            common_docs = invoice_doc_numbers & affidavit_doc_numbers
            invoice_docs = {k: v for k, v in invoice_docs.items() if k in common_docs}
            affidavit_docs = {k: v for k, v in affidavit_docs.items() if k in common_docs}
            
            logging.warning("\n".join(mismatch_details))

        logging.info("Merging documents...")
        for doc_num in tqdm(invoice_docs, desc="Creating merged PDFs", unit="doc"):
            try:
                writer = PdfWriter()
                
                # Add invoice and affidavit pages
                for page in invoice_docs[doc_num]:
                    writer.add_page(page)
                for page in affidavit_docs[doc_num]:
                    writer.add_page(page)
                
                # Extract customer info
                affidavit_text = affidavit_docs[doc_num][0].extract_text()
                customer_info = self.extract_customer_info(affidavit_text)
                
                # Log the derived customer name
                logging.info(f"Derived customer name for {doc_num}: {customer_info}")
                
                # Extract invoice balance
                invoice_balance = self.extract_invoice_balance(invoice_docs[doc_num][0].extract_text())
                self.stats['total_invoice_balance'] += invoice_balance  # Update total_invoice_balance
                logging.info(f"Invoice balance for {doc_num}: {invoice_balance}")
                
                # Check if "WorldLink" is in the customer name
                if "WorldLink" in customer_info:
                    name_portion = "WorldLink"  # Use only "WorldLink" for the name portion
                else:
                    name_portion = customer_info  # Use the full customer name
                
                # Sanitize the name portion to create a valid file name
                sanitized_name_portion = FileValidator.sanitize_filename(name_portion)
                output_filename = os.path.join(output_dir, f"{doc_num} {sanitized_name_portion}.pdf")
                
                # Save the merged PDF
                with open(output_filename, 'wb') as output_file:
                    writer.write(output_file)
                self.stats['processed_count'] += 1
                logging.info(f"Processed document {doc_num}.")
            except Exception as e:
                logging.error(f"Error processing document {doc_num}: {e}")
                continue

        logging.info(f"Processing complete! Output files are in the '{output_dir}' directory.")
        return self.stats, mismatch_details if (missing_invoices or missing_affidavits) else None