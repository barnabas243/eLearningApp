from celery import shared_task
from PIL import Image


@shared_task
def process_image(photo_path):
    try:
        with Image.open(photo_path) as img:
            img.thumbnail((256, 256))
            img.save(photo_path)

        print("success")
    except Exception as e:
        # Handle exceptions
        print(f"Error processing image: {e}")