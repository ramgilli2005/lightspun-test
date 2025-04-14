# Claim Processing Service

A dockerized service for processing dental claims.

## Docker Architecture

The application is containerized using Docker with the following components:

- **Web Service**: A FastAPI application that processes dental claims
- **Database**: PostgreSQL database for storing claim data

### Docker Components

- **Dockerfile**: Defines the web service container based on Python 3.12
- **docker-compose.yml**: Orchestrates the web service and database containers

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the containers
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

This will start both the PostgreSQL database and the web service. The API will be available at http://localhost:8000.

### Docker Management Commands

```bash
# Stop the containers
docker-compose down

# View container logs
docker-compose logs

# View logs for a specific service
docker-compose logs web
docker-compose logs db

# Restart services
docker-compose restart

# Rebuild and restart services after code changes
docker-compose up --build
```

### Environment Variables

The Docker setup uses the following environment variables:

- **DATABASE_URL**: Connection string for PostgreSQL (`postgresql://postgres:postgres@db:5432/claims`)
- **POSTGRES_USER**: Database username (`postgres`)
- **POSTGRES_PASSWORD**: Database password (`postgres`)
- **POSTGRES_DB**: Database name (`claims`)

These are pre-configured in the docker-compose.yml file and don't require manual setup.

### Data Persistence

PostgreSQL data is persisted using a Docker volume (`postgres_data`), ensuring your data remains intact even if containers are stopped or removed.

### Testing with Sample Data

Once the service is running, you can test it with the provided sample data:

```bash
# Process claims from the sample JSON file
curl -X POST -H "Content-Type: application/json" -d @sample_claims.json http://localhost:8000/claims/process

# Get top providers by net fee
curl http://localhost:8000/claims/top-providers
```

### Accessing the Database

You can connect to the PostgreSQL database using:

```bash
# Connect to the database container
docker-compose exec db psql -U postgres -d claims

# Or connect using a local PostgreSQL client
psql -h localhost -p 5432 -U postgres -d claims
```

### Running Locally

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Process a CSV file:
   ```bash
   python process_csv.py claim_1234_fixed.csv
   ```

## API Documentation

Once the service is running, you can access the API documentation at:

```
http://localhost:8000/docs
```

The API documentation is generated automatically by FastAPI and provides interactive documentation for all endpoints.

## Features

- Process claims from JSON or CSV
- Calculate net fees
- Get top providers by net fee
- Data validation for submitted procedures and provider NPIs
- Rate limiting for API endpoints

## Testing

### Running Tests in Docker

```bash
# Run tests inside the Docker container
docker-compose exec web pytest
```

### Running Tests Locally

```bash
pytest
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure the database container is running: `docker-compose ps`
   - Check database logs: `docker-compose logs db`
   - Verify the DATABASE_URL environment variable in docker-compose.yml

2. **Port Conflicts**:
   - If port 8000 or 5432 is already in use, modify the port mappings in docker-compose.yml

3. **Container Not Starting**:
   - Check container logs: `docker-compose logs`
   - Ensure all required environment variables are set

### Rebuilding from Scratch

If you need to start fresh:

```bash
# Stop containers and remove volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

## Solution Details

For a detailed explanation of the solution, please see [SOLUTION.md](SOLUTION.md).
