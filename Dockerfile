# Use a slim Python 3.11 image
FROM python:3.11-slim

# Install system packages needed for compiling and PDF exporting
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy python dependencies and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set up database file permissions for non-root containers (like Hugging Face Spaces)
RUN touch /app/local_firestore_db.json && \
    chmod -R 777 /app && \
    chown -R 1000:1000 /app

# Switch to standard non-root user (UID 1000 is used by Hugging Face)
USER 1000

# Set environment configurations
ENV PORT=7860
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False
ENV PYTHONPATH=/app

# Expose target port
EXPOSE 7860

# Run application using gunicorn WSGI server
CMD ["gunicorn", "backend.app:app", "-b", "0.0.0.0:7860", "--workers", "2", "--threads", "4", "--timeout", "120"]
