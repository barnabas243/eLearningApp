# Use an official Python runtime as a parent image
FROM python:3.10.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /eLearningApp/

# Install Python dependencies
COPY requirements.txt /eLearningApp/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /eLearningApp/

# Run migrations and collect static files (replace with appropriate commands)
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Expose the port on which the Django app will run
EXPOSE 8000

# Define the command to run the Django app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
