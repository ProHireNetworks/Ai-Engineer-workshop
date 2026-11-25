# TripMate AI Deployment Guide

## Docker Compose (Local / Staging)
```bash
docker-compose up --build -d
```
Services started:
- `tripmate-backend`: FastAPI application on port 8000.
- `tripmate-postgres`: PostgreSQL 16 with pgvector on port 5432.

## AWS Production Architecture
- **Compute**: AWS ECS Fargate running the containerized FastAPI backend.
- **Database**: Amazon RDS for PostgreSQL with pgvector extension.
- **Storage**: Amazon S3 for travel knowledge documents and export files.
- **Secrets**: AWS Secrets Manager for LLM API keys and database credentials.
- **Load Balancer**: AWS Application Load Balancer (ALB) terminating HTTPS and distributing traffic across Fargate tasks.
- **Monitoring**: AWS CloudWatch for structured container logs and alarms.

