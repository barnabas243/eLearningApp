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

# Install Nginx
RUN apt-get update && apt-get install -y nginx

# Copy the nginx.conf file to /etc/nginx/
COPY nginx.conf /etc/nginx/

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt 

# Change ownership of the application directory to appuser
# RUN chown -R appuser:appuser .

# Switch to the non-privileged user to run the application.
# USER appuser

# Copy the source code into the container.
COPY . /eLearningApp/

# RUN python manage.py collectstatic --no-input

COPY docs /eLearningApp/static/docs/


# Expose the port that the application listens on.
EXPOSE 8000

# Define the command to run the Django app with Daphne
CMD service redis-server start && celery -A eLearningApp worker -l INFO & nginx -g 'daemon off;' && daphne -b 0.0.0.0 -p 8000 eLearningApp.asgi:application
