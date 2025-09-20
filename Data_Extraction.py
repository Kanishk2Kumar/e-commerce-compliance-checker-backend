import easyocr
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Root folder where your product images are stored
IMAGE_ROOT = Path("Product-Images")

# Initialize EasyOCR reader (load once)
reader = easyocr.Reader(['en'], gpu=False)  # set gpu=True if you have CUDA

# Output CSV file
OUTPUT_FILE = "extracted_text.csv"

def process_image(product_id, image_file):
    """Run OCR on a single image and return row for CSV."""
    try:
        result = reader.readtext(str(image_file), detail=0)
        extracted_text = " ".join(result) if result else ""
        return [product_id, image_file.name, extracted_text]
    except Exception as e:
        print(f"Error processing {image_file}: {e}")
        return [product_id, image_file.name, ""]

def extract_text_from_images(max_workers=6):
    rows = []

    # Collect all image files first
    image_tasks = []
    for product_dir in IMAGE_ROOT.iterdir():
        if product_dir.is_dir():
            product_id = product_dir.name
            for image_file in product_dir.glob("*.*"):
                if image_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                    image_tasks.append((product_id, image_file))

    print(f"Found {len(image_tasks)} images. Processing with {max_workers} workers...")

    # Run OCR in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_img = {executor.submit(process_image, pid, img): (pid, img) for pid, img in image_tasks}

        for future in as_completed(future_to_img):
            rows.append(future.result())

    # Save to CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["product_id", "image_name", "extracted_text"])
        writer.writerows(rows)

    print(f"\n✅ OCR extraction complete! Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_text_from_images(max_workers=8)  # adjust based on CPU cores
