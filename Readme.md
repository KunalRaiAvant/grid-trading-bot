Based on the code provided, this appears to be a Grid Trading Bot simulation system. Let me break down the key components:

1. Frontend (HTML/JavaScript):
- A web interface that displays:
  - Virtual account balance (USDT and OM tokens)
  - Trading performance metrics (Total PnL, Realized/Unrealized PnL)
  - Real-time price chart
  - Grid visualization
  - Recent trades table
  - Grid configuration controls

2. Backend (Python/Flask):
- Manages a virtual trading account with:
  - Balance tracking
  - Order placement
  - Trade history
  - PnL calculations
- Implements grid trading strategy logic:
  - Automatically calculates optimal grid parameters based on current price
  - Places buy/sell orders at calculated price levels
  - Monitors price movements for order execution

3. Key Features:
- Test Mode: Uses virtual balance ($20,000 USDT initial balance)
- Grid Trading Strategy:
  - Creates multiple buy/sell orders at different price levels
  - Automatically buys when price hits lower levels
  - Automatically sells when price hits upper levels
  - Aims to profit from price oscillations within a range
- Real-time price monitoring
- Performance tracking (win rate, PnL, etc.)
- Account reset functionality

4. Grid Trading Parameters:
- Upper/Lower price bounds
- Number of grid levels (default 6)
- Quantity per grid
- Automatic grid spacing calculation

This system allows users to test grid trading strategies without risking real money, while providing real-time feedback on performance and trade execution.

Would you like me to explain any specific component in more detail?