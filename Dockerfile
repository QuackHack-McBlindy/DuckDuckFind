# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5556 for the Flask app
EXPOSE 5556

# Run the command to update the documents when the container starts
CMD ["sh", "-c", "python app.py"]

