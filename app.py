from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import time
from datetime import datetime
import threading
import json
from pathlib import Path
import os
import logging

# auth_routes.py
from flask import Blueprint, request, jsonify
from supabase_client import supabase
from functools import wraps


auth_bp = Blueprint('auth', __name__)
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            user = supabase.auth.get_user(token)
            return f(user.user.id, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401
            
    return decorated

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
            
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        return jsonify({
            'access_token': response.session.access_token,
            'user': {
                'id': response.user.id,
                'email': response.user.email
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 401
@auth_bp.route('/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
            
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        return jsonify({
            'access_token': response.session.access_token,
            'user': {
                'id': response.user.id,
                'email': response.user.email
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 401

# Configure logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app) 

class VirtualAccount:
    def __init__(self, initial_balance=20000):
        self.initial_usdt = initial_balance
        self.reset_balance()
        self.orders = []
        self.trades = []
        self.initial_portfolio_value = initial_balance
        self.realized_pnl_applied = set()  # Track which trades' PnL has been applied
        self._load_state()

    def place_order(self, market, side, price, quantity):
        base_asset = market.replace('USDT', '')
        
        order_id = f"order_{int(time.time() * 1000)}_{len(self.orders)}"
        
        # Calculate entry price for the trade
        entry_price = self._calculate_average_entry_price() if side == 'sell' else price
        
        try:
            # Check if we have enough balance
            if side == 'buy':
                cost = float(price) * float(quantity)
                if self.balances['USDT'] < cost:
                    logger.error(f"Insufficient USDT balance. Required: {cost}, Available: {self.balances['USDT']}")
                    return {'error': 'Insufficient USDT balance'}
                self.balances['USDT'] -= cost
                self.balances[base_asset] += float(quantity)
            else:  # sell
                if self.balances[base_asset] < float(quantity):
                    logger.error(f"Insufficient {base_asset} balance. Required: {quantity}, Available: {self.balances[base_asset]}")
                    return {'error': f'Insufficient {base_asset} balance'}
                
                # Calculate and apply realized PnL for sell orders
                if entry_price:
                    realized_pnl = float(quantity) * (float(price) - entry_price)
                    self.balances['USDT'] += float(price) * float(quantity)  # Add the sell proceeds
                    logger.info(f"Realized PnL for trade: {realized_pnl}")
                
                self.balances[base_asset] -= float(quantity)

            # Record the trade
            trade = {
                'order_id': order_id,
                'market': market,
                'side': side,
                'price': float(price),
                'quantity': float(quantity),
                'entry_price': entry_price,
                'timestamp': datetime.now().isoformat(),
                'value': float(price) * float(quantity)
            }
            
            if side == 'sell':
                trade['realized_pnl'] = realized_pnl

            self.orders.append(order)
            self.trades.append(trade)
            self._save_state()
            
            logger.info(f"Order placed successfully: {order_id}")
            return {'id': order_id, 'status': 'SUCCESS'}

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {'error': str(e)}    
    def reset_balance(self):
        self.balances = {
            'USDT': self.initial_usdt,
            'OM': 0,
            'ETH': 0,
            'BNB': 0,
            'XRP': 0,
            'SOL': 0
        }
        logger.info(f"Balance reset to: {self.balances}")

    def _load_state(self):
        try:
            if Path('virtual_account.json').exists():
                with open('virtual_account.json', 'r') as f:
                    data = json.load(f)
                    self.balances = data.get('balances', self.balances)
                    self.orders = data.get('orders', [])
                    self.trades = data.get('trades', [])
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")

    def _save_state(self):
        try:
            with open('virtual_account.json', 'w') as f:
                json.dump({
                    'balances': self.balances,
                    'orders': self.orders,
                    'trades': self.trades
                }, f)
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
    def calculate_pnl(self):
        try:
            current_price = market_data.get_market_price('OMUSDT')
            if not current_price:
                logger.error("Could not fetch current market price")
                return {
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'realized_pnl': 0,
                    'realized_pnl_percent': 0,
                    'unrealized_pnl': 0,
                    'unrealized_pnl_percent': 0,
                    'total_trades': len(self.trades),
                    'win_rate': 0
                }
            
            # Calculate realized PnL from completed trades
            realized_pnl = sum(
                trade.get('realized_pnl', 0) 
                for trade in self.trades 
                if trade['side'] == 'sell'
            )
            
            # Calculate unrealized PnL
            average_entry_price = self._calculate_average_entry_price()
            unrealized_pnl = self.balances['OM'] * (current_price - average_entry_price)
            
            # Calculate total PnL
            total_pnl = realized_pnl + unrealized_pnl
            
            # Calculate percentages
            realized_pnl_percent = (realized_pnl / self.initial_portfolio_value) * 100 if self.initial_portfolio_value != 0 else 0
            unrealized_pnl_percent = (unrealized_pnl / self.initial_portfolio_value) * 100 if self.initial_portfolio_value != 0 else 0
            total_pnl_percent = (total_pnl / self.initial_portfolio_value) * 100 if self.initial_portfolio_value != 0 else 0
            
            # Calculate win rate
            sell_trades = [t for t in self.trades if t['side'] == 'sell']
            profitable_trades = sum(1 for t in sell_trades if t.get('realized_pnl', 0) > 0)
            win_rate = (profitable_trades / len(sell_trades) * 100) if sell_trades else 0
            
            return {
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'realized_pnl': realized_pnl,
                'realized_pnl_percent': realized_pnl_percent,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_percent': unrealized_pnl_percent,
                'total_trades': len(self.trades),
                'win_rate': win_rate
            }
                
        except Exception as e:
            logger.error(f"Error calculating PnL: {str(e)}")
            return {
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'realized_pnl': 0,
                'realized_pnl_percent': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_percent': 0,
                'total_trades': len(self.trades),
                'win_rate': 0
            }

    def place_order(self, market, side, price, quantity):
        base_asset = market.replace('USDT', '')
        
        order_id = f"order_{int(time.time() * 1000)}_{len(self.orders)}"
        order = {
            'id': order_id,
            'market': market,
            'side': side,
            'price': float(price),
            'quantity': float(quantity),
            'status': 'OPEN',
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check if we have enough balance
            if side == 'buy':
                cost = float(price) * float(quantity)
                logger.info(f"Buy order cost: {cost}, Current USDT balance: {self.balances['USDT']}")
                if self.balances['USDT'] < cost:
                    logger.error(f"Insufficient USDT balance. Required: {cost}, Available: {self.balances['USDT']}")
                    return {'error': 'Insufficient USDT balance'}
                self.balances['USDT'] -= cost
                self.balances[base_asset] += float(quantity)
            else:  # sell
                logger.info(f"Sell order quantity: {quantity}, Current {base_asset} balance: {self.balances[base_asset]}")
                if self.balances[base_asset] < float(quantity):
                    logger.error(f"Insufficient {base_asset} balance. Required: {quantity}, Available: {self.balances[base_asset]}")
                    return {'error': f'Insufficient {base_asset} balance'}
                self.balances['USDT'] += float(price) * float(quantity)
                self.balances[base_asset] -= float(quantity)

            # Record the trade
            trade = {
                'order_id': order_id,
                'market': market,
                'side': side,
                'price': float(price),
                'quantity': float(quantity),
                'timestamp': datetime.now().isoformat(),
                'value': float(price) * float(quantity)
            }

            self.orders.append(order)
            self.trades.append(trade)
            self._save_state()
            logger.info(f"Order placed successfully: {order_id}")
            return {'id': order_id, 'status': 'SUCCESS'}

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {'error': str(e)}
    def reset_all(self):
        """Reset everything: balance, orders, and trades"""
        self.reset_balance()
        self._save_state()
        return {
            'balances': self.balances,
            'orders': self.orders,
            'trades': self.trades
        }
   
        try:
            current_price = market_data.get_market_price('OMUSDT')
            if not current_price:
                logger.error("Could not fetch current market price")
                return {
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'realized_pnl': 0,
                    'realized_pnl_percent': 0,
                    'unrealized_pnl': 0,
                    'unrealized_pnl_percent': 0,
                    'total_trades': len(self.trades),
                    'win_rate': 0
                }
                
            # Calculate current portfolio value
            current_portfolio_value = (
                self.balances['USDT'] +
                self.balances['OM'] * current_price
            )
            
            # Calculate total PnL
            total_pnl = current_portfolio_value - self.initial_portfolio_value
            total_pnl_percent = (total_pnl / self.initial_portfolio_value) * 100 if self.initial_portfolio_value != 0 else 0
            
            # Initialize realized PnL variables
            realized_pnl = 0
            entry_prices = {}
            
            # Calculate realized PnL from completed trades
            for trade in self.trades:
                if trade['side'] == 'buy':
                    # Store entry price for the quantity bought
                    if 'OM' not in entry_prices:
                        entry_prices['OM'] = []
                    entry_prices['OM'].append({
                        'price': trade['price'],
                        'quantity': trade['quantity']
                    })
                elif trade['side'] == 'sell' and entry_prices.get('OM'):
                    # FIFO calculation for realized PnL
                    sell_quantity = trade['quantity']
                    sell_price = trade['price']
                    
                    while sell_quantity > 0 and entry_prices['OM']:
                        entry = entry_prices['OM'][0]
                        used_quantity = min(sell_quantity, entry['quantity'])
                        
                        # Calculate PnL for this portion
                        realized_pnl += used_quantity * (sell_price - entry['price'])
                        
                        # Update remaining quantities
                        sell_quantity -= used_quantity
                        entry['quantity'] -= used_quantity
                        
                        # Remove entry if fully used
                        if entry['quantity'] <= 0:
                            entry_prices['OM'].pop(0)
            
            # Calculate unrealized PnL
            average_entry_price = self._calculate_average_entry_price()
            unrealized_pnl = self.balances['OM'] * (current_price - average_entry_price)
            
            # Calculate percentages
            realized_pnl_percent = (realized_pnl / self.initial_portfolio_value) * 100 if self.initial_portfolio_value != 0 else 0
            unrealized_pnl_percent = (unrealized_pnl / self.initial_portfolio_value) * 100 if self.initial_portfolio_value != 0 else 0
            
            # Calculate win rate
            sell_trades = [t for t in self.trades if t['side'] == 'sell']
            profitable_trades = sum(1 for t in sell_trades if t['price'] > t.get('entry_price', 0))
            win_rate = (profitable_trades / len(sell_trades) * 100) if sell_trades else 0
            
            return {
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'realized_pnl': realized_pnl,
                'realized_pnl_percent': realized_pnl_percent,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_percent': unrealized_pnl_percent,
                'total_trades': len(self.trades),
                'win_rate': win_rate
            }
                
        except Exception as e:
            logger.error(f"Error calculating PnL: {str(e)}")
            return {
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'realized_pnl': 0,
                'realized_pnl_percent': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_percent': 0,
                'total_trades': len(self.trades),
                'win_rate': 0
            }
                
    def _calculate_average_entry_price(self):
        """Calculate average entry price for current OM position"""
        buy_trades = [t for t in self.trades if t['side'] == 'buy']
        if not buy_trades:
            return 0
            
        total_quantity = sum(t['quantity'] for t in buy_trades)
        total_value = sum(t['quantity'] * t['price'] for t in buy_trades)
        
        return total_value / total_quantity if total_quantity > 0 else 0
        
    def place_order(self, market, side, price, quantity):
        base_asset = market.replace('USDT', '')
        
        order_id = f"order_{int(time.time() * 1000)}_{len(self.orders)}"
        order = {
            'id': order_id,
            'market': market,
            'side': side,
            'price': float(price),
            'quantity': float(quantity),
            'status': 'OPEN',
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check if we have enough balance
            if side == 'buy':
                cost = float(price) * float(quantity)
                logger.info(f"Buy order cost: {cost}, Current USDT balance: {self.balances['USDT']}")
                if self.balances['USDT'] < cost:
                    logger.error(f"Insufficient USDT balance. Required: {cost}, Available: {self.balances['USDT']}")
                    return {'error': 'Insufficient USDT balance'}
                self.balances['USDT'] -= cost
                self.balances[base_asset] += float(quantity)
            else:  # sell
                logger.info(f"Sell order quantity: {quantity}, Current {base_asset} balance: {self.balances[base_asset]}")
                if self.balances[base_asset] < float(quantity):
                    logger.error(f"Insufficient {base_asset} balance. Required: {quantity}, Available: {self.balances[base_asset]}")
                    return {'error': f'Insufficient {base_asset} balance'}
                self.balances['USDT'] += float(price) * float(quantity)
                self.balances[base_asset] -= float(quantity)

            # Record the trade
            trade = {
                'order_id': order_id,
                'market': market,
                'side': side,
                'price': float(price),
                'quantity': float(quantity),
                'timestamp': datetime.now().isoformat(),
                'value': float(price) * float(quantity)
            }

            self.orders.append(order)
            self.trades.append(trade)
            self._save_state()
            logger.info(f"Order placed successfully: {order_id}")
            return {'id': order_id, 'status': 'SUCCESS'}

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {'error': str(e)}

class MarketData:
    def __init__(self):
        self.base_url = "https://api.coindcx.com"

    def get_market_price(self, market):
        try:
            response = requests.get(f"{self.base_url}/exchange/ticker")
            if response.status_code == 200:
                data = response.json()
                for ticker in data:
                    if ticker['market'] == market:
                        return float(ticker['last_price'])
        except Exception as e:
            logger.error(f"Error fetching market price: {str(e)}")
        return None

class GridCalculator:
    def __init__(self, total_usdt=20000):
        self.total_usdt = total_usdt

    def calculate_grid_parameters(self, current_price):
        try:
            grid_levels = 6
            price_margin = current_price * 0.003
            upper_price = current_price + price_margin
            lower_price = current_price - price_margin
            grid_spacing = (upper_price - lower_price) / (grid_levels - 1)
            
            usable_balance = self.total_usdt * 0.8
            max_quantity_per_grid = usable_balance / (grid_levels * current_price)
            
            quantity_per_grid = round(max_quantity_per_grid, 6)
            
            grid_prices = [round(lower_price + (i * grid_spacing), 2) for i in range(grid_levels)]
            
            return {
                'upper_price': round(upper_price, 2),
                'lower_price': round(lower_price, 2),
                'grid_levels': grid_levels,
                'quantity_per_grid': quantity_per_grid,
                'estimated_total_cost': round(quantity_per_grid * current_price * grid_levels, 2),
                'grid_spacing': round(grid_spacing, 2),
                'current_price': round(current_price, 2),
                'grid_prices': grid_prices
            }
        except Exception as e:
            logger.error(f"Error calculating grid parameters: {str(e)}")
            return None

virtual_account = VirtualAccount()
market_data = MarketData()
grid_calculator = GridCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/grid/calculate', methods=['GET'])
def calculate_grid():
    try:
        market = request.args.get('market', 'OMUSDT')
        current_price = market_data.get_market_price(market)
        
        if not current_price:
            return jsonify({'status': 'error', 'message': 'Could not fetch current price'})
        
        params = grid_calculator.calculate_grid_parameters(current_price)
        
        if not params:
            return jsonify({'status': 'error', 'message': 'Could not calculate grid parameters'})
            
        return jsonify({
            'status': 'success',
            'current_price': current_price,
            'parameters': params
        })
        
    except Exception as e:
        logger.error(f"Error in calculate_grid: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/grid/start', methods=['POST'])
def start_grid():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'})

        logger.info(f"Received grid trading request: {data}")

        # Validate required fields
        required_fields = ['upper_price', 'lower_price', 'grid_levels', 'quantity_per_grid']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'})

        market = data.get('market', 'OMUSDT')
        upper_price = float(data['upper_price'])
        lower_price = float(data['lower_price'])
        grid_levels = int(data['grid_levels'])
        quantity_per_grid = float(data['quantity_per_grid'])

        # Get current market price
        current_price = market_data.get_market_price(market)
        if not current_price:
            return jsonify({'status': 'error', 'message': 'Could not fetch market price'})

        logger.info(f"Current market price: {current_price}")

        # Place initial market order
        logger.info("Placing initial market order")
        initial_order = virtual_account.place_order(
            market=market,
            side="buy",
            price=current_price,
            quantity=quantity_per_grid
        )

        if 'error' in initial_order:
            return jsonify({'status': 'error', 'message': initial_order['error']})

        # Place grid orders
        orders = [initial_order]
        price_interval = (upper_price - lower_price) / (grid_levels - 1)
        
        for i in range(grid_levels):
            grid_price = lower_price + (i * price_interval)
            
            # Skip prices too close to current price
            if abs(grid_price - current_price) < price_interval * 0.5:
                continue

            order = virtual_account.place_order(
                market=market,
                side="sell" if grid_price > current_price else "buy",
                price=grid_price,
                quantity=quantity_per_grid
            )
            
            if 'error' in order:
                return jsonify({'status': 'error', 'message': order['error']})
            
            orders.append(order)

        return jsonify({
            'status': 'success',
            'message': f'Successfully placed {len(orders)} orders',
            'orders': orders
        })

    except Exception as e:
        logger.error(f"Error in start_grid: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/virtual/balance')
@require_auth
def get_virtual_balance():
    return jsonify(virtual_account.balances)

@app.route('/api/virtual/trades')
def get_virtual_trades():
    return jsonify(virtual_account.trades)

# @app.route('/api/virtual/reset', methods=['POST'])
# def reset_virtual_account():
#     virtual_account.reset_balance()
#     virtual_account._save_state()
#     return jsonify({'status': 'success', 'message': 'Account reset successful'})

@app.route('/api/market/price/<market>')
def get_market_price(market):
    price = market_data.get_market_price(market)
    return jsonify({'price': price})

@app.route('/api/virtual/reset', methods=['POST'])
def reset_virtual_account():
    result = virtual_account.reset_all()
    return jsonify({
        'status': 'success',
        'message': 'Account reset successful',
        'data': result
    })
@app.route('/api/virtual/pnl')
def get_pnl():
    pnl_data = virtual_account.calculate_pnl()
    if pnl_data:
        return jsonify(pnl_data)
    return jsonify({'error': 'Could not calculate PnL'})

@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
            
        # Send password reset email
        response = supabase.auth.reset_password_email(email)
        
        return jsonify({
            'status': 'success',
            'message': 'Password reset instructions sent to your email'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'New password required'}), 400
            
        # Get access token from the request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Reset token required'}), 401
            
        token = auth_header.split(' ')[1]
        
        # Update the user's password
        response = supabase.auth.update_user(
            token,
            {"password": new_password}
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Password successfully updated'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 401

if __name__ == '__main__':
    # Register the auth blueprint
    app.register_blueprint(auth_bp)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)