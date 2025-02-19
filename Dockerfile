FROM python:3.9

# Set working directory
WORKDIR /app

# Install system dependencies required for building blis & spaCy
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache

# Copy dependency file first for caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN BLIS_ARCH="generic" pip install spacy --no-binary blis
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy model after installing spaCy
RUN python -m spacy download en_core_web_sm

# Create a directory for Hugging Face cache
RUN mkdir -p /root/.cache/huggingface 

# Copy only necessary files (avoiding __pycache__)
COPY src /app/src
COPY config.yaml /app/config.yaml

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
