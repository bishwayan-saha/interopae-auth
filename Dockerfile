# Use an official Python base image
FROM python:3.13.3-slim

ENV ACCEPT_EULA=Y
ENV SERVER_DOMAIN=http://4.247.183.66

RUN apt-get update && \
    apt-get install -y curl apt-transport-https gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    apt-get install -y msodbcsql17 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the application port
EXPOSE 5002

# Set the entrypoint command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5002"]