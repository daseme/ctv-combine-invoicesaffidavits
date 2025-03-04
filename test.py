from pdf_processor import PDFProcessor

def test_extract_invoice_balance():
    processor = PDFProcessor()
    text = "Invoice Balance $1,372.75"
    assert processor.extract_invoice_balance(text) == 1372.75

    text = "Total $912.05"
    assert processor.extract_invoice_balance(text) == 912.05

    text = "No balance here"
    assert processor.extract_invoice_balance(text) == 0.0

# Call the test function
test_extract_invoice_balance()
print("All tests passed!")