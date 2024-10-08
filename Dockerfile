# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies, including PostgreSQL client and Playwright dependencies
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    libpq-dev \
    pkg-config \
    curl \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    # Required for Playwright
    libdrm2 \
    libgbm1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Debugging step: Check installed packages
RUN pip list

# Install Pre-commit (for development use)
RUN pip install pre-commit

# Install Playwright and its browsers
RUN pip install playwright && python -m playwright install

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=app.settings

# Debugging step: List contents of /app
RUN ls -la /app

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000 for the application
EXPOSE 8000

# Install Uvicorn
RUN pip install uvicorn

# Run the application with Uvicorn
CMD ["uvicorn", "app.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
