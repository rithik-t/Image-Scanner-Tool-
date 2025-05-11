from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, BlipProcessor, BlipForConditionalGeneration
import torch
import exifread

# Load AI models
ocr_processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
ocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def extract_text(image_path):
    """Extract handwritten/printed text using TrOCR."""
    image = Image.open(image_path).convert("RGB")
    pixel_values = ocr_processor(images=image, return_tensors="pt").pixel_values
    generated_ids = ocr_model.generate(pixel_values)
    text = ocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return text.strip()

def convert_to_degrees(value):
    """Convert EXIF GPS coordinates to decimal degrees."""
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0)

def extract_metadata(image_path):
    """Extract EXIF metadata including GPS and Google Maps link."""
    metadata = {}

    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

        # Store all metadata
        for tag in tags:
            metadata[tag] = str(tags[tag])

        # Extract and convert GPS coordinates
        try:
            gps_latitude = tags.get('GPS GPSLatitude')
            gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
            gps_longitude = tags.get('GPS GPSLongitude')
            gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                print(f"GPS GPSLatitude: {gps_latitude.values}")
                print(f"GPS GPSLatitudeRef: {gps_latitude_ref.values}")
                print(f"GPS GPSLongitude: {gps_longitude.values}")
                print(f"GPS GPSLongitudeRef: {gps_longitude_ref.values}")

                lat = convert_to_degrees(gps_latitude)
                lon = convert_to_degrees(gps_longitude)

                if gps_latitude_ref.values[0] != 'N':
                    lat = -lat
                if gps_longitude_ref.values[0] != 'E':
                    lon = -lon

                location_url = f"https://maps.google.com/?q={lat},{lon}"
                print(f"✅ Location Found: {location_url}")

                metadata['GPS Latitude'] = lat
                metadata['GPS Longitude'] = lon
                metadata['Google Maps Location'] = location_url
            else:
                print("❌ GPS tags not found. No location available.")
        except Exception as e:
            metadata['GPS Error'] = f"Failed to parse GPS info: {e}"

    return metadata

def describe_image(image_path):
    """Generate a caption for the image using BLIP."""
    raw_image = Image.open(image_path).convert('RGB')
    inputs = caption_processor(raw_image, return_tensors="pt")
    with torch.no_grad():
        out = caption_model.generate(**inputs)
    caption = caption_processor.decode(out[0], skip_special_tokens=True)
    return caption

def is_ai_generated_by_exif(exif_data: dict) -> bool:
    """Heuristic to detect AI-generated images based on EXIF metadata."""
    if not exif_data:
        return True  # No metadata at all – likely AI

    important_tags = [
        'Image Make', 'Image Model', 'EXIF DateTimeOriginal',
        'EXIF FocalLength', 'EXIF ISOSpeedRatings'
    ]

    missing = [tag for tag in important_tags if tag not in exif_data]

    return len(missing) >= 3  # Missing many camera-related tags
