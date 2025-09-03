# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Install the necessary dependencies from requirements.txt
RUN pip install  --no-cache-dir -r requirements.txt

# Expose the port on which your app will run
EXPOSE 8010

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "app.py"]
