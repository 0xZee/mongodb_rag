# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .
COPY app_tools.py .

# Expose the port Streamlit will run on
EXPOSE 8501

# Create a non-root user
RUN useradd -m myuser
USER myuser

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py"]

##################################################
# TO BUILD THE DOCKERFILE :
# docker build -t mongodb-rag-app .
# docker run -p 8501:8501 \
#     -e GROQ_API_KEY=your_groq_api_key \
#     -e COHERE_DEV_API=your_cohere_api_key \
#     -e MONGO_URI=your_mongodb_connection_string \
#     mongodb-rag-app
##################################################
