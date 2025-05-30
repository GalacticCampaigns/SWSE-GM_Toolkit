# """
# SCRIPT: PDF Image OCR Extractor (Command-Line Version - Iterative, Incremental, Skip Pages)
#
# DESCRIPTION:
# This script performs Optical Character Recognition (OCR) on image-based PDF files.
# It converts PDF pages to images iteratively (one page at a time) to manage memory.
# Extracted text is written to the output file incrementally in batches.
# Allows skipping a specified number of initial pages (e.g., covers).
#
# REQUIREMENTS:
# 1.  Python 3.x
# 2.  Tesseract OCR Engine (configured in PATH or via pytesseract.tesseract_cmd)
# 3.  Poppler Utilities (installed and in PATH)
# 4.  Python Libraries: pip install pytesseract Pillow pdf2image
#
# INPUT:
# -   Primary input is the file path to an image-based PDF (command-line argument).
# -   Optional arguments for output file, OCR language, DPI, write batch size, and pages to skip.
#
# OUTPUT:
# -   A single .txt file containing all extracted text, written incrementally.
# -   Default output: "[input_pdf_name]_extracted_text.txt" in input PDF's directory.
#
# USAGE:
#   python pdf_ocr_tool.py path/to/your/document.pdf
#   python pdf_ocr_tool.py document.pdf --skip-pages 2 -o output.txt --lang spa --dpi 200 --batch-write 20
#
#   For detailed help: python pdf_ocr_tool.py -h
#
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
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Example for Linux/macOS:
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

def ocr_pdf_to_text(pdf_path: str, output_txt_file: str, lang: str = 'eng',
                    dpi_value: int = 300, write_batch_size: int = 10,
                    skip_first_n_pages: int = 0) -> bool:
    """
    Performs OCR on PDF pages iteratively, writing extracted text incrementally in batches,
    and skipping a specified number of initial pages.

    Args:
        pdf_path (str): Path to the input PDF.
        output_txt_file (str): Path for the output text file.
        lang (str): OCR language code for Tesseract.
        dpi_value (int): DPI for PDF to image conversion.
        write_batch_size (int): Number of pages to process before writing their text.
        skip_first_n_pages (int): Number of pages to skip from the beginning of the PDF.

    Returns:
        bool: True if OCR was successful or no pages needed processing, False otherwise.
    """
    print(f"**Starting OCR process for: {pdf_path}**")
    print(f"**Output will be saved to: {output_txt_file}**")
    print(f"**OCR Language: {lang}, DPI: {dpi_value}, Write Batch Size: {write_batch_size} pages, Skip First: {skip_first_n_pages} pages**")

    current_batch_text_list = []
    output_file_object = None
    num_pages_actually_processed_so_far = 0

    try:
        # 1. Get PDF page count
        print(f"**Getting PDF info for {pdf_path}...**")
        info = pdfinfo_from_path(pdf_path) # Add poppler_path if needed
        total_pages_in_pdf = info["Pages"]

        if skip_first_n_pages > 0:
            print(f"**Skipping the first {skip_first_n_pages} page(s) as requested.**")

        if skip_first_n_pages >= total_pages_in_pdf:
            print(f"**Number of pages to skip ({skip_first_n_pages}) is greater than or equal to total pages ({total_pages_in_pdf}). No pages will be processed.**")
            # Optionally create an empty output file or a file with a note
            try:
                output_dir = os.path.dirname(os.path.abspath(output_txt_file))
                if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
                with open(output_txt_file, "w", encoding="utf-8") as outfile:
                    outfile.write(f"--- No pages processed. Skipped {skip_first_n_pages} of {total_pages_in_pdf} total pages. ---\n")
                print(f"**Empty/note file created at '{output_txt_file}'.**")
            except Exception as e_file:
                print(f"**Could not write note to output file: {e_file}**")
            return True # Operation successful as per instruction, though no OCR done.

        first_page_to_ocr = 1 + skip_first_n_pages
        num_pages_targeted_for_ocr = total_pages_in_pdf - skip_first_n_pages

        print(f"**PDF has {total_pages_in_pdf} pages. Targeting pages {first_page_to_ocr} to {total_pages_in_pdf} for OCR ({num_pages_targeted_for_ocr} pages).**")
        print(f"**Writing text incrementally every {write_batch_size} processed pages.**")

        # 2. Open output file in write mode
        output_dir = os.path.dirname(os.path.abspath(output_txt_file))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"**Created output directory: {output_dir}**")
        output_file_object = open(output_txt_file, "w", encoding="utf-8")

        # 3. Iterate through targeted pages
        for actual_pdf_page_num in range(first_page_to_ocr, total_pages_in_pdf + 1):
            num_pages_actually_processed_so_far += 1
            print(f"**Processing PDF page {actual_pdf_page_num} (Processed count: {num_pages_actually_processed_so_far} of {num_pages_targeted_for_ocr})...**")

            try:
                page_images = convert_from_path(
                    pdf_path,
                    dpi=dpi_value,
                    first_page=actual_pdf_page_num,
                    last_page=actual_pdf_page_num,
                    grayscale=True,
                )

                if not page_images:
                    print(f"**Warning: Could not convert PDF page {actual_pdf_page_num}. Skipping.**")
                    current_batch_text_list.append(f"--- Page {actual_pdf_page_num} ---\n[Conversion Error on this page]\n\n")
                else:
                    image_obj = page_images[0]
                    tesseract_config = '--oem 1'
                    page_text = pytesseract.image_to_string(image_obj, lang=lang, config=tesseract_config)
                    current_batch_text_list.append(f"--- Page {actual_pdf_page_num} ---\n")
                    current_batch_text_list.append(page_text)
                    current_batch_text_list.append("\n\n")
                    del image_obj
                    del page_images

            except PDFInfoNotInstalledError: raise
            except (PDFPageCountError, PDFSyntaxError, PDFPopplerTimeoutError) as e:
                print(f"**PDF processing error on PDF page {actual_pdf_page_num}: {e}. Skipping.**")
                current_batch_text_list.append(f"--- Page {actual_pdf_page_num} ---\n[PDF Processing Error: {e}]\n\n")
            except pytesseract.TesseractNotFoundError: raise
            except pytesseract.TesseractError as te:
                print(f"**Tesseract OCR error on PDF page {actual_pdf_page_num}: {te}. Skipping.**")
                current_batch_text_list.append(f"--- Page {actual_pdf_page_num} ---\n[OCR Error: {te}]\n\n")
            except Exception as e:
                print(f"**Unexpected error on PDF page {actual_pdf_page_num}: {e}. Skipping.**")
                current_batch_text_list.append(f"--- Page {actual_pdf_page_num} ---\n[Unexpected Error: {e}]\n\n")

            # Check if it's time to write the batch
            # Condition: (batch size met) OR (it's the very last page of the PDF to be processed)
            if num_pages_actually_processed_so_far % write_batch_size == 0 or actual_pdf_page_num == total_pages_in_pdf:
                if current_batch_text_list:
                    print(f"**Writing batch to '{output_txt_file}' (up to PDF page {actual_pdf_page_num})...**")
                    batch_text_to_write = "".join(current_batch_text_list)
                    output_file_object.write(batch_text_to_write)
                    output_file_object.flush()
                    current_batch_text_list = []

        print(f"**OCR process complete. All targeted text has been incrementally saved to '{output_txt_file}'**")
        return True

    except PDFInfoNotInstalledError:
        print("**Error: Poppler not installed/found. Cannot get PDF info or convert pages.**")
        return False
    except pytesseract.TesseractNotFoundError:
        print("**Error: Tesseract not found. Please install/configure Tesseract.**")
        return False
    except Exception as e:
        print(f"**An overall error occurred during the OCR process: {e}**")
        return False
    finally:
        if output_file_object:
            print(f"**Closing output file: {output_txt_file}**")
            output_file_object.close()


def strictly_positive_int(value):
    """Custom argparse type for strictly positive integers (>0)."""
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"{value} must be a positive integer greater than 0")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")

def non_negative_int(value):
    """Custom argparse type for non-negative integers (>=0)."""
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError(f"{value} must be a non-negative integer (0 or greater)")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extracts text from an image-based PDF using OCR (iterative, incremental, skips pages) and saves it.",
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
        help="Language code for Tesseract OCR (e.g., 'eng', 'spa', 'fra'). Default: 'eng'.",
        default='eng'
    )
    parser.add_argument(
        "--dpi",
        type=strictly_positive_int,
        help="Dots Per Inch for PDF to image conversion (>0). Default: 300.",
        default=300
    )
    parser.add_argument(
        "--batch-write",
        type=strictly_positive_int,
        help="Number of pages to process before an incremental write to the output file (>0). Default: 10.",
        default=10
    )
    parser.add_argument(
        "--skip-pages",
        type=non_negative_int,
        help="Number of pages to skip from the beginning of the PDF (0 or more). Default: 0.",
        default=0
    )

    args = parser.parse_args()

    # Validate input PDF path (basic check)
    if not os.path.exists(args.pdf_filepath):
        print(f"**Error: Input PDF file not found at '{args.pdf_filepath}'**")
        parser.print_help()
        exit(1)
    if not args.pdf_filepath.lower().endswith(".pdf"):
        print(f"**Error: Input file '{args.pdf_filepath}' does not appear to be a PDF.**")
        parser.print_help()
        exit(1)

    # Determine output file path
    output_file_path = args.output
    if output_file_path is None:
        input_directory = os.path.dirname(os.path.abspath(args.pdf_filepath))
        base_filename_without_ext = os.path.splitext(os.path.basename(args.pdf_filepath))[0]
        output_file_path = os.path.join(input_directory, f"{base_filename_without_ext}_extracted_text.txt")
    output_file_path = os.path.abspath(output_file_path)

    success = ocr_pdf_to_text(
        pdf_path=args.pdf_filepath,
        output_txt_file=output_file_path,
        lang=args.lang,
        dpi_value=args.dpi,
        write_batch_size=args.batch_write,
        skip_first_n_pages=args.skip_pages
    )

    if success:
        print(f"**Script finished successfully.**")
    else:
        print(f"**Script finished with errors.**")
        exit(1)