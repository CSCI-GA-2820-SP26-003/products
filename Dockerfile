FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY Pipfile Pipfile.lock ./
RUN pip install --upgrade pip pipenv && \
    pipenv install --system --deploy

# Copy application code
COPY service/ ./service/
COPY wsgi.py ./

# Expose port
EXPOSE 8080

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--log-level", "info", "wsgi:app"]