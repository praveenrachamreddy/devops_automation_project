# Simple MCP Server (Currency Conversion)

This is an MCP (Model Context Protocol) server that provides currency conversion tools for use with the Google Agent Development Kit (ADK). It uses the FastMCP framework and connects to the Frankfurter API to get real-time exchange rates.

## Features

The server provides the following tools for currency conversion:

1. **`get_exchange_rate`**: Get current exchange rates between two currencies
2. **`list_currencies`**: List all available currencies supported by the API
3. **`convert_amount`**: Convert a specific amount from one currency to another

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The server can be run as a standalone HTTP service:

```bash
python server.py
```

By default, it will start on port 8080. You can change the port by setting the `PORT` environment variable.

## Environment Variables

- `PORT`: Port to run the server on (default: 8080)

## Tools API

### get_exchange_rate
Get the current exchange rate between two currencies.

Parameters:
- `currency_from` (optional): The currency to convert from (e.g., "USD"). Defaults to "USD".
- `currency_to` (optional): The currency to convert to (e.g., "EUR"). Defaults to "EUR".
- `currency_date` (optional): The date for the exchange rate or "latest". Defaults to "latest".

Returns:
```json
{
  "amount": 1.0,
  "base": "USD",
  "date": "2025-09-02",
  "rates": {
    "EUR": 0.85
  }
}
```

### list_currencies
List all available currencies supported by the API.

Parameters:
- None

Returns:
```json
{
  "AUD": "Australian Dollar",
  "BGN": "Bulgarian Lev",
  "BRL": "Brazilian Real",
  // ... more currencies
}
```

### convert_amount
Convert a specific amount from one currency to another.

Parameters:
- `amount`: The amount to convert.
- `currency_from` (optional): The currency to convert from (e.g., "USD"). Defaults to "USD".
- `currency_to` (optional): The currency to convert to (e.g., "EUR"). Defaults to "EUR".
- `currency_date` (optional): The date for the exchange rate or "latest". Defaults to "latest".

Returns:
```json
{
  "original_amount": 100,
  "from_currency": "USD",
  "to_currency": "EUR",
  "exchange_rate": 0.85,
  "converted_amount": 85.0,
  "date": "2025-09-02"
}
```

## Testing the Server

You can test if the server is running correctly by making a request to list the available tools:

```bash
curl http://localhost:8080/mcp
```

## API Used

This server uses the [Frankfurter API](https://www.frankfurter.app/) which provides real-time and historical foreign exchange rates.

The Frankfurter API is free to use and doesn't require authentication. It provides exchange rates from the European Central Bank.