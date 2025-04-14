# Claim Processing Service

A dockerized service for processing dental claims.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the containers
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

This will start both the PostgreSQL database and the web service. The API will be available at http://localhost:8000.

### Testing with Sample Data

Once the service is running, you can test it with the provided sample data:

```bash
# Process claims from the sample JSON file
curl -X POST -H "Content-Type: application/json" -d @sample_claims.json http://localhost:8000/claims/process

# Get top providers by net fee
curl http://localhost:8000/claims/top-providers
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

## Features

- Process claims from JSON or CSV
- Calculate net fees
- Get top providers by net fee
- Data validation for submitted procedures and provider NPIs
- Rate limiting for API endpoints

## Testing

Run the tests with:

```bash
pytest
```

## Solution Details

For a detailed explanation of the solution, please see [SOLUTION.md](SOLUTION.md).
