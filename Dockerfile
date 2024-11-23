FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

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
    libdrm2 \
    libgbm1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

RUN pip list

RUN pip install pre-commit

RUN pip install playwright && python -m playwright install

COPY . .

ENV DJANGO_SETTINGS_MODULE=app.settings

RUN ls -la /app

RUN python manage.py collectstatic --noinput

EXPOSE 8000

RUN pip install uvicorn

CMD ["uvicorn", "app.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
