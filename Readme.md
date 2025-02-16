# Grid Trading Bot Setup Guide

## Prerequisites
- Python 3.7 or higher
- pip (Python package installer)
- Git (optional)

## Installation Steps

1. Create a new directory for your project:
```bash
mkdir grid-trading-bot
cd grid-trading-bot
```

2. Create a Python virtual environment and activate it:
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install required dependencies:
```bash
pip install flask requests
```

4. Create the following file structure:
```
grid-trading-bot/
├── static/
├── templates/
│   └── index.html      # Copy the first HTML file here
├── app.py              # Copy the second Python file here
└── virtual_account.json # This will be created automatically
```

5. Copy the provided HTML code into `templates/index.html`
   - Make sure to preserve all the JavaScript code within the script tags

6. Copy the provided Python code into `app.py`

## Running the Application

1. Make sure your virtual environment is activated:
```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

2. Start the Flask development server:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Using the Grid Trading Bot

1. When you first load the application, you'll see:
   - Virtual balance display ($20,000 USDT initial balance)
   - Real-time price chart
   - Grid configuration panel
   - Trading performance metrics

2. To start grid trading:
   - Click "Calculate Optimal Grid" to get suggested parameters
   - Or manually set your preferred:
     - Upper price
     - Lower price
     - Grid levels
     - Quantity per grid
   - Click "Start Grid Trading"

3. Monitor your trading:
   - Watch the price chart with grid levels
   - Monitor PnL in real-time
   - View recent trades in the trades table
   - Check debug information for detailed logs

4. Reset your account:
   - Click "Reset Account" to start over with initial balance

## Troubleshooting

1. If you see "Error fetching market price":
   - Check your internet connection
   - Verify the CoinDCX API is accessible
   - Wait a few seconds and try again

2. If grid trading doesn't start:
   - Check your virtual balance
   - Verify grid parameters are valid
   - Look at the debug log for specific errors

3. If the web interface doesn't load:
   - Verify Flask server is running
   - Check browser console for JavaScript errors
   - Ensure all files are in correct locations

## Development Notes

- The application uses Flask's development server
- Real-time price data comes from CoinDCX API
- All trades are simulated (no real money involved)
- Account state is persisted in `virtual_account.json`

## Security Considerations

- This is a test/simulation environment
- Do not use real API keys or real trading credentials
- Keep the development server behind a firewall
- Don't expose to public internet without proper security measures