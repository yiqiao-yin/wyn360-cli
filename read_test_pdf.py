#!/usr/bin/env python3
"""
Simple script to read and extract text from tests/test.pdf
"""
import sys

try:
    import pymupdf as fitz  # PyMuPDF
    print("Using PyMuPDF for PDF extraction")
except ImportError:
    try:
        import fitz
        print("Using fitz for PDF extraction")
    except ImportError:
        print("PyMuPDF not available, trying pdfplumber...")
        try:
            import pdfplumber
            print("Using pdfplumber for PDF extraction")
        except ImportError:
            print("No PDF libraries available. Please install pymupdf or pdfplumber")
            sys.exit(1)

def extract_pdf_text(pdf_path):
    """Extract text from PDF using available library"""
    text_content = []
    
    if 'fitz' in globals():
        # Using PyMuPDF
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_content.append(f"=== Page {page_num + 1} ===\n{text}")
        doc.close()
        
    elif 'pdfplumber' in globals():
        # Using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    text_content.append(f"=== Page {page_num + 1} ===\n{text}")
    
    return "\n\n".join(text_content)

def main():
    pdf_path = "tests/test.pdf"
    
    try:
        print(f"Reading PDF: {pdf_path}")
        text = extract_pdf_text(pdf_path)
        
        if text.strip():
            print(f"\n{'='*50}")
            print("EXTRACTED TEXT:")
            print(f"{'='*50}")
            print(text)
            
            # Basic summary info
            lines = text.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            word_count = len(text.split())
            
            print(f"\n{'='*50}")
            print("SUMMARY STATISTICS:")
            print(f"{'='*50}")
            print(f"Total characters: {len(text)}")
            print(f"Total words: {word_count}")
            print(f"Total non-empty lines: {len(non_empty_lines)}")
            
        else:
            print("No text content found in PDF")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())