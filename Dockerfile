# Use an official Python slim image
FROM python:3.10-slim

# System dependencies for netCDF4, pyproj, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc g++ libproj-dev proj-data proj-bin \
    libgeos-dev libhdf5-dev libnetcdf-dev && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code into the container
COPY . .

EXPOSE 9263

# Start your Bokeh app 
CMD ["bokeh", "serve", "--allow-websocket-origin=*", "--port", "9263", "--show", "ERMES.py"]
