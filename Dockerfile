# 1. Use an official Python image
FROM python:3.11-slim

# 2. Set the working directory inside the cloud container
WORKDIR /app

# 3. Copy your requirements file first (to speed up builds)
COPY requirements.txt .

# 4. Install your libraries (FastAPI, Transformers, Torch, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code from your computer to the cloud
COPY . .

# 6. Tell Google Cloud to start the server on port 8080
CMD ["uvicorn", "tests.app:app", "--host", "0.0.0.0", "--port", "8080"]