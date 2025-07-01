# Use a slim Python base image
FROM python:3.10-slim

# Set environment variables to avoid prompts and cache models under /app/cache
ENV TRANSFORMERS_CACHE=/app/cache
ENV TORCH_HOME=/app/cache

# Create working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Pre-download DialoGPT-small tokenizer and model
RUN python - << 'EOF'
from transformers import AutoTokenizer, AutoModelForCausalLM
# Force download into $TRANSFORMERS_CACHE
AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
EOF

# Copy your app code
COPY . /app/

# Expose port
EXPOSE 5000

# Command to run both files together
CMD ["sh", "-c", "python main.py & python dumb.py && wait"]

