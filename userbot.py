import telebot
import validators
from telebot import types
import json
import os
import time
import requests
from datetime import datetime

TOKEN = '8009582164:AAGTH7C9LpH1uhDmiGZMGtXvnVXzTZrrD1k'
bot = telebot.TeleBot(TOKEN)
user_states = {}

# File Paths
USERS_FILE = 'users.json'
SERVICES_FILE = 'services.json'
REQUESTS_FILE = 'fund_requests.json'
ORDERS_FILE = 'orders.json'
API_KEY = '6e1c6b406b873c2cdf3074c34c0a622148c0d76c'
API_URL = 'https://fastsmmstore.com/api/v2'

# Admin ID for notifications
ADMIN_ID = 7187468717

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

# Initialize data files with proper structure
def initialize_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(SERVICES_FILE):
        services_data = {
            "1": {
                "name": "TikTok Likes",
                "price_per_1000": 60.00,
                "category": "TikTok",
                "api_id": 9374,
                "min": 100,
                "max": 100000,
                "description": "High quality TikTok likes from real accounts",
                "default_discount": 10,
                "special_discount": 20
            },
            "2": {
                "name": "Instagram Followers",
                "price_per_1000": 100.00,
                "category": "Instagram",
                "api_id": 456,
                "min": 50,
                "max": 5000,
                "description": "Premium Instagram followers with gradual delivery",
                "default_discount": 5,
                "special_discount": 15
            }
        }
        with open(SERVICES_FILE, 'w') as f:
            json.dump(services_data, f, indent=4)
    
    if not os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'w') as f:
            json.dump([], f)
    
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump([], f)

# Load JSON data with error handling
def load_json(file):
    try:
        if not os.path.exists(file):
            initialize_files()
        
        with open(file, 'r') as f:
            data = json.load(f)
            # Validate data structure
            if file == USERS_FILE and not isinstance(data, dict):
                return {}
            elif file in [ORDERS_FILE, REQUESTS_FILE] and not isinstance(data, list):
                return []
            elif file == SERVICES_FILE and not isinstance(data, dict):
                initialize_files()
                return load_json(file)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted, recreate it
        if file in [USERS_FILE, SERVICES_FILE, REQUESTS_FILE, ORDERS_FILE]:
            initialize_files()
            return load_json(file)
        return {}

def save_json(file, data):
    try:
        with open(file, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {file}: {e}")

def make_api_request(data):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.post(API_URL, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request Failed: {e}")
        return {"error": str(e)}
    except ValueError:
        return {"error": "Invalid JSON response"}

def format_timestamp(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "N/A"

# Calculate price with custom discounts
def calculate_price(service_id, user_id):
    try:
        services = load_json(SERVICES_FILE)
        users = load_json(USERS_FILE)
        
        if service_id not in services:
            return None
        
        service = services[service_id]
        base_price = service['price_per_1000']
        
        # Check if user has custom discounts
        if user_id in users and 'custom_discounts' in users[user_id] and service_id in users[user_id]['custom_discounts']:
            discount = users[user_id]['custom_discounts'][service_id]
        # Check if user is special member
        elif user_id in users and users[user_id].get('is_special', False):
            discount = service['special_discount']
        # Apply default discount
        else:
            discount = service['default_discount']
        
        # Calculate final price
        final_price = base_price * (1 - discount/100)
        return round(final_price, 2)
    except Exception as e:
        print(f"Error calculating price: {e}")
        return None

# Main menu keyboard
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.row("🛍️ Services", "💳 Add Funds")
    kb.row("📦 My Orders", "💰 Balance")
    kb.row("🔄 Refill Order", "❌ Cancel Order", "📊 Refer & Earn")
    kb.row("😈 Amazing Hacks", "🆘 Support")
    return kb

# Back button keyboard
def back_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Back")
    return kb

# Start command handler
@bot.message_handler(commands=['start'])
def start(msg):
    try:
        users = load_json(USERS_FILE)
        uid = str(msg.from_user.id)
        
        # Initialize new user if not exists
        if uid not in users:
            users[uid] = {
                'username': msg.from_user.username,
                'balance': 0,
                'orders': [],
                'total_spent': 0,
                'join_date': time.time(),
                'referrals': 0,
                'bonus_level': 0,
                'referral_earnings': 0,
                'referred_by': None,
                'is_special': False,
                'custom_discounts': {}
            }
        
        # Handle referral link
        if len(msg.text.split()) > 1 and msg.text.split()[1].startswith('ref_'):
            referrer_id = msg.text.split()[1].replace('ref_', '')
            
            # Only process if user doesn't already have a referrer
            if referrer_id in users and referrer_id != uid and users[uid].get('referred_by') is None:
                users[uid]['referred_by'] = referrer_id
                users[referrer_id]['referrals'] = users[referrer_id].get('referrals', 0) + 1
                
                # Calculate bonus level based on referrals
                referrals = users[referrer_id]['referrals']
                if referrals >= 50:
                    users[referrer_id]['bonus_level'] = 10
                elif referrals >= 20:
                    users[referrer_id]['bonus_level'] = 7
                elif referrals >= 1:
                    users[referrer_id]['bonus_level'] = 5
                
                # Notify referrer
                try:
                    bot.send_message(
                        referrer_id,
                        f"🎉 New referral!\n"
                        f"User: @{msg.from_user.username}\n"
                        f"Total referrals: {users[referrer_id]['referrals']}\n"
                        f"Your bonus level: {users[referrer_id]['bonus_level']}%"
                    )
                except Exception as e:
                    print(f"Failed to notify referrer: {e}")
        
        save_json(USERS_FILE, users)
            
        text = f"""🎉 Welcome {msg.from_user.first_name}!
━━━━━━━━━━━━━━━━
💰 Balance: Rs {users[uid]['balance']:.2f}
🛍️ Order Services
💳 Add Funds Anytime
━━━━━━━━━━━━━━━━"""
        bot.send_message(uid, text, reply_markup=main_menu())
    except Exception as e:
        print(f"Error in start handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Services menu - Updated to show all categories
@bot.message_handler(func=lambda m: m.text == "📊 Refer & Earn")
def refer_and_earn(msg):
    try:
        users = load_json(USERS_FILE)
        uid = str(msg.from_user.id)
        
        # Initialize user if not exists
        if uid not in users:
            users[uid] = {
                'username': msg.from_user.username,
                'balance': 0,
                'orders': [],
                'total_spent': 0,
                'join_date': time.time(),
                'referrals': 0,
                'bonus_level': 0,
                'referral_earnings': 0,
                'referred_by': None,
                'is_special': False,
                'custom_discounts': {}
            }
            save_json(USERS_FILE, users)

        # Generate proper referral link
        bot_username = bot.get_me().username
        referral_link = f"https://t.me/{bot_username}?start=ref_{uid}"
        
        # Prepare dashboard message
        text = f"""📊 *Referral Dashboard - Sirf Deposit Par Bonus*
━━━━━━━━━━━━━━━━
👥 Total Referrals: {users[uid]['referrals']}
💰 Referral Earnings: Rs {users[uid].get('referral_earnings', 0):.2f}
🏆 Bonus Level: {users[uid]['bonus_level']}%
━━━━━━━━━━━━━━━━
🔗 *Your Referral Link:*
`{referral_link}`

📢 *How it works:*
1. Link ko apne friends ke sath share kare

2. Agar wo aap ke link se join hote hai to 👇 

3. Jab wo fund add karwaye ge aap ko aap ke Bonus Level par Commission mile ga Lifetime tak

4. Is Waqt Aap ka bonus Level hai {users[uid]['bonus_level']}%

5. Increase Kare bonus level with share link
━━━━━━━━━━━━━━━━
💡 *Bonus Levels:*
• 1+ Referrals = 5% bonus
• 20+ Referrals = 7% bonus
• 50+ Referrals = 10% bonus"""

        # Create share button
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton(
            text="📤 Share Link", 
            url=f"https://t.me/share/url?url={referral_link}&text=Join%20using%20my%20referral%20link!"
        )
        markup.add(share_button)

        bot.send_message(
            msg.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )
        
    except Exception as e:
        print(f"Error in refer_and_earn: {e}")
        bot.send_message(
            msg.chat.id,
            "❌ Could not load referral information. Please try again later.",
            reply_markup=main_menu()
        )
@bot.message_handler(func=lambda m: m.text == "🛍️ Services")
def services(msg):
    try:
        services_data = load_json(SERVICES_FILE)
        categories = set()
        
        for service in services_data.values():
            categories.add(service['category'])
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for category in sorted(categories):
            kb.add(types.KeyboardButton(category))
        kb.row("🔙 Back", "Main Menu")
        
        bot.send_message(msg.chat.id, "📦 Please select a category:", reply_markup=kb)
    except Exception as e:
        print(f"Error in services menu: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Show services in category - Updated with better display
@bot.message_handler(func=lambda m: any(m.text == service['category'] for service in load_json(SERVICES_FILE).values()))
def show_category(msg):
    try:
        services_data = load_json(SERVICES_FILE)
        uid = str(msg.from_user.id)
        users = load_json(USERS_FILE)
        is_special = users.get(uid, {}).get('is_special', False)
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        for sid, service in services_data.items():
            if service['category'] == msg.text:
                price = calculate_price(sid, uid)
                if price is None:
                    continue
                
                # Check if user has custom discount for this service
                custom_discount = users.get(uid, {}).get('custom_discounts', {}).get(sid)
                
                # Prepare service display text
                service_text = f"{service['name']} (Rs {price:.2f}/1k)"
                
                if custom_discount is not None:
                    service_text += " 🔥"  # Indicate custom discount
                elif is_special:
                    service_text += " ★"   # Indicate special member
                
                kb.add(types.KeyboardButton(service_text))
        
        kb.row("🔙 Back", "Main Menu")
        user_states[msg.chat.id] = {'category': msg.text}
        
        # Add discount information note
        note = ""
        if is_special:
            note += "★ = Special Member Discount\n"
        if any(sid in users.get(uid, {}).get('custom_discounts', {}) for sid in services_data):
            note += "🔥 = Your Custom Discount"
        
        if note:
            bot.send_message(msg.chat.id, note)
        
        bot.send_message(msg.chat.id, f"📦 Available {msg.text} Services:", reply_markup=kb)
    except Exception as e:
        print(f"Error showing category: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle service selection - Updated pattern matching
@bot.message_handler(func=lambda m: any(
    m.text.startswith(service['name']) and '(Rs ' in m.text and '/1k' in m.text 
    for service in load_json(SERVICES_FILE).values()
))
def handle_service_selection(msg):
    try:
        services_data = load_json(SERVICES_FILE)
        uid = str(msg.from_user.id)
        users = load_json(USERS_FILE)
        
        # Extract the base service name (remove price and discount indicators)
        service_name = msg.text.split(' (Rs ')[0].strip()
        service_name = service_name.replace(' ★', '').replace(' 🔥', '')
        
        # Find the matching service
        for sid, service in services_data.items():
            if service['name'] == service_name:
                final_price = calculate_price(sid, uid)
                if final_price is None:
                    return bot.send_message(msg.chat.id, "❌ Error calculating price. Please try again.", reply_markup=main_menu())
                
                original_price = service['price_per_1000']
                
                user_states[msg.chat.id] = {
                    'service_id': sid,
                    'service_name': service['name'],
                    'price_per_1000': final_price,
                    'original_price': original_price,
                    'is_special': users.get(uid, {}).get('is_special', False),
                    'has_custom_discount': sid in users.get(uid, {}).get('custom_discounts', {}),
                    'api_id': service['api_id'],
                    'min': service['min'],
                    'max': service['max'],
                    'description': service.get('description', ''),
                    'step': 'link'
                }
                break
        else:
            return bot.send_message(msg.chat.id, "❌ Service not found", reply_markup=main_menu())
        
        bot.send_message(msg.chat.id, "🔗 Please enter your link:", reply_markup=back_keyboard())
    except Exception as e:
        print(f"Error in service selection: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())
# Handle link input
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'link')
def handle_link_input(msg):
    try:
        if msg.text == "🔙 Back":
            category = user_states[msg.chat.id].get('category', 'TikTok')
            del user_states[msg.chat.id]
            return show_category(types.Message(message_id=msg.message_id, chat=msg.chat, from_user=msg.from_user, text=category))
        
        if not validators.url(msg.text):
            return bot.send_message(msg.chat.id, "❌ Invalid URL! Please enter a valid link:", reply_markup=back_keyboard())
        
        user_states[msg.chat.id]['link'] = msg.text
        user_states[msg.chat.id]['step'] = 'quantity'
        
        bot.send_message(msg.chat.id, 
                        f"🔢 Please enter quantity (Min: {user_states[msg.chat.id]['min']}, Max: {user_states[msg.chat.id]['max']}):",
                        reply_markup=back_keyboard())
    except Exception as e:
        print(f"Error in link input: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle quantity input
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'quantity')
def handle_quantity_input(msg):
    try:
        if msg.text == "🔙 Back":
            user_states[msg.chat.id]['step'] = 'link'
            return bot.send_message(msg.chat.id, "🔗 Please enter your link:", reply_markup=back_keyboard())
        
        try:
            qty = int(msg.text)
            min_qty = user_states[msg.chat.id]['min']
            max_qty = user_states[msg.chat.id]['max']
            
            if qty < min_qty or qty > max_qty:
                return bot.send_message(msg.chat.id, f"❌ Quantity must be between {min_qty} and {max_qty}!")
            
            user_states[msg.chat.id]['qty'] = qty
            price = (user_states[msg.chat.id]['price_per_1000'] * qty) / 1000
            user_states[msg.chat.id]['price'] = round(price, 2)
            user_states[msg.chat.id]['step'] = 'confirm'
            
            # Prepare confirmation message
            text = f"""📦 Order Summary
━━━━━━━━━━━━━━━━
🛍️ Service: {user_states[msg.chat.id]['service_name']}
🔗 Link: {user_states[msg.chat.id]['link']}
🔢 Quantity: {qty}
💰 Price: Rs {user_states[msg.chat.id]['price']:.2f}"""
            
            # Show discount information if applicable
            if user_states[msg.chat.id]['is_special'] or user_states[msg.chat.id]['has_custom_discount']:
                original_cost = (user_states[msg.chat.id]['original_price'] * qty) / 1000
                saved = original_cost - user_states[msg.chat.id]['price']
                text += f"\n🎁 You saved: Rs {saved:.2f}"
                
                if user_states[msg.chat.id]['has_custom_discount']:
                    text += " (Custom Discount)"
                else:
                    text += " (Special Member Discount)"
            
            text += "\n━━━━━━━━━━━━━━━━\n✅ Confirm Order?"
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row("✅ Confirm", "❌ Cancel")
            kb.row("🔙 Back", "Main Menu")
            bot.send_message(msg.chat.id, text, reply_markup=kb)
            
        except ValueError:
            bot.send_message(msg.chat.id, "❌ Please enter a valid number!", reply_markup=back_keyboard())
    except Exception as e:
        print(f"Error in quantity input: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Confirm order
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'confirm')
def confirm_order(msg):
    try:
        if msg.text == "🔙 Back":
            user_states[msg.chat.id]['step'] = 'quantity'
            return bot.send_message(msg.chat.id, 
                                 f"🔢 Please enter quantity (Min: {user_states[msg.chat.id]['min']}, Max: {user_states[msg.chat.id]['max']}):",
                                 reply_markup=back_keyboard())
        
        if msg.text == "❌ Cancel":
            del user_states[msg.chat.id]
            return bot.send_message(msg.chat.id, "❌ Order cancelled", reply_markup=main_menu())
        
        if msg.text != "✅ Confirm":
            return
        
        users = load_json(USERS_FILE)
        orders = load_json(ORDERS_FILE)
        uid = str(msg.from_user.id)
        
        if uid not in users:
            return bot.send_message(msg.chat.id, "❌ Please use /start first.", reply_markup=main_menu())
        
        order_price = float(user_states[msg.chat.id]['price'])
        user_balance = float(users[uid]['balance'])
        
        if user_balance < order_price:
            return bot.send_message(msg.chat.id, "❌ Insufficient balance! Please add funds.", reply_markup=main_menu())
        
        # Make API request to create order
        api_data = {
            'key': API_KEY,
            'action': 'add',
            'service': user_states[msg.chat.id]['api_id'],
            'link': user_states[msg.chat.id]['link'],
            'quantity': user_states[msg.chat.id]['qty']
        }
        
        api_response = make_api_request(api_data)
        if 'error' in api_response:
            raise Exception(api_response['error'])
        if 'order' not in api_response:
            raise Exception("API did not return order ID")
        
        # Deduct balance and create order
        users[uid]['balance'] -= order_price
        users[uid]['total_spent'] += order_price
        
        order = {
            'api_order_id': str(api_response['order']),
            'user_id': uid,
            'username': msg.from_user.username,
            'service': user_states[msg.chat.id]['service_name'],
            'description': user_states[msg.chat.id]['description'],
            'link': user_states[msg.chat.id]['link'],
            'qty': user_states[msg.chat.id]['qty'],
            'price': order_price,
            'status': 'Processing',
            'timestamp': time.time(),
            'is_special': user_states[msg.chat.id]['is_special'],
            'has_custom_discount': user_states[msg.chat.id]['has_custom_discount'],
            'original_price': user_states[msg.chat.id]['original_price']
        }
        
        users[uid]['orders'].append(order)
        orders.append(order)
        
        # Process referral bonus if applicable
        if users[uid].get('referred_by'):
            referrer_id = users[uid]['referred_by']
            if referrer_id in users:
                bonus_percent = users[referrer_id].get('bonus_level', 0)
                if bonus_percent > 0:
                    bonus_amount = (order_price * bonus_percent) / 100
                    users[referrer_id]['balance'] = float(users[referrer_id].get('balance', 0)) + bonus_amount
                    users[referrer_id]['referral_earnings'] = float(users[referrer_id].get('referral_earnings', 0)) + bonus_amount
                    
                    try:
                        bot.send_message(
                            referrer_id,
                            f"🎉 Referral Purchase Bonus!\n"
                            f"User @{users[uid]['username']} made a purchase of Rs {order_price:.2f}\n"
                            f"You earned {bonus_percent}% = Rs {bonus_amount:.2f}\n"
                            f"New balance: Rs {users[referrer_id]['balance']:.2f}"
                        )
                    except Exception as e:
                        print(f"Failed to notify referrer: {e}")
        
        save_json(USERS_FILE, users)
        save_json(ORDERS_FILE, orders)
        
        # Prepare confirmation message
        msg_text = f"""✅ Order Successful!
━━━━━━━━━━━━━━━━
📦 Service: {order['service']}
📝 Description: {order['description']}
🔗 Link: {order['link']}
🔢 Quantity: {order['qty']}"""

        if order['is_special'] or order['has_custom_discount']:
            original_cost = order['original_price'] * order['qty'] / 1000
            saved = original_cost - order_price
            msg_text += f"\n🎁 You saved: Rs {saved:.2f}"

            if order['has_custom_discount']:
                msg_text += " (Custom Discount)"
            else:
                msg_text += " (Special Member Discount)"

        msg_text += f"""
💵 Paid: Rs {order_price:.2f}
🆔 Order ID: {order['api_order_id']}
━━━━━━━━━━━━━━━━"""

        bot.send_message(msg.chat.id, msg_text, reply_markup=main_menu())

        # Notify admin
        try:
            text = f"📦 New Order!\n\n👤 User: @{msg.from_user.username}\n🆔 Order ID: {order['api_order_id']}\n📦 Service: {order['service']}\n🔢 Quantity: {order['qty']}\n💵 Amount: Rs {order_price:.2f}"
            if order['is_special'] or order['has_custom_discount']:
                admin_text += f"\n🎁 Discount Applied: {'Custom' if order['has_custom_discount'] else 'Special Member'}"
            bot.send_message(ADMIN_ID, admin_text)
        except Exception as e:
            print(f"Failed to notify admin: {e}")
        
    except Exception as e:
        error_msg = f"❌ Order Failed!\nError: {str(e)}"
        bot.send_message(msg.chat.id, error_msg, reply_markup=main_menu())
        print(f"Order Error: {str(e)}")
    
    del user_states[msg.chat.id]

# Amazing Hacks menu
@bot.message_handler(func=lambda m: m.text == "😈 Amazing Hacks")
def amazing_hacks(msg):
    try:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("📱 SIM Database")
        kb.row("🔙 Back", "Main Menu")
        bot.send_message(msg.chat.id, "🔮 Select a hack:", reply_markup=kb)
    except Exception as e:
        print(f"Error in amazing hacks menu: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# SIM Database handler
@bot.message_handler(func=lambda m: m.text == "📱 SIM Database")
def sim_database(msg):
    try:
        users = load_json(USERS_FILE)
        user_id = str(msg.from_user.id)
        
        if user_id in users and 'orders' in users[user_id] and len(users[user_id]['orders']) > 0:
            bot.send_message(msg.chat.id, 
                           "🔍 CNIC ya Mobile Number bhejein:\n\n📱 Mobile: 03XXXXXXXXX (11 digits)\n🪪 CNIC: 13 digits (without dashes)", 
                           parse_mode="Markdown", 
                           reply_markup=back_keyboard())
            user_states[msg.chat.id] = {'step': 'sim_db_input'}
        else:
            bot.send_message(msg.chat.id, 
                           "❌ *Access Denied!*\n\nℹ️ **Shart:** Kam se kam 1 order karna zaroori hai\n\n🛍️ Pehle koi service order karein\n💰 Phir aap Sim Database or Amazing Hacks use kar sakte hain", 
                           parse_mode="Markdown", 
                           reply_markup=main_menu())
    except Exception as e:
        print(f"Error in SIM database handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle SIM database input
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'sim_db_input')
def handle_sim_db_input(msg):
    try:
        if msg.text == "🔙 Back":
            del user_states[msg.chat.id]
            return amazing_hacks(msg)
        
        user_input = msg.text.strip()
        del user_states[msg.chat.id]
        
        if user_input.isdigit() and len(user_input) == 13: 
            check_cnic(msg, user_input)
        elif user_input.startswith('03') and len(user_input) == 11 and user_input.isdigit(): 
            check_number(msg, user_input)
        else:
            bot.send_message(msg.chat.id, 
                           "❌ Invalid input. Please send a valid *CNIC* (13 digits) or *mobile number* (starting with 03, 11 digits).", 
                           parse_mode="Markdown", 
                           reply_markup=main_menu())
    except Exception as e:
        print(f"Error in SIM database input: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

def check_cnic(msg, cnic):
    try:
        url = f"https://fam-official.serv00.net/sim/api.php?num={cnic}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "success" and data.get("data"):
            sims = data["data"]
            reply = f"🪪 *CNIC:* `{cnic}`\n📱 *Total SIMs:* {len(sims)}\n\n"
            for idx, sim in enumerate(sims, start=1):
                reply += (f"🔢 *SIM {idx}:*\n👤 *Name:* `{sim['Name']}`\n📞 *Mobile:* `{sim['Mobile']}`\n📡 *Operator:* `{sim['Operator']}`\n🏠 *Address:* `{sim['Address']}`\n━━━━━━━━━━━━━━━\n")
            bot.send_message(msg.chat.id, reply, parse_mode="Markdown")
        else: 
            bot.send_message(msg.chat.id, "❌ No SIMs found for this CNIC.")
    except Exception as e: 
        bot.send_message(msg.chat.id, f"⚠️ Error checking CNIC: {e}")
    finally: 
        bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())

def check_number(msg, number):
    try:
        url = f"https://fam-official.serv00.net/sim/api.php?num={number}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "success" and data.get("data"):
            sim = data["data"][0]
            reply = (f"📞 *SIM Info for:* `{number}`\n👤 *Name:* `{sim['Name']}`\n🪪 *CNIC:* `{sim['CNIC']}`\n📡 *Operator:* `{sim['Operator']}`\n🏠 *Address:* `{sim['Address']}`")
            bot.send_message(msg.chat.id, reply, parse_mode="Markdown")
        else: 
            bot.send_message(msg.chat.id, "❌ No details found for this number.")
    except Exception as e: 
        bot.send_message(msg.chat.id, f"⚠️ Error checking number: {e}")
    finally: 
        bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())

# Add funds handler
@bot.message_handler(func=lambda m: m.text == "💳 Add Funds")
def add_funds(msg):
    try:
        user_states[msg.chat.id] = {'step': 'amount'}
        bot.send_message(msg.chat.id, 
                        "⚠️ *Pehle Payment Karain Phir Request Bejain!*\n\n💳 *Payment Details:*\n👤 *Name:* ASIF ALI\n🏦 *Account:* 03225815922\n📲 *Easypaisa / JazzCash (Dono Available)*\n\n❌ *Bina Payment Ke Fund Request Mat Bejein!*\n🚫 *Fake Request Par Aapka Account Ban Ho Sakta Hai!*", 
                        parse_mode="Markdown", 
                        reply_markup=back_keyboard())
        bot.send_message(msg.chat.id, 
                        "✅ *Payment Karne Ke Baad Neeche Amount Likhein (Kam Se Kam Rs 20):*", 
                        parse_mode="Markdown")
    except Exception as e:
        print(f"Error in add funds handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle amount input
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'amount')
def handle_amount(msg):
    try:
        if msg.text == "🔙 Back":
            del user_states[msg.chat.id]
            return bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())
        
        try:
            amount = float(msg.text)
        except ValueError:
            return bot.send_message(msg.chat.id, "❌ Ghalat amount! Sirf numbers likhein (e.g., 10.50).", reply_markup=back_keyboard())
        
        if amount < 20: 
            return bot.send_message(msg.chat.id, "❌ Kam se Kam Rs 20 Amount", reply_markup=back_keyboard())
        
        user_states[msg.chat.id]['amount'] = amount
        user_states[msg.chat.id]['step'] = 'method'
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("JazzCash", "EasyPaisa")
        kb.row("Bank Transfer", "Other")
        kb.row("🔙 Back", "Cancel")
        bot.send_message(msg.chat.id, "📟 Select payment method:", reply_markup=kb)
    except Exception as e:
        print(f"Error in amount input: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle payment method
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'method')
def handle_method(msg):
    try:
        if msg.text == "🔙 Back":
            user_states[msg.chat.id]['step'] = 'amount'
            return bot.send_message(msg.chat.id, 
                                 "✅ *Payment Karne Ke Baad Neeche Amount Likhein (Kam Se Kam Rs 20):*", 
                                 parse_mode="Markdown", 
                                 reply_markup=back_keyboard())
        
        if msg.text == "Cancel":
            del user_states[msg.chat.id]
            return bot.send_message(msg.chat.id, "❌ Request cancelled", reply_markup=main_menu())
        
        user_states[msg.chat.id]['method'] = msg.text
        user_states[msg.chat.id]['step'] = 'screenshot'
        bot.send_message(msg.chat.id, 
                        "📸 Payment ka screenshot send kar de:", 
                        reply_markup=back_keyboard())
    except Exception as e:
        print(f"Error in payment method handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle screenshot
@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'screenshot')
def handle_screenshot(msg):
    try:
        if msg.text == "🔙 Back":
            user_states[msg.chat.id]['step'] = 'method'
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row("JazzCash", "EasyPaisa")
            kb.row("Bank Transfer", "Other")
            kb.row("🔙 Back", "Cancel")
            return bot.send_message(msg.chat.id, "📟 Select payment method:", reply_markup=kb)
        
        user_states[msg.chat.id]['screenshot'] = msg.photo[-1].file_id
        user_states[msg.chat.id]['step'] = 'confirm_request'
        
        text = f"""📋 Fund Request Summary:
━━━━━━━━━━━━━━━━
💵 Amount: Rs {user_states[msg.chat.id]['amount']}
📟 Method: {user_states[msg.chat.id]['method']}
━━━━━━━━━━━━━━━━
✅ Confirm request?"""
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("✅ Confirm", "❌ Cancel")
        kb.row("🔙 Back", "Main Menu")
        bot.send_message(msg.chat.id, text, reply_markup=kb)
    except Exception as e:
        print(f"Error in screenshot handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Confirm fund request
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'confirm_request')
def confirm_fund_request(msg):
    try:
        if msg.text == "🔙 Back":
            user_states[msg.chat.id]['step'] = 'screenshot'
            return bot.send_message(msg.chat.id, 
                                 "📸 Payment ka screenshot send kar de:", 
                                 reply_markup=back_keyboard())
        
        if msg.text == "❌ Cancel":
            del user_states[msg.chat.id]
            return bot.send_message(msg.chat.id, "❌ Request cancelled", reply_markup=main_menu())
        
        if msg.text != "✅ Confirm":
            return
        
        request_id = f"{msg.from_user.id}_{int(time.time())}"
        request_data = {
            'request_id': request_id,
            'user_id': str(msg.from_user.id),
            'username': msg.from_user.username,
            'amount': user_states[msg.chat.id]['amount'],
            'method': user_states[msg.chat.id]['method'],
            'screenshot': user_states[msg.chat.id].get('screenshot', ''),
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        requests = load_json(REQUESTS_FILE)
        if not isinstance(requests, list): 
            requests = []
        requests.append(request_data)
        save_json(REQUESTS_FILE, requests)
        
        try:
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{request_id}"),
                types.InlineKeyboardButton("❌ Decline", callback_data=f"decline_{request_id}")
            )
            
            if 'screenshot' in user_states[msg.chat.id]:
                try: 
                    bot.send_photo(
                        ADMIN_ID, 
                        user_states[msg.chat.id]['screenshot'], 
                        caption=f"🔄 New Fund Request\n\n🆔 ID: {request_id}\n👤 User: @{msg.from_user.username}\n💵 Amount: Rs {request_data['amount']}\n📟 Method: {request_data['method']}", 
                        reply_markup=markup
                    )
                except: 
                    bot.send_message(
                        ADMIN_ID, 
                        f"🔄 New Fund Request\n\n🆔 ID: {request_id}\n👤 User: @{msg.from_user.username}\n💵 Amount: Rs {request_data['amount']}\n📟 Method: {request_data['method']}\n📸 Screenshot: [Available]", 
                        reply_markup=markup
                    )
            else: 
                bot.send_message(
                    ADMIN_ID, 
                    f"🔄 New Fund Request\n\n🆔 ID: {request_id}\n👤 User: @{msg.from_user.username}\n💵 Amount: Rs {request_data['amount']}\n📟 Method: {request_data['method']}", 
                    reply_markup=markup
                )
        except Exception as e: 
            print(f"Error notifying admin: {e}")
        
        bot.send_message(msg.chat.id, 
                       f"✅ Request submitted!\n\n🆔 ID: {request_id}\n⏳ Please wait kare admin check kare ga auto update ho jayega.", 
                       reply_markup=main_menu())
        del user_states[msg.chat.id]
    except Exception as e:
        print(f"Error in confirm fund request: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Handle admin response to fund requests
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'decline_')))
def handle_admin_response(call):
    try:
        action, request_id = call.data.split('_', 1)
        requests = load_json(REQUESTS_FILE)
        users = load_json(USERS_FILE)
        
        request = next((r for r in requests if r['request_id'] == request_id), None)
        if not request:
            return bot.answer_callback_query(call.id, "Request not found!")
        
        user_id = request['user_id']
        
        if action == 'approve':
            # Initialize user if not exists
            if user_id not in users:
                users[user_id] = {
                    'username': request['username'],
                    'balance': 0,
                    'orders': [],
                    'total_spent': 0,
                    'join_date': time.time(),
                    'referrals': 0,
                    'bonus_level': 0,
                    'referral_earnings': 0,
                    'referred_by': None,
                    'is_special': False,
                    'custom_discounts': {}
                }
            
            # Add funds to user
            deposit_amount = float(request['amount'])
            users[user_id]['balance'] += deposit_amount
            
            # Process referral bonus ONLY for fund additions (not orders)
            if users[user_id].get('referred_by'):
                referrer_id = users[user_id]['referred_by']
                if referrer_id in users:
                    # Calculate bonus percentage
                    referral_count = users[referrer_id].get('referrals', 0)
                    bonus_percent = 10 if referral_count >= 50 else 7 if referral_count >= 20 else 5
                    
                    # Calculate and add bonus
                    bonus_amount = round((deposit_amount * bonus_percent) / 100, 2)
                    users[referrer_id]['balance'] += bonus_amount
                    users[referrer_id]['referral_earnings'] += bonus_amount
                    
                    # Notify referrer in Roman Urdu
                    try:
                        bot.send_message(
                            referrer_id,
                            f"🎉 *Referral Bonus (Sirf Deposit Par)*\n\n"
                            f"🆔 Referred User: @{users[user_id]['username']}\n"
                            f"💵 Deposit Amount: Rs {deposit_amount:.2f}\n"
                            f"💰 Aapka Bonus: Rs {bonus_amount:.2f} ({bonus_percent}%)\n"
                            f"🏦 New Balance: Rs {users[referrer_id]['balance']:.2f}\n\n"
                            f"ℹ️ Note: Order par koi bonus nahi milta, sirf deposit par milta hai",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"Referrer notification error: {e}")

            # Update request status
            request['status'] = 'approved'
            save_json(USERS_FILE, users)
            save_json(REQUESTS_FILE, [r for r in requests if r['request_id'] != request_id])
            
            # Notify user in Roman Urdu
            bot.send_message(
                user_id,
                f"✅ *Deposit Approve Ho Gaya!*\n\n"
                f"💵 Amount: Rs {deposit_amount:.2f}\n"
                f"🏦 New Balance: Rs {users[user_id]['balance']:.2f}\n\n"
                f"Shukriya!",
                parse_mode="Markdown"
            )
            
            bot.answer_callback_query(call.id, f"Approved Rs {deposit_amount:.2f}")
            
        elif action == 'decline':
            request['status'] = 'declined'
            save_json(REQUESTS_FILE, [r for r in requests if r['request_id'] != request_id])
            
            bot.send_message(
                user_id,
                f"❌ *Deposit Decline Ho Gaya!*\n\n"
                f"🆔 Request ID: {request_id}\n"
                f"💵 Amount: Rs {float(request['amount']):.2f}\n\n"
                f"Agar ghalti se decline hua hai to support se contact karein",
                parse_mode="Markdown"
            )
            
            bot.answer_callback_query(call.id, "Request declined")
            
    except Exception as e:
        print(f"Error in admin response: {e}")
        bot.answer_callback_query(call.id, "Error processing request")


@bot.message_handler(func=lambda m: m.text == "📊 Refer & Earn")
def refer_and_earn(msg):
    try:
        users = load_json(USERS_FILE)
        uid = str(msg.from_user.id)
        
        if uid not in users:
            users[uid] = {
                'username': msg.from_user.username,
                'balance': 0,
                'orders': [],
                'total_spent': 0,
                'join_date': time.time(),
                'referrals': 0,
                'bonus_level': 0,
                'referral_earnings': 0,
                'referred_by': None,
                'is_special': False,
                'custom_discounts': {}
            }
            save_json(USERS_FILE, users)

        # Generate referral link
        referral_link = f"https://t.me/{bot.get_me().username}?start=ref_{uid}"
        
        # Prepare dashboard message in Roman Urdu
        text = f"""📊 *Referral System - Sirf Deposit Par Bonus*

━━━━━━━━━━━━━━━━
👥 Aapke Referrals: {users[uid]['referrals']}
💰 Total Bonus: Rs {users[uid].get('referral_earnings', 0):.2f}
🏆 Aapka Bonus Level: {users[uid]['bonus_level']}%
━━━━━━━━━━━━━━━━
🔗 *Aapka Referral Link:*
`{referral_link}`

📢 *Kaam Ka Tareeka:*
1. Apna referral link share karein
2. Log aapke link se join karein
3. Jab wo deposit karein, aapko bonus milega
4. Order par koi bonus nahi milta

💡 *Bonus Levels:*
• 1+ Referrals = 5% bonus
• 20+ Referrals = 7% bonus 
• 50+ Referrals = 10% bonus

⚠️ Note: Sirf deposit par bonus, order par nahi"""

        # Create share button
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton(
            text="📤 Share Link", 
            url=f"https://t.me/share/url?url={referral_link}&text=Join%20using%20my%20referral%20link!"
        )
        markup.add(share_button)

        bot.send_message(
            msg.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )
        
    except Exception as e:
        print(f"Error in refer_and_earn: {e}")
        bot.send_message(
            msg.chat.id,
            "❌ Referral system temporary unavailable. Please try again later.",
            reply_markup=main_menu()
        )

# Support handler
@bot.message_handler(func=lambda m: m.text == "🆘 Support")
def support(msg):
    try:
        text = """🆘 **Support Center:**
━━━━━━━━━━━━━━━━
✉️ Email: asifmufti922@gmail.com
📱 WhatsApp: https://wa.me/923225815922
📢 Telegram: @hafizhacker
⏰ 24/7 Support
━━━━━━━━━━━━━━━━"""
        bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        print(f"Error in support handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# My Orders handler
@bot.message_handler(func=lambda m: m.text == "📦 My Orders")
def show_orders(msg):
    try:
        users = load_json(USERS_FILE)
        uid = str(msg.from_user.id)
        
        if uid not in users or not users[uid].get('orders'):
            return bot.send_message(msg.chat.id, "📭 You don't have any orders yet!", reply_markup=main_menu())
        
        text = "📦 *Your Orders*\n━━━━━━━━━━━━━━━━\n"
        
        # Sort orders by timestamp (newest first)
        sorted_orders = sorted(users[uid]['orders'], key=lambda x: x.get('timestamp', 0), reverse=True)
        
        for order in sorted_orders:
            status_emoji = "✅" if order['status'] == 'Completed' else "🔄" if order['status'] == 'Processing' else "❌" if order['status'] == 'Cancelled' else "❓"
            
            text += f"""{status_emoji} *Order #{order['api_order_id']}*
📦 Service: {order['service']}
📝 Description: {order.get('description', 'N/A')}
🔗 Link: {order['link']}
🔢 Quantity: {order['qty']}
💵 Price: Rs {order['price']:.2f}
⏰ Order Time: {format_timestamp(order.get('timestamp'))}
🔄 Status: {order['status']}"""
            
            if order.get('status_data'):
                sd = order['status_data']
                text += f"\n📊 Start Count: {sd.get('start_count', 'N/A')}"
                text += f"\n📉 Remaining: {sd.get('remains', 'N/A')}"
                text += f"\n🌐 API Status: {sd.get('status', 'N/A')}"
            
            text += "\n━━━━━━━━━━━━━━━━\n"
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔄 Refresh All Statuses", callback_data=f"refresh_orders_{uid}"))
        bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        print(f"Error in show orders: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred while fetching your orders.", reply_markup=main_menu())

def notify_order_completed(user_id, order):
    try:
        bot.send_message(
            user_id,
            f"✅ *Order Completed!*\n\n"
            f"🆔 Order ID: {order['api_order_id']}\n"
            f"📦 Service: {order['service']}\n"
            f"🔢 Quantity: {order['qty']}\n"
            f"📊 Start Count: {order['status_data'].get('start_count', 'N/A')}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Notification failed: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('refresh_orders_'))
def refresh_orders(call):
    try:
        user_id = call.data.split('_')[2]
        update_all_orders_status(user_id)
        bot.answer_callback_query(call.id, "All order statuses updated!")
        show_orders(call.message)
    except Exception as e:
        print(f"Error refreshing orders: {e}")
        bot.answer_callback_query(call.id, "Error updating orders")

def update_all_orders_status(user_id):
    try:
        users = load_json(USERS_FILE)
        orders = load_json(ORDERS_FILE)
        
        if user_id not in users or not users[user_id].get('orders'):
            return
        
        changed = False
        
        for order in users[user_id]['orders']:
            if order['status'] in ['Processing', 'Partial']:
                try:
                    api_response = make_api_request({
                        'key': API_KEY,
                        'action': 'status',
                        'order': order['api_order_id']
                    })
                    if 'error' not in api_response:
                        order['status_data'] = {
                            'start_count': api_response.get('start_count'),
                            'remains': api_response.get('remains'),
                            'status': api_response.get('status', 'Processing')
                        }
                        if api_response.get('status') == 'Completed' and order['status'] != 'Completed':
                            order['status'] = 'Completed'
                            notify_order_completed(user_id, order)
                            changed = True
                except Exception as e:
                    print(f"Error checking order status: {e}")
        
        if changed:
            # Update global orders list
            for global_order in orders:
                for user_order in users[user_id]['orders']:
                    if global_order['api_order_id'] == user_order['api_order_id']:
                        global_order.update(user_order)
                        break
            
            save_json(USERS_FILE, users)
            save_json(ORDERS_FILE, orders)
    except Exception as e:
        print(f"Error updating order statuses: {e}")

# Balance handler
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(msg):
    try:
        users = load_json(USERS_FILE)
        uid = str(msg.from_user.id)
        
        if uid not in users:
            return bot.send_message(msg.chat.id, "❌ Please use /start first.", reply_markup=main_menu())
        
        text = f"""💰 *Balance Information:*
━━━━━━━━━━━━━━━━
💵 *Current Balance:* Rs {float(users[uid]['balance']):.2f}
🛍️ *Total Spent:* Rs {float(users[uid]['total_spent']):.2f}
👥 *Referral Earnings:* Rs {float(users[uid].get('referral_earnings', 0)):.2f}
━━━━━━━━━━━━━━━━"""
        
        bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        print(f"Error in balance handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Refill/Cancel order handlers
@bot.message_handler(func=lambda m: m.text in ["🔄 Refill Order", "❌ Cancel Order"])
def handle_order_action(msg):
    try:
        action = "refill" if msg.text == "🔄 Refill Order" else "cancel"
        user_states[msg.chat.id] = {'step': f'{action}_order'}
        bot.send_message(msg.chat.id, 
                        f"🆔 Please enter your Order ID for {action}:", 
                        reply_markup=back_keyboard())
    except Exception as e:
        print(f"Error in order action handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') in ['refill_order', 'cancel_order'])
def process_order_action(msg):
    try:
        if msg.text == "🔙 Back":
            del user_states[msg.chat.id]
            return bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())
        
        action = user_states[msg.chat.id]['step'].split('_')[0]
        order_id = msg.text.strip()
        users = load_json(USERS_FILE)
        orders = load_json(ORDERS_FILE)
        uid = str(msg.from_user.id)
        
        if uid not in users or not users[uid].get('orders'):
            bot.send_message(msg.chat.id, "❌ You don't have any orders yet!", reply_markup=main_menu())
            del user_states[msg.chat.id]
            return
        
        user_order = next((o for o in users[uid]['orders'] if o['api_order_id'] == order_id), None)
        if not user_order:
            bot.send_message(msg.chat.id, "❌ Order not found! Please check your Order ID.", reply_markup=main_menu())
            del user_states[msg.chat.id]
            return
        
        if action == 'refill':
            try:
                api_response = make_api_request({
                    'key': API_KEY,
                    'action': 'refill',
                    'order': user_order['api_order_id']
                })
                if 'error' in api_response:
                    raise Exception(api_response['error'])
                if api_response.get('status') != 'Success':
                    raise Exception(api_response.get('message', 'Refill failed'))
                
                bot.send_message(
                    msg.chat.id,
                    f"✅ Refill request submitted successfully!\n\n"
                    f"📦 Service: {user_order['service']}\n"
                    f"🆔 Order ID: {order_id}\n"
                    f"🌐 API Order ID: {user_order['api_order_id']}\n\n"
                    f"Your order will be processed shortly.",
                    reply_markup=main_menu()
                )
                
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"🔄 Refill Request!\n\n"
                        f"👤 User: @{msg.from_user.username}\n"
                        f"🆔 Order ID: {order_id}\n"
                        f"📦 Service: {user_order['service']}\n"
                        f"🌐 API Order ID: {user_order['api_order_id']}"
                    )
                except Exception as e:
                    print(f"Admin notification failed: {e}")
                
            except Exception as e:
                bot.send_message(
                    msg.chat.id,
                    f"❌ Refill failed!\n\nError: {str(e)}\n\nPlease try again later or contact support.",
                    reply_markup=main_menu()
                )
        
        elif action == 'cancel':
            try:
                api_response = make_api_request({
                    'key': API_KEY,
                    'action': 'cancel',
                    'order': user_order['api_order_id']
                })
                if 'error' in api_response:
                    raise Exception(api_response['error'])
                if api_response.get('status') != 'Success':
                    raise Exception(api_response.get('message', 'Cancellation failed'))
                
                user_order['status'] = 'Cancelled'
                for o in orders:
                    if o['api_order_id'] == order_id:
                        o['status'] = 'Cancelled'
                        break
                
                save_json(USERS_FILE, users)
                save_json(ORDERS_FILE, orders)
                
                bot.send_message(
                    msg.chat.id,
                    f"❌ Order cancelled successfully!\n\n"
                    f"📦 Service: {user_order['service']}\n"
                    f"🆔 Order ID: {order_id}\n"
                    f"🌐 API Order ID: {user_order['api_order_id']}\n\n"
                    f"Any unused balance will be refunded.",
                    reply_markup=main_menu()
                )
                
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"❌ Order Cancelled!\n\n"
                        f"👤 User: @{msg.from_user.username}\n"
                        f"🆔 Order ID: {order_id}\n"
                        f"📦 Service: {user_order['service']}\n"
                        f"🌐 API Order ID: {user_order['api_order_id']}"
                    )
                except Exception as e:
                    print(f"Admin notification failed: {e}")
                
            except Exception as e:
                bot.send_message(
                    msg.chat.id,
                    f"❌ Cancellation failed!\n\nError: {str(e)}\n\nPlease try again later or contact support.",
                    reply_markup=main_menu()
                )
        
        del user_states[msg.chat.id]
    except Exception as e:
        print(f"Error in process order action: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

# Admin commands
@bot.message_handler(commands=['setdiscount'])
def set_discount(msg):
    if str(msg.from_user.id) != str(ADMIN_ID):
        return
    
    try:
        # Command format: /setdiscount user_id service_id discount_percent
        _, user_id, service_id, discount = msg.text.split()
        discount = float(discount)
        
        if not 0 <= discount <= 100:
            return bot.send_message(msg.chat.id, "Discount must be between 0-100%")
            
        users = load_json(USERS_FILE)
        
        if user_id not in users:
            return bot.send_message(msg.chat.id, "User not found")
            
        if 'custom_discounts' not in users[user_id]:
            users[user_id]['custom_discounts'] = {}
            
        users[user_id]['custom_discounts'][service_id] = discount
        save_json(USERS_FILE, users)
        
        bot.send_message(msg.chat.id, f"✅ Custom discount set!\nUser: {user_id}\nService: {service_id}\nDiscount: {discount}%")
        
    except Exception as e:
        bot.send_message(msg.chat.id, f"Usage: /setdiscount <user_id> <service_id> <discount_percent>\nError: {str(e)}")

@bot.message_handler(commands=['syncservices'])
def sync_services(msg):
    if str(msg.from_user.id) != str(ADMIN_ID):
        return
    
    try:
        api_response = make_api_request({
            'key': API_KEY,
            'action': 'services'
        })
        
        if isinstance(api_response, list):
            services_data = {}
            for idx, service in enumerate(api_response, start=1):
                services_data[str(idx)] = {
                    'name': service.get('name'),
                    'base_price': float(service.get('rate', 0)) * 100,  # Convert to your currency
                    'category': service.get('category'),
                    'api_id': service.get('service'),
                    'min': int(service.get('min', 0)),
                    'max': int(service.get('max', 0)),
                    'description': service.get('type', ''),
                    'default_discount': 5,  # Default values
                    'special_discount': 15
                }
            
            save_json(SERVICES_FILE, services_data)
            bot.send_message(msg.chat.id, f"✅ Synced {len(services_data)} services from API")
        else:
            bot.send_message(msg.chat.id, f"❌ Error: {api_response.get('error', 'Unknown error')}")
            
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Sync failed: {str(e)}")

@bot.message_handler(commands=['apibalance'])
def api_balance(msg):
    if str(msg.from_user.id) != str(ADMIN_ID):
        return
    
    try:
        api_response = make_api_request({
            'key': API_KEY,
            'action': 'balance'
        })
        
        if 'balance' in api_response:
            bot.send_message(msg.chat.id, f"💰 API Balance: {api_response['balance']} {api_response.get('currency', 'USD')}")
        else:
            bot.send_message(msg.chat.id, f"❌ Error: {api_response.get('error', 'Unknown error')}")
            
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Balance check failed: {str(e)}")

# Back to main menu
@bot.message_handler(func=lambda m: m.text == "Main Menu")
def back_to_main(msg):
    try:
        if msg.chat.id in user_states:
            del user_states[msg.chat.id]
        bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())
    except Exception as e:
        print(f"Error in back to main: {e}")

# Back button handler
@bot.message_handler(func=lambda m: m.text == "🔙 Back")
def handle_back_button(msg):
    try:
        current_state = user_states.get(msg.chat.id, {})
        
        if 'step' in current_state:
            if current_state['step'] == 'link':
                category = current_state.get('category', 'TikTok')
                del user_states[msg.chat.id]
                return show_category(types.Message(message_id=msg.message_id, chat=msg.chat, from_user=msg.from_user, text=category))
            elif current_state['step'] == 'quantity':
                user_states[msg.chat.id]['step'] = 'link'
                return bot.send_message(msg.chat.id, "🔗 Please enter your link:", reply_markup=back_keyboard())
            elif current_state['step'] == 'confirm':
                user_states[msg.chat.id]['step'] = 'quantity'
                return bot.send_message(msg.chat.id, 
                                     f"🔢 Please enter quantity (Min: {user_states[msg.chat.id]['min']}, Max: {user_states[msg.chat.id]['max']}):",
                                     reply_markup=back_keyboard())
            elif current_state['step'] == 'amount':
                del user_states[msg.chat.id]
                return bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())
            elif current_state['step'] == 'method':
                user_states[msg.chat.id]['step'] = 'amount'
                return bot.send_message(msg.chat.id, 
                                     "✅ *Payment Karne Ke Baad Neeche Amount Likhein (Kam Se Kam Rs 20):*", 
                                     parse_mode="Markdown", 
                                     reply_markup=back_keyboard())
            elif current_state['step'] == 'screenshot':
                user_states[msg.chat.id]['step'] = 'method'
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.row("JazzCash", "EasyPaisa")
                kb.row("Bank Transfer", "Other")
                kb.row("🔙 Back", "Cancel")
                return bot.send_message(msg.chat.id, "📟 Select payment method:", reply_markup=kb)
            elif current_state['step'] == 'confirm_request':
                user_states[msg.chat.id]['step'] = 'screenshot'
                return bot.send_message(msg.chat.id, 
                                     "📸 Payment ka screenshot send kar de:", 
                                     reply_markup=back_keyboard())
            elif current_state['step'] in ['refill_order', 'cancel_order']:
                del user_states[msg.chat.id]
                return bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())
            elif current_state['step'] == 'sim_db_input':
                del user_states[msg.chat.id]
                return amazing_hacks(msg)
        
        # Default back behavior
        bot.send_message(msg.chat.id, "🏠 Main Menu", reply_markup=main_menu())
    except Exception as e:
        print(f"Error in back button handler: {e}")
        bot.send_message(msg.chat.id, "❌ An error occurred. Please try again.", reply_markup=main_menu())

if __name__ == "__main__":
    initialize_files()
    print("🟢 Bot Running with API Integration...")
    bot.polling(none_stop=True)
    def run():
    bot.polling()  # Add this at the end of adminbot.py to start polling
