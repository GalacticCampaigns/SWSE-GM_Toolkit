# """
# SCRIPT: PDF Image OCR Extractor (Command-Line Version - Iterative Page & Incremental Write)
#
# DESCRIPTION:
# This script performs Optical Character Recognition (OCR) on image-based PDF files.
# It converts PDF pages to images iteratively (one page at a time) to manage memory.
# Extracted text is written to the output file incrementally in batches (e.g., every 10 pages)
# to save progress and further manage resources for very large documents.
#
# REQUIREMENTS:
# 1.  Python 3.x
# 2.  Tesseract OCR Engine (configured in PATH or via pytesseract.tesseract_cmd)
# 3.  Poppler Utilities (installed and in PATH)
# 4.  Python Libraries: pip install pytesseract Pillow pdf2image
#
# INPUT:
# -   Primary input is the file path to an image-based PDF (command-line argument).
# -   Optional arguments for output file, OCR language, DPI, and write batch size.
#
# OUTPUT:
# -   A single .txt file containing all extracted text, written incrementally.
# -   Default output: "[input_pdf_name]_extracted_text.txt" in input PDF's directory.
#
# USAGE:
#   python pdf_ocr_tool.py path/to/your/document.pdf
#   python pdf_ocr_tool.py document.pdf -o output.txt --lang spa --dpi 200 --batch-write 20
#
#   For detailed help: python pdf_ocr_tool.py -h
#
# OCR LANGUAGE: Default 'eng'. Use -l or --lang.
# IMAGE PREPROCESSING: Placeholder in ocr_pdf_to_text function.
# WRITE BATCH SIZE: Use --batch-write (default 10) to set pages per incremental write.
# """

import os
import argparse
from pdf2image import convert_from_path, pdfinfo_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
    PDFPopplerTimeoutError
)
import pytesseract
from PIL import Image
# import gc # Uncomment if you want to try explicit garbage collection

# --- Tesseract Configuration ---
# IMPORTANT: If Tesseract is not in your system's PATH, uncomment and set the following line.
# Example for Windows:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Example for Linux/macOS:
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

def ocr_pdf_to_text(pdf_path: str, output_txt_file: str, lang: str = 'eng', dpi_value: int = 300, write_batch_size: int = 10) -> bool:
    """
    Performs OCR on PDF pages iteratively, writing extracted text incrementally in batches.

    Args:
        pdf_path (str): Path to the input PDF.
        output_txt_file (str): Path for the output text file.
        lang (str): OCR language code for Tesseract.
        dpi_value (int): DPI for PDF to image conversion.
        write_batch_size (int): Number of pages to process before writing their text to the file.

    Returns:
        bool: True if OCR was successful, False otherwise.
    """
    print(f"**Starting OCR process for: {pdf_path}**")
    print(f"**Output will be saved to: {output_txt_file}**")
    print(f"**OCR Language: {lang}, DPI: {dpi_value}, Write Batch Size: {write_batch_size} pages**")

    current_batch_text_list = [] # Stores text for the current batch
    output_file_object = None

    try:
        # 1. Get PDF page count
        print(f"**Getting PDF info for {pdf_path}...**")
        info = pdfinfo_from_path(pdf_path) # Add poppler_path if needed
        total_pages = info["Pages"]
        if total_pages == 0:
            print("**Error: PDF has 0 pages or page count could not be determined.**")
            return False
        print(f"**PDF has {total_pages} pages. Processing iteratively, writing every {write_batch_size} pages.**")

        # 2. Open output file in write mode (clears existing content)
        output_dir = os.path.dirname(os.path.abspath(output_txt_file))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"**Created output directory: {output_dir}**")
        output_file_object = open(output_txt_file, "w", encoding="utf-8")

        # 3. Iterate through pages, convert one by one, perform OCR
        for page_num in range(1, total_pages + 1):
            print(f"**Processing page {page_num} of {total_pages}...**")
            try:
                page_images = convert_from_path(
                    pdf_path,
                    dpi=dpi_value,
                    first_page=page_num,
                    last_page=page_num,
                    grayscale=True, # Recommended for OCR
                    # poppler_path=r"C:\path\to\poppler\bin" # Add if poppler not in PATH
                )

                if not page_images:
                    print(f"**Warning: Could not convert page {page_num}. Skipping.**")
                    current_batch_text_list.append(f"--- Page {page_num} ---\n[Conversion Error on this page]\n\n")
                    # Continue to the batch write check
                else:
                    image_obj = page_images[0]
                    tesseract_config = '--oem 1' # LSTM only engine
                    page_text = pytesseract.image_to_string(image_obj, lang=lang, config=tesseract_config)
                    current_batch_text_list.append(f"--- Page {page_num} ---\n")
                    current_batch_text_list.append(page_text)
                    current_batch_text_list.append("\n\n")
                    del image_obj
                    del page_images

            except PDFInfoNotInstalledError:
                 print("**Error: Poppler not installed or not in PATH (encountered during page conversion).**")
                 raise # Re-raise to be caught by outer try-finally for file closing
            except (PDFPageCountError, PDFSyntaxError, PDFPopplerTimeoutError) as e:
                print(f"**PDF processing error on page {page_num}: {e}. Skipping page text.**")
                current_batch_text_list.append(f"--- Page {page_num} ---\n[PDF Processing Error on this page: {e}]\n\n")
            except pytesseract.TesseractNotFoundError:
                print("**Error: Tesseract executable not found. (Ensure Tesseract is installed and configured).**")
                raise # Re-raise
            except pytesseract.TesseractError as te:
                print(f"**Tesseract OCR error on page {page_num}: {te}. Skipping text for this page.**")
                current_batch_text_list.append(f"--- Page {page_num} ---\n[OCR Error on this page: {te}]\n\n")
            except Exception as e:
                print(f"**An unexpected error occurred processing page {page_num}: {e}. Skipping page text.**")
                current_batch_text_list.append(f"--- Page {page_num} ---\n[Unexpected Error processing this page: {e}]\n\n")

            # Check if it's time to write the batch
            if page_num % write_batch_size == 0 or page_num == total_pages:
                if current_batch_text_list:
                    print(f"**Writing text for pages up to {page_num} to '{output_txt_file}'...**")
                    batch_text_to_write = "".join(current_batch_text_list)
                    output_file_object.write(batch_text_to_write)
                    output_file_object.flush() # Ensure data is written to disk
                    current_batch_text_list = [] # Clear the batch
                # Optional: gc.collect() if memory is extremely tight, but use with caution
                # if (page_num % (write_batch_size * 5) == 0): gc.collect()


        print(f"**OCR process complete. All text has been incrementally saved to '{output_txt_file}'**")
        return True

    except PDFInfoNotInstalledError: # From initial pdfinfo_from_path call
        print("**Error: Poppler not installed or not found in PATH. `pdfinfo_from_path` requires Poppler.**")
        print("**Please install Poppler and ensure its 'bin' directory is added to your system's PATH.**")
        return False
    except pytesseract.TesseractNotFoundError: # If re-raised from loop
        # Message already printed
        return False
    except Exception as e:
        print(f"**An overall error occurred during the OCR process: {e}**")
        return False
    finally:
        if output_file_object:
            print(f"**Closing output file: {output_txt_file}**")
            output_file_object.close()


def positive_int(value):
    """Custom argparse type for positive integers."""
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extracts text from an image-based PDF using OCR (iterative page processing, incremental writing) and saves it to a text file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "pdf_filepath",
        help="Path to the input image-based PDF file."
    )
    parser.add_argument(
        "-o", "--output",
        help="Path for the output text file.\n"
             "If not specified, defaults to '[input_pdf_name]_extracted_text.txt'\n"
             "in the same directory as the input PDF.",
        default=None
    )
    parser.add_argument(
        "-l", "--lang",
        help="Language code for Tesseract OCR (e.g., 'eng', 'spa', 'fra').\n"
             "Default is 'eng'. Ensure the language pack is installed for Tesseract.",
        default='eng'
    )
    parser.add_argument(
        "--dpi",
        type=positive_int, # Use custom type for validation
        help="Dots Per Inch for converting PDF pages to images (positive integer).\n"
             "Higher DPI (e.g., 300, 400) can improve OCR accuracy but increases processing time and memory usage.\n"
             "Default is 300.",
        default=300
    )
    parser.add_argument(
        "--batch-write",
        type=positive_int, # Use custom type for validation
        help="Number of pages to process before writing their collected text to the output file (positive integer).\n"
             "Default is 10.",
        default=10
    )

    args = parser.parse_args()

    input_pdf_path = args.pdf_filepath
    output_file_path = args.output
    ocr_lang = args.lang
    image_conversion_dpi = args.dpi
    write_batch_pages = args.batch_write

    # Validate input PDF path
    if not os.path.exists(input_pdf_path):
        print(f"**Error: Input PDF file not found at '{input_pdf_path}'**")
        parser.print_help()
        exit(1)
    if not input_pdf_path.lower().endswith(".pdf"):
        print(f"**Error: The provided input file '{input_pdf_path}' does not appear to be a PDF file.**")
        parser.print_help()
        exit(1)

    # Determine output file path if not specified
    if output_file_path is None:
        input_directory = os.path.dirname(os.path.abspath(input_pdf_path))
        base_filename_without_ext = os.path.splitext(os.path.basename(input_pdf_path))[0]
        output_file_path = os.path.join(input_directory, f"{base_filename_without_ext}_extracted_text.txt")
    output_file_path = os.path.abspath(output_file_path) # Ensure it's an absolute path

    success = ocr_pdf_to_text(
        pdf_path=input_pdf_path,
        output_txt_file=output_file_path,
        lang=ocr_lang,
        dpi_value=image_conversion_dpi,
        write_batch_size=write_batch_pages
    )

    if success:
        print(f"**Script finished successfully.**")
    else:
        print(f"**Script finished with errors.**")
        exit(1)