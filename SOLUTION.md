# Claim Processing Service Solution

This is a solution for the Backend Assessment - Assignment 1. The solution implements a dockerized service for processing dental claims.

## Features

1. **Claim Processing**: Transforms JSON/CSV claim data and stores it in a database.
2. **Unique ID Generation**: Generates a unique ID for each claim.
3. **Net Fee Calculation**: Computes the net fee using the formula: "net fee" = "provider fees" + "member coinsurance" + "member copay" - "Allowed fees".
4. **Top Providers Endpoint**: Returns the top 10 providers by net fees generated, with rate limiting.
5. **Data Validation**: Validates "submitted procedure" (must begin with 'D') and "Provider NPI" (must be a 10-digit number).

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database connection and session management
│   ├── models.py               # SQLModel models
│   ├── api/
│   │   ├── __init__.py
│   │   └── claims.py           # API endpoints
│   └── services/
│       ├── __init__.py
│       └── claim_processor.py  # Claim processing logic
├── tests/
│   ├── __init__.py
│   ├── test_api.py             # API tests
│   └── test_claim_processor.py # Unit tests for claim processor
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── process_csv.py              # Script to process CSV files
```

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLModel**: ORM for database operations
- **PostgreSQL/SQLite**: Database for storing claims
- **Docker**: Containerization
- **Pydantic**: Data validation
- **SlowAPI**: Rate limiting

## API Endpoints

1. **POST /claims/process**: Process claims from JSON payload
2. **POST /claims/process-csv**: Process claims from CSV file
3. **GET /claims/top-providers**: Get top providers by net fee (rate limited to 10 requests per minute)
4. **GET /**: Root endpoint
5. **GET /health**: Health check endpoint

## Communication with Payments Service

The solution proposes a message queue-based communication between the claim_process and payments services:

1. **Message Queue Communication**:
   - After processing a claim, claim_process publishes a message to a queue
   - The payments service subscribes to this queue and processes the payment

2. **Handling Failures**:
   - Uses a transactional outbox pattern to ensure message delivery
   - Stores outgoing messages in a database table as part of the claim processing transaction
   - A separate process reads from this table and publishes messages to the queue
   - If the payments service fails, it publishes a failure message to another queue

3. **Handling Concurrent Processing**:
   - Uses message deduplication to prevent duplicate processing
   - Includes a unique claim ID in each message
   - The payments service checks if a payment has already been processed for a given claim ID
   - Uses distributed locks to prevent concurrent processing of the same claim

## Running the Application

### Using Docker Compose

```bash
docker-compose up
```

This will start both the PostgreSQL database and the web service.

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

## Testing

Run the tests with:

```bash
pytest
```

## Performance Optimization

The top providers endpoint is optimized for performance using:

1. Database indexing on the provider_npi field
2. Efficient SQL query with GROUP BY and ORDER BY
3. Rate limiting to prevent abuse

The algorithm has:
- Time complexity: O(n log n) where n is the number of providers
- Space complexity: O(n) for storing the aggregated results
