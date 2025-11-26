#!/usr/bin/env python3
"""
Manual PDF reader to extract text from test.pdf
"""
import os
import sys

def read_pdf_with_pymupdf(filepath):
    """Read PDF using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error with PyMuPDF: {e}"

def read_pdf_with_pdfplumber(filepath):
    """Read PDF using pdfplumber"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    text += "[No text found on this page]"
        return text
    except Exception as e:
        return f"Error with pdfplumber: {e}"

def main():
    filepath = "test.pdf"
    
    if not os.path.exists(filepath):
        print(f"❌ Error: File '{filepath}' not found in current directory.")
        print(f"Current directory: {os.getcwd()}")
        print("Available files:")
        for file in os.listdir('.'):
            if file.endswith('.pdf'):
                print(f"  - {file}")
        return
    
    print(f"📖 Reading PDF: {filepath}")
    print(f"File size: {os.path.getsize(filepath)} bytes")
    
    # Try PyMuPDF first
    print("\n🔍 Attempting to read with PyMuPDF...")
    text_pymupdf = read_pdf_with_pymupdf(filepath)
    
    if not text_pymupdf.startswith("Error"):
        print("✅ Successfully read with PyMuPDF")
        print("\n" + "="*50)
        print("PDF CONTENT:")
        print("="*50)
        print(text_pymupdf)
        return
    
    # Try pdfplumber as fallback
    print("⚠️ PyMuPDF failed, trying pdfplumber...")
    text_pdfplumber = read_pdf_with_pdfplumber(filepath)
    
    if not text_pdfplumber.startswith("Error"):
        print("✅ Successfully read with pdfplumber")
        print("\n" + "="*50)
        print("PDF CONTENT:")
        print("="*50)
        print(text_pdfplumber)
        return
    
    # Both failed
    print("❌ Both PyMuPDF and pdfplumber failed:")
    print(f"PyMuPDF error: {text_pymupdf}")
    print(f"pdfplumber error: {text_pdfplumber}")

if __name__ == "__main__":
    main()