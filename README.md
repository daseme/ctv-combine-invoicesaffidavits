# Invoice and Affidavit Merger

A Python application that automatically merges invoice and affidavit PDF files, with a modern graphical user interface built using tkinter.

## Features

- Automatically matches invoice and affidavit PDFs based on document numbers
- Modern GUI interface with progress tracking
- Validates PDF files before processing
- Creates merged PDFs named with document number and customer information
- Supports handling mismatched documents with option to ignore discrepancies
- Organizes output files in year-month coded directories

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone this repository or download the source code:
```bash
git clone [repository-url]
cd invoice-merger
```

2. Install the required dependencies:
```bash
pip install PyPDF2 ttkthemes tqdm
```

## Usage

### GUI Method

1. Run the application:
```bash
python main.py
```

2. Place your PDF files in the `input` directory:
   - Files should contain either 'invoice' or 'affidavit' in their names
   - Example: `2024_invoice.pdf`, `2024_affidavit.pdf`

3. Use the GUI interface to:
   - Select input directory (optional)
   - Toggle "Ignore Mismatches" option
   - Start processing
   - Monitor progress
   - View processing results

### File Structure

```
project/
├── input/
│   ├── YYYY_invoice.pdf
│   └── YYYY_affidavit.pdf
├── YYYY_output/
│   └── XXXX-XXX Customer Name.pdf
├── main.py
├── pdf_processor.py
└── utils/
    ├── logger.py
    └── validator.py
```

### Output

- Merged PDFs are saved in a directory named `YYYY_output` (where YYYY is extracted from the input filename)
- Each merged file is named with the format: `XXXX-XXX Customer Name.pdf`
  - XXXX-XXX is the document number
  - Customer Name is extracted from the affidavit

## Error Handling

The program includes several validation checks:
- Verifies presence of both invoice and affidavit files
- Validates PDF file structure
- Checks for matching document numbers between invoices and affidavits
- Provides detailed error messages for troubleshooting

## Development

The application is structured into several components:
- `main.py`: Application entry point and GUI initialization
- `pdf_processor.py`: Core PDF processing logic
- `utils/`: Helper functions for logging and validation

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

[Insert your license information here]