# Parliamentary Meeting Minutes Analysis

## Overview

This FastAPI service queries parliamentary meeting minutes and returns relevant information in a structured format.

## Prerequisites

- Docker
- Docker Compose
- MacOS (ARM64) operating system

## Instructions for how to run the service

### **Quick Start (Recommended)**

If you have Docker Compose installed, simply run:

```sh
docker compose up --build
```

### Manual Steps (If Not Using Docker Compose)

Build the Docker image:

```sh
docker buildx build --platform linux/arm64 --no-cache -t fastapi-parliamentary-meeting-analysis --load .
```

Run the container:

```sh
docker run -p 8000:8000 fastapi-parliamentary-meeting-analysis
```

### API Usage
