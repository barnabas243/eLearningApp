# syntax=docker/dockerfile:1

# Use Python slim image as base
ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /eLearningApp/

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt 

# Copy the source code into the container.
COPY . /eLearningApp/

# Run collectstatic command
RUN python manage.py collectstatic --no-input
RUN python manage.py migrate

# Copy static docs directory
COPY docs /eLearningApp/static/docs/

# Expose the port that the application listens on.
EXPOSE 8000

# Define the command to run the Django app with Daphne
CMD celery -A eLearningApp worker -l INFO & daphne -b 0.0.0.0 -p 8000 eLearningApp.asgi:application
# celery -A eLearningApp worker -l INFO &