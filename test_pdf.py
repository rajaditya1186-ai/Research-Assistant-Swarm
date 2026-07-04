import os
import fitz
from tools.pdf_tool import extract_text

def create_sample_pdf(pdf_path, content_text):
    # Create a new PDF document using PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    # Insert text at coordinate (50, 50)
    page.insert_text((50, 50), content_text)
    doc.save(pdf_path)
    doc.close()
    print(f"Created sample PDF at {pdf_path}")

def test_extraction():
    test_pdf_path = "test_sample.pdf"
    test_content = "This is a test PDF for checking PyMuPDF text extraction."
    
    try:
        # 1. Create the sample PDF
        create_sample_pdf(test_pdf_path, test_content)
        
        # 2. Extract text using the tool
        extracted_text = extract_text(test_pdf_path)
        print("\n--- Extracted Text ---")
        print(extracted_text.strip())
        print("----------------------\n")
        
        # 3. Verify the result
        if test_content in extracted_text:
            print("SUCCESS: Text extraction verified successfully!")
        else:
            print("FAILURE: Extracted text does not match the original content.")
            
    finally:
        # Clean up the test file
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            print(f"Cleaned up test file: {test_pdf_path}")

if __name__ == "__main__":
    test_extraction()
