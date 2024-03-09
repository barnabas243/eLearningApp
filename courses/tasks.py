import logging
import os
from celery import shared_task

from courses.models import CourseMaterial
from django.core.files.uploadedfile import SimpleUploadedFile

logger = logging.getLogger(__name__)


@shared_task
def upload_materials(course_id, week_number, temporary_paths):
    """
    Upload materials asynchronously.

    :param course_id: The ID of the course for which materials are being uploaded.
    :type course_id: int
    :param week_number: The week number for which materials are being uploaded.
    :type week_number: int
    :param temporary_paths: List of temporary file paths.
    :type temporary_paths: list[str]
    """
    num_of_materials = 0  # Counter for successfully uploaded materials
    failed_materials = []  # List to store failed uploads

    for temp_path in temporary_paths:
        try:
            # Read the file content
            with open(temp_path, "rb") as file:
                file_content = file.read()

            # Create an InMemoryUploadedFile
            uploaded_file = SimpleUploadedFile(
                name=temp_path.split("/")[-1],  # Extract filename from the path
                content=file_content,
                content_type="application/octet-stream",  # Specify the content type
            )

            # Create a CourseMaterial object for the uploaded material
            course_material = CourseMaterial.objects.create(
                course_id=course_id,
                week_number=week_number,
                material=uploaded_file,
            )
            num_of_materials += 1
        except Exception as e:
            # Log the error and add the failed material to the list
            failed_materials.append(
                {"material_path": temp_path, "error_message": str(e)}
            )
            logger.error(f"Failed to upload material: {temp_path}. Error: {e}")
    # Delete temporary files after processing
    for temp_path in temporary_paths:
        os.remove(temp_path)

    return num_of_materials, failed_materials
