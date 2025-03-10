# pdf_processor.py
import os
from PyPDF2 import PdfReader
from PyPDF2._writer import PdfWriter  # force direct import
import re
import logging
from tqdm import tqdm
from typing import Dict, List, Tuple
from utils.validator import FileValidator

class PDFProcessor:
    def __init__(self, input_dir: str = None, output_dir=None, ignore_mismatches: bool = False):
        self.input_dir = input_dir or 'input'
        self.output_dir = output_dir
        self.ignore_mismatches = ignore_mismatches
        self.found_files = self._find_input_files()
        self.stats = {
            'invoice_count': 0,
            'affidavit_count': 0,
            'processed_count': 0
        }

    def _find_input_files(self) -> Tuple[str, str]:
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

        file_paths = [os.path.join(self.input_dir, invoice_file), os.path.join(self.input_dir, affidavit_file)]
        validation_errors = FileValidator.validate_pdfs(file_paths)
        if validation_errors:
            raise ValueError("\n".join(validation_errors))

        for file_path in file_paths:
            structure_error = FileValidator.validate_pdf_structure(file_path)
            if structure_error:
                raise ValueError(structure_error)

        return (os.path.join(self.input_dir, invoice_file), os.path.join(self.input_dir, affidavit_file))

    def extract_customer_info_from_invoice(self, text: str) -> str:
        lines = text.splitlines()
        bill_to_index = -1
        for i, line in enumerate(lines):
            if "Bill To" in line:
                bill_to_index = i
                break
        if bill_to_index != -1 and bill_to_index + 1 < len(lines):
            customer_name = lines[bill_to_index + 1].strip()
            return customer_name
        return "UNKNOWN"

    def extract_info_from_pdf(self, pdf_path: str, debug_doc_num: str = None) -> Dict[str, List]:
        reader = PdfReader(pdf_path)
        documents = {}
        current_doc = None
        current_pages = []
        doc_numbers = []
        for page in tqdm(reader.pages, desc=f"Processing {os.path.basename(pdf_path)}", unit="page"):
            text = page.extract_text()
            doc_match = re.search(r'(?:Invoice #|Affidavit)\s*(\d{4}-\d{3})', text)
            if doc_match:
                if current_doc:
                    documents[current_doc] = current_pages
                current_doc = doc_match.group(1)
                current_pages = [page]
                doc_numbers.append(current_doc)
            elif current_doc:
                current_pages.append(page)
        if current_doc:
            documents[current_doc] = current_pages
        logging.info(f"Found documents in {os.path.basename(pdf_path)}: {sorted(doc_numbers)}")
        return documents

    def process_pdfs(self):
        invoice_file, affidavit_file = self.found_files
        ym_match = re.search(r'(\d{4})', os.path.basename(invoice_file))
        ym_code = ym_match.group(1) if ym_match else "0000"
        output_dir = self.output_dir or f"{ym_code}_output"
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
            common_docs = invoice_doc_numbers & affidavit_doc_numbers
            invoice_docs = {k: v for k, v in invoice_docs.items() if k in common_docs}
            affidavit_docs = {k: v for k, v in affidavit_docs.items() if k in common_docs}
            logging.warning("\n".join(mismatch_details))

        logging.info("Merging documents...")
        for doc_num in invoice_docs:
            try:
                writer = PdfWriter()
                # Debug log for writer
                logging.info(f"Created writer for document {doc_num}: {writer}")

                valid_invoice_pages = [page for page in invoice_docs[doc_num] if page is not None]
                valid_affidavit_pages = [page for page in affidavit_docs[doc_num] if page is not None]

                for page in valid_invoice_pages:
                    writer.add_page(page)
                for page in valid_affidavit_pages:
                    writer.add_page(page)

                if not writer.pages:
                    logging.warning(f"No valid pages for document {doc_num}; skipping file creation.")
                    continue

                invoice_text = valid_invoice_pages[0].extract_text() if valid_invoice_pages else ""
                customer_info = self.extract_customer_info_from_invoice(invoice_text)
                sanitized_customer_info = FileValidator.sanitize_filename(customer_info)
                output_filename = os.path.join(output_dir, f"{doc_num} {sanitized_customer_info}.pdf")
                logging.info(f"Writing output file: {output_filename}")
                with open(output_filename, 'wb') as output_file:
                    writer.write(output_file)
                self.stats['processed_count'] += 1
                logging.info(f"Processed document {doc_num}.")
            except Exception as e:
                logging.error(f"Error processing document {doc_num}: {e}")
                continue

        logging.info(f"Processing complete! Output files are in the '{output_dir}' directory.")
        return self.stats, mismatch_details if (missing_invoices or missing_affidavits) else None