from celery import shared_task
from .models import CourseMaterial
import logging

logger = logging.getLogger(__name__)


@shared_task
def upload_materials(course, week_number, files):
    """
    Upload materials asynchronously.

    This task uploads materials for a specified course and week asynchronously,
    creating CourseMaterial objects for each uploaded file.

    :param course: The Course instance for which materials are being uploaded.
    :type course: Course
    :param week_number: The week number for which materials are being uploaded.
    :type week_number: int
    :param files: A dictionary containing the uploaded files.
    :type files: dict

    :return: A tuple containing the number of successfully uploaded materials and a list of failed uploads.
    :rtype: tuple[int, list[dict]]

    :raises: Any exception raised during the upload process.

    The function iterates over each uploaded file and attempts to create a CourseMaterial object
    for it. If successful, the counter for successful uploads is incremented. If an error occurs
    during the upload process, the details of the failed upload are logged, and the file is added
    to the list of failed uploads.

    Example Usage:
    ```
    num_of_materials, failed_materials = upload_materials(course_instance, 3, {'file1': <File>, 'file2': <File>})
    ```
    """
    num_of_materials = 0
    failed_materials = []

    # Iterate over each uploaded material
    for material in files:
        try:
            # Create a CourseMaterial object for the uploaded material
            course_material = CourseMaterial.objects.create(
                course=course,
                week_number=week_number,
                material=material,
            )
            num_of_materials += 1  # Increment the counter for successful uploads
        except Exception as e:
            # Log the error and add the failed material to the list
            failed_materials.append(
                {"material_name": material.name, "error_message": str(e)}
            )
            logger.error(f"Failed to upload material: {material.name}. Error: {e}")

    return num_of_materials, failed_materials
