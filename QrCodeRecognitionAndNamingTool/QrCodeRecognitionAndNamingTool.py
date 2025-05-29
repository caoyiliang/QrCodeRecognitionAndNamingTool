import os
import sys
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image
import fitz  # PyMuPDF, used to render PDF pages as images
import cv2
import numpy as np

def detect_and_crop_qr_code(image):
    """
    Detect and crop the QR code region using OpenCV
    """
    try:
        # Ensure the image is in RGB format
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Convert to grayscale
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        detector = cv2.QRCodeDetector()
        _, points = detector.detect(gray)
        if points is not None:
            # Get the bounding box of the QR code
            points = points[0]
            x_min = int(min(points[:, 0]))
            y_min = int(min(points[:, 1]))
            x_max = int(max(points[:, 0]))
            y_max = int(max(points[:, 1]))
            print(f"QR code detected at: ({x_min}, {y_min}), ({x_max}, {y_max})")
            return image.crop((x_min, y_min, x_max, y_max))  # Crop the QR code region
        else:
            print("No QR code detected, returning the full image")
    except Exception as e:
        print(f"QR code detection failed: {e}")
    return image  # Return the full image if no QR code is detected

def preprocess_image(image):
    """
    Preprocess the image to enhance QR code detection
    """
    try:
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return Image.fromarray(binary)
    except Exception as e:
        print(f"Image preprocessing failed: {e}")
        return image

def extract_qr_code_from_pdf(pdf_path):
    """
    Extract QR code content from the first page of a PDF
    """
    try:
        # Use a context manager to ensure the PDF file is properly closed
        with fitz.open(pdf_path) as pdf_document:
            page = pdf_document[0]
            pix = page.get_pixmap(dpi=300)  # Increase DPI for better image quality
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Preprocess the image
            image = preprocess_image(image)

            # Automatically detect and crop the QR code region
            cropped_image = detect_and_crop_qr_code(image)

            # Save the cropped image for debugging
            # debug_image_path = os.path.join(os.path.dirname(pdf_path), "debug_image.png")
            # cropped_image.save(debug_image_path)

            # Decode the QR code using pyzbar
            qr_codes = decode(cropped_image, symbols=[ZBarSymbol.QRCODE])
            if qr_codes:
                return qr_codes[0].data.decode("utf-8")  # Return the content of the first QR code

            # If pyzbar fails, try using OpenCV
            print(f"pyzbar failed, trying OpenCV for {pdf_path}")
            qr_content = extract_qr_code_with_opencv(cropped_image)
            if qr_content:
                return qr_content
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    finally:
        # Ensure resources are released
        image.close()
        cropped_image.close()
    return None

def extract_qr_code_with_opencv(image):
    """
    Decode QR code using OpenCV
    """
    try:
        image = np.array(image)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)
        if data:
            print(f"OpenCV successfully decoded: {data}")
        else:
            print("OpenCV failed to decode the QR code")
        return data
    except Exception as e:
        print(f"OpenCV decoding failed: {e}")
        return None

def rename_pdfs_in_folder(folder_path):
    """
    Iterate through all PDF files in the folder, extract QR code content, and rename the files
    """
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            print(f"Processing: {filename}")
            qr_content = extract_qr_code_from_pdf(pdf_path)
            if qr_content:
                new_filename = f"{qr_content}.pdf"
                new_path = os.path.join(folder_path, new_filename)
                # Check if the new filename is the same as the original filename
                if os.path.abspath(pdf_path) == os.path.abspath(new_path):
                    print(f"File name is already correct: {new_filename}, skipping rename")
                    continue
                try:
                    os.rename(pdf_path, new_path)
                    print(f"Renamed to: {new_filename}")
                except FileExistsError:
                    print(f"File {new_filename} already exists, skipping rename")
                except Exception as e:
                    print(f"Error renaming {filename}: {e}")
            else:
                print(f"QR code not found in {filename}")

if __name__ == "__main__":
    # Dynamically determine the current folder based on the environment
    if getattr(sys, 'frozen', False):  # Check if running in a frozen (packaged) environment
        current_folder = os.path.dirname(sys.executable)  # Path to the EXE file
    else:
        current_folder = os.path.dirname(os.path.abspath(__file__))  # Path to the script

    print(f"Current folder: {current_folder}")
    rename_pdfs_in_folder(current_folder)