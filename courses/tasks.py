from PIL import Image
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_image(photo_path):
    """
    Process an image asynchronously.

    This task processes an image by resizing it to a thumbnail of 256x256 pixels.
    The processed image is then saved back to the original path.

    :param photo_path: The path to the image file.
    :type photo_path: str
    """
    try:
        with Image.open(photo_path) as img:
            img.thumbnail((256, 256))
            img.save(photo_path)

        logger.info("Image processing successful: %s", photo_path)
    except Exception as e:
        # Log the exception and any relevant details
        logger.error("Error processing image: %s", e, exc_info=True)
