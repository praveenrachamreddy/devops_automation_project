import asyncio
import logging
import os

import httpx
from fastmcp import FastMCP

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Currency MCP Server 💵")

@mcp.tool()
def get_exchange_rate(
    currency_from: str = 'USD',
    currency_to: str = 'EUR',
    currency_date: str = 'latest',
):
    """Use this to get current exchange rate.

    Args:
        currency_from: The currency to convert from (e.g., "USD").
        currency_to: The currency to convert to (e.g., "EUR").
        currency_date: The date for the exchange rate or "latest". Defaults to "latest".

    Returns:
        A dictionary containing the exchange rate data, or an error message if the request fails.
    """
    logger.info(f"--- 🛠️ Tool: get_exchange_rate called for converting {currency_from} to {currency_to} ---")
    
    # Validate inputs
    if not currency_from or not currency_to:
        return {'error': 'Both currency_from and currency_to are required.'}
    
    # Convert to uppercase for API consistency
    currency_from = currency_from.upper()
    currency_to = currency_to.upper()
    
    try:
        logger.info(f"Making API request to Frankfurter for {currency_from} to {currency_to} on {currency_date}")
        response = httpx.get(
            f'https://api.frankfurter.app/{currency_date}',
            params={'from': currency_from, 'to': currency_to},
            timeout=10.0  # Add timeout
        )
        response.raise_for_status()

        data = response.json()
        logger.info(f'✅ API response received: {data}')
        
        # Validate response structure
        if 'rates' not in data:
            return {'error': 'Invalid API response format: missing rates data.'}
            
        if currency_to not in data['rates']:
            available_currencies = list(data['rates'].keys())
            return {
                'error': f'Currency {currency_to} not available in the response. Available currencies: {available_currencies}'
            }
            
        return data
    except httpx.TimeoutException:
        return {'error': 'API request timed out. Please try again later.'}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return {'error': f'API request failed: {e}'}
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        return {'error': f'Invalid JSON response from API: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {'error': f'An unexpected error occurred: {e}'}

@mcp.tool()
def list_currencies():
    """List all available currencies supported by the API."""
    logger.info("--- 🛠️ Tool: list_currencies called ---")
    try:
        response = httpx.get('https://api.frankfurter.app/currencies', timeout=10.0)
        response.raise_for_status()
        data = response.json()
        logger.info(f'✅ Currencies retrieved: {list(data.keys())}')
        return data
    except httpx.TimeoutException:
        return {'error': 'API request timed out. Please try again later.'}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return {'error': f'API request failed: {e}'}
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        return {'error': f'Invalid JSON response from API: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {'error': f'An unexpected error occurred: {e}'}

@mcp.tool()
def convert_amount(
    amount: float,
    currency_from: str = 'USD',
    currency_to: str = 'EUR',
    currency_date: str = 'latest',
):
    """Convert a specific amount from one currency to another.
    
    Args:
        amount: The amount to convert.
        currency_from: The currency to convert from (e.g., "USD").
        currency_to: The currency to convert to (e.g., "EUR").
        currency_date: The date for the exchange rate or "latest". Defaults to "latest".
        
    Returns:
        A dictionary with the converted amount and exchange rate information.
    """
    logger.info(f"--- 🛠️ Tool: convert_amount called for {amount} {currency_from} to {currency_to} ---")
    
    # Get exchange rate
    rate_data = get_exchange_rate(currency_from, currency_to, currency_date)
    
    # Check for errors
    if 'error' in rate_data:
        return rate_data
    
    # Calculate converted amount
    if currency_to in rate_data['rates']:
        rate = rate_data['rates'][currency_to]
        converted_amount = amount * rate
        result = {
            'original_amount': amount,
            'from_currency': currency_from,
            'to_currency': currency_to,
            'exchange_rate': rate,
            'converted_amount': converted_amount,
            'date': rate_data.get('date', 'latest')
        }
        logger.info(f'✅ Conversion result: {result}')
        return result
    else:
        return {'error': f'Could not find exchange rate for {currency_to}'}

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    logger.info(f"🚀 Currency MCP Server starting on port {port}")
    logger.info("Available tools: get_exchange_rate, list_currencies, convert_amount")
    logger.info("Server URL will be: http://localhost:%d/mcp", port)
    
    try:
        # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
        asyncio.run(
            mcp.run_async(
                transport="streamable-http",
                host="0.0.0.0",
                port=port,
            )
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")