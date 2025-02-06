# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y gcc netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install gunicorn


# Copy project
COPY . /app/

# Collect static files (optional, if using Django staticfiles)
RUN python manage.py collectstatic --noinput

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port 8000
EXPOSE 8000

# Set the entrypoint and command
ENTRYPOINT ["/app/entrypoint.sh"]

# Run Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
