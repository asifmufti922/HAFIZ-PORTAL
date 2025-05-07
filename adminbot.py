import telebot
import json
import os
import time
import requests
from datetime import datetime
from telebot.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardRemove
)

# Configuration
ADMIN_ID = 7187468717
BOT_TOKEN = '8139160756:AAFAlP_UvFfuG38c6wSpgkU6_DFvQIyjfXs'

# File Paths
USERS_FILE = 'users.json'
SERVICES_FILE = 'services.json'
REQUESTS_FILE = 'fund_requests.json'
ORDERS_FILE = 'orders.json'

# Currency Settings
CURRENCY = 'PKR'  # Pakistani Rupees
CURRENCY_SYMBOL = '₨'

# Emoji Constants
EMOJI = {
    'HOME': "🏠",
    'USERS': "👥",
    'ORDERS': "📦",
    'BALANCE': "💰",
    'BROADCAST': "📢",
    'REQUESTS': "🔄",
    'PRICE': "🏷️",
    'BACK': "🔙",
    'APPROVE': "✅",
    'DECLINE': "❌",
    'ADD': "➕",
    'REMOVE': "➖",
    'EDIT': "✏️",
    'DELETE': "🗑️",
    'INFO': "ℹ️",
    'PROCESSING': "🔄",
    'COMPLETED': "✅",
    'SUPPORT': "🆘",
    'DISCOUNT': "💲",
    'SPECIAL': "⭐",
    'REFRESH': "🔄",
    'STATS': "📊",
    'API': "🌐",
    'SEARCH': "🔍",
    'NEXT': "➡️",
    'PREV': "⬅️",
    'HISTORY': "📜",
    'DETAILS': "📝"
}

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# Initialize Data with proper error handling
def initialize_data():
    try:
        for file in [USERS_FILE, SERVICES_FILE, REQUESTS_FILE, ORDERS_FILE]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    if file == SERVICES_FILE:
                        json.dump({
                            "1": {
                                "name": "TikTok Likes", 
                                "price_per_1000": 60, 
                                "category": "TikTok",
                                "api_id": 9374,
                                "min": 100,
                                "max": 100000,
                                "default_discount": 10,
                                "special_discount": 20,
                                "description": "High quality TikTok likes from real accounts"
                            },
                            "2": {
                                "name": "Instagram Followers", 
                                "price_per_1000": 100, 
                                "category": "Instagram",
                                "api_id": 456,
                                "min": 50,
                                "max": 5000,
                                "default_discount": 5,
                                "special_discount": 15,
                                "description": "Premium Instagram followers with gradual delivery"
                            }
                        }, f, indent=4)
                    elif file in [ORDERS_FILE, REQUESTS_FILE]:
                        json.dump([], f)
                    else:
                        json.dump({}, f)
    except Exception as e:
        print(f"Initialization error: {e}")

# Enhanced data helpers with error handling
def load_data(filename):
    try:
        if not os.path.exists(filename):
            initialize_data()
        with open(filename, 'r') as f:
            data = json.load(f)
            # Validate data structure
            if filename == USERS_FILE and not isinstance(data, dict):
                return {}
            elif filename in [ORDERS_FILE, REQUESTS_FILE] and not isinstance(data, list):
                return []
            elif filename == SERVICES_FILE and not isinstance(data, dict):
                return {
                    "1": {
                        "name": "TikTok Likes", 
                        "price_per_1000": 60, 
                        "category": "TikTok",
                        "api_id": 9374,
                        "min": 100,
                        "max": 100000,
                        "default_discount": 10,
                        "special_discount": 20,
                        "description": "High quality TikTok likes from real accounts"
                    }
                }
            return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {filename}: {e}")
        # Reinitialize file if corrupted
        initialize_data()
        return load_data(filename)
    except Exception as e:
        print(f"Unexpected error loading {filename}: {e}")
        return {} if filename == USERS_FILE else [] if filename in [ORDERS_FILE, REQUESTS_FILE] else {}

def save_data(data, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

# Keyboards with consistent styling
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton(f"{EMOJI['ORDERS']} Orders"),
        KeyboardButton(f"{EMOJI['USERS']} Users"),
        KeyboardButton(f"{EMOJI['BALANCE']} Balance"),
        KeyboardButton(f"{EMOJI['BROADCAST']} Broadcast"),
        KeyboardButton(f"{EMOJI['REQUESTS']} Fund Requests"),
        KeyboardButton(f"{EMOJI['PRICE']} Services"),
        KeyboardButton(f"{EMOJI['DISCOUNT']} Discounts"),
        KeyboardButton(f"{EMOJI['STATS']} Stats"),
        KeyboardButton(f"{EMOJI['SUPPORT']} Support")
    )
    return kb

def back_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(f"{EMOJI['BACK']} Back"))

def cancel_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(f"{EMOJI['BACK']} Cancel"))

def users_list_keyboard(page=0, search_query=None):
    users = load_data(USERS_FILE)
    markup = InlineKeyboardMarkup()
    
    # Filter users if search query provided
    if search_query:
        filtered_users = {
            uid: user for uid, user in users.items() 
            if search_query.lower() in user.get('username', '').lower() or 
               search_query.lower() in uid.lower()
        }
    else:
        filtered_users = users
    
    user_ids = list(filtered_users.keys())
    total_pages = (len(user_ids) // 10 + (1 if len(user_ids) % 10 != 0 else 0))
    
    # Add 10 users per page
    for uid in user_ids[page*10 : (page+1)*10]:
        user = filtered_users[uid]
        btn_text = f"👤 @{user.get('username', uid)}"[:20]
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"userinfo_{uid}"))
    
    # Add navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(f"{EMOJI['PREV']} Prev", callback_data=f"users_prev_{page-1}_{search_query or ''}"))
    if (page+1)*10 < len(user_ids):
        nav_buttons.append(InlineKeyboardButton(f"{EMOJI['NEXT']} Next", callback_data=f"users_next_{page+1}_{search_query or ''}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    # Add search button
    markup.add(InlineKeyboardButton(f"{EMOJI['SEARCH']} Search Users", callback_data="search_users"))
    
    return markup

# Start Command with access control
@bot.message_handler(commands=['start', 'admin'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 Access Denied")
        return
    
    initialize_data()
    bot.send_message(
        message.chat.id,
        "👋 *Admin Panel* - Select Option:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# Admin Statistics
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['STATS']} Stats")
def show_stats(message):
    try:
        users = load_data(USERS_FILE)
        orders = load_data(ORDERS_FILE)
        requests = load_data(REQUESTS_FILE)
        services = load_data(SERVICES_FILE)
        
        total_users = len(users)
        active_users = len([u for u in users.values() if u.get('orders')])
        total_orders = len(orders)
        pending_orders = len([o for o in orders if o.get('status') == 'Processing'])
        completed_orders = len([o for o in orders if o.get('status') == 'Completed'])
        total_requests = len(requests)
        pending_requests = len([r for r in requests if isinstance(r, dict) and r.get('status') == 'pending'])
        total_services = len(services)
        
        text = f"""
📊 *System Statistics*
━━━━━━━━━━━━━━━━
👥 Users: {total_users} ({active_users} active)
📦 Orders: {total_orders} (🔄 {pending_orders} | ✅ {completed_orders})
🔄 Fund Requests: {total_requests} ({pending_requests} pending)
🏷️ Services: {total_services}
━━━━━━━━━━━━━━━━
💰 Total Revenue: {CURRENCY_SYMBOL}{sum(o.get('price', 0) for o in orders):.2f}
"""
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error generating stats: {str(e)}",
            reply_markup=main_menu()
        )

# Enhanced Balance Management
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['BALANCE']} Balance")
def balance_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(f"{EMOJI['ADD']} Add Balance"),
        KeyboardButton(f"{EMOJI['REMOVE']} Remove Balance"),
        KeyboardButton(f"{EMOJI['INFO']} View Balances"),
        KeyboardButton(f"{EMOJI['BACK']} Back")
    )
    bot.send_message(
        message.chat.id,
        "💰 *Balance Management* - Select Option:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['ADD']} Add Balance")
def add_balance_start(message):
    msg = bot.send_message(
        message.chat.id,
        "👤 Enter user ID and amount to add (format: user_id amount):",
        reply_markup=back_keyboard()
    )
    bot.register_next_step_handler(msg, process_add_balance)

def process_add_balance(message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return balance_menu(message)
        
        parts = message.text.split()
        if len(parts) < 2:
            raise ValueError("Invalid format")
            
        user_id = parts[0]
        amount = float(parts[1])
        
        users = load_data(USERS_FILE)
        
        if user_id not in users:
            users[user_id] = {
                'username': f"user_{user_id}",
                'balance': 0,
                'orders': [],
                'total_spent': 0,
                'join_date': time.time()
            }
        
        users[user_id]['balance'] = round(users[user_id].get('balance', 0) + amount, 2)
        
        if save_data(users, USERS_FILE):
            bot.send_message(
                message.chat.id,
                f"✅ Added {CURRENCY_SYMBOL}{amount:.2f} to user {user_id}\nNew balance: {CURRENCY_SYMBOL}{users[user_id]['balance']:.2f}",
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save user data")
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}\n\nPlease use format: user_id amount",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['REMOVE']} Remove Balance")
def remove_balance_start(message):
    msg = bot.send_message(
        message.chat.id,
        "👤 Enter user ID and amount to remove (format: user_id amount):",
        reply_markup=back_keyboard()
    )
    bot.register_next_step_handler(msg, process_remove_balance)

def process_remove_balance(message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return balance_menu(message)
        
        parts = message.text.split()
        if len(parts) < 2:
            raise ValueError("Invalid format")
            
        user_id = parts[0]
        amount = float(parts[1])
        
        users = load_data(USERS_FILE)
        
        if user_id not in users:
            raise ValueError("User not found")
        
        if users[user_id]['balance'] < amount:
            raise ValueError("Insufficient balance")
        
        users[user_id]['balance'] = round(users[user_id]['balance'] - amount, 2)
        
        if save_data(users, USERS_FILE):
            bot.send_message(
                message.chat.id,
                f"✅ Removed {CURRENCY_SYMBOL}{amount:.2f} from user {user_id}\nNew balance: {CURRENCY_SYMBOL}{users[user_id]['balance']:.2f}",
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save user data")
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}\n\nPlease use format: user_id amount",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['INFO']} View Balances")
def view_balances(message):
    try:
        users = load_data(USERS_FILE)
        
        text = "💰 *User Balances*\n━━━━━━━━━━━━━━━━\n"
        for user_id, user in users.items():
            text += f"👤 @{user.get('username', user_id)}: {CURRENCY_SYMBOL}{user.get('balance', 0):.2f}\n"
        
        text += f"\n💰 Total Balance: {CURRENCY_SYMBOL}{sum(u.get('balance', 0) for u in users.values()):.2f}"
        
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading balances: {str(e)}",
            reply_markup=main_menu()
        )

# Enhanced Discount Management
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['DISCOUNT']} Discounts")
def discount_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(f"{EMOJI['SPECIAL']} Special Users"),
        KeyboardButton(f"{EMOJI['EDIT']} Custom Discounts"),
        KeyboardButton(f"{EMOJI['BACK']} Back")
    )
    bot.send_message(
        message.chat.id,
        "💲 *Discount Management* - Select Option:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['SPECIAL']} Special Users")
def special_users_menu(message):
    try:
        users = load_data(USERS_FILE)
        special_users = [uid for uid, user in users.items() if user.get('is_special', False)]
        
        markup = InlineKeyboardMarkup()
        for user_id in special_users[:50]:  # Limit to 50 users per page
            user = users[user_id]
            btn_text = f"⭐ @{user.get('username', user_id)}"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"special_{user_id}"))
        
        if len(special_users) > 50:
            markup.add(InlineKeyboardButton(f"{EMOJI['NEXT']} Next Page", callback_data=f"special_next_1"))
        
        markup.add(InlineKeyboardButton(f"{EMOJI['ADD']} Add Special User", callback_data="add_special"))
        markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_discounts"))
        
        bot.send_message(
            message.chat.id,
            f"⭐ *Special Users* ({len(special_users)}):",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading special users: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data == "add_special")
def add_special_user(call):
    msg = bot.send_message(
        call.message.chat.id,
        "👤 Enter user ID or @username to make special:",
        reply_markup=back_keyboard()
    )
    bot.register_next_step_handler(msg, process_add_special)

def process_add_special(message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return discount_menu(message)
        
        user_input = message.text.strip()
        users = load_data(USERS_FILE)
        
        # Check if input is username
        if user_input.startswith('@'):
            user_id = next((uid for uid, user in users.items() if user.get('username', '').lower() == user_input[1:].lower()), None)
            if not user_id:
                raise ValueError("User not found")
        else:
            user_id = user_input
        
        if user_id not in users:
            users[user_id] = {
                'username': user_input if user_input.startswith('@') else f"user_{user_id}",
                'balance': 0,
                'orders': [],
                'total_spent': 0,
                'is_special': True,
                'join_date': time.time()
            }
        else:
            users[user_id]['is_special'] = True
        
        if save_data(users, USERS_FILE):
            bot.send_message(
                message.chat.id,
                f"✅ User {user_id} is now a special member!",
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save user data")
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith('special_'))
def manage_special_user(call):
    try:
        user_id = call.data.split('_')[1]
        users = load_data(USERS_FILE)
        user = users.get(user_id)
        
        if not user:
            bot.answer_callback_query(call.id, "User not found", show_alert=True)
            return
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(f"{EMOJI['REMOVE']} Remove Special", callback_data=f"remove_special_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['EDIT']} Set Service Discounts", callback_data=f"set_special_discounts_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_special_users")
        )
        
        # Get service discounts if any
        service_discounts = user.get('special_discounts', {})
        services = load_data(SERVICES_FILE)
        
        discount_text = ""
        if service_discounts:
            discount_text = "\n\n⭐ *Service Discounts:*\n"
            for srv_id, discount in service_discounts.items():
                srv_name = services.get(srv_id, {}).get('name', f"Service {srv_id}")
                discount_text += f"📦 {srv_name}: {discount}%\n"
        
        bot.edit_message_text(
            f"⭐ *Special User*\n━━━━━━━━━━━━━━━━\n🆔 ID: `{user_id}`\n👤 Username: @{user.get('username', 'N/A')}\n💰 Balance: {CURRENCY_SYMBOL}{user.get('balance', 0):.2f}\n📦 Orders: {len(user.get('orders', []))}{discount_text}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('set_special_discounts_'))
def set_special_discounts_start(call):
    try:
        user_id = call.data.split('_')[3]
        services = load_data(SERVICES_FILE)
        
        markup = InlineKeyboardMarkup()
        for srv_id, service in services.items():
            markup.add(InlineKeyboardButton(
                f"{service['name']} (Current: {service['special_discount']}%)",
                callback_data=f"set_sdiscount_{user_id}_{srv_id}"
            ))
        
        markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data=f"special_{user_id}"))
        
        bot.edit_message_text(
            "📦 Select a service to set special discount:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('set_sdiscount_'))
def set_special_discount(call):
    try:
        _, _, user_id, srv_id = call.data.split('_')
        services = load_data(SERVICES_FILE)
        service = services.get(srv_id)
        
        if not service:
            bot.answer_callback_query(call.id, "Service not found", show_alert=True)
            return
        
        msg = bot.send_message(
            call.message.chat.id,
            f"💲 Enter discount percentage for {service['name']} (0-100):",
            reply_markup=back_keyboard()
        )
        
        bot.register_next_step_handler(msg, process_special_discount, user_id, srv_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

def process_special_discount(message, user_id, srv_id):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return manage_special_user(message)
        
        discount = float(message.text)
        if discount < 0 or discount > 100:
            raise ValueError("Discount must be between 0-100")
        
        users = load_data(USERS_FILE)
        if user_id not in users:
            raise ValueError("User not found")
        
        if 'special_discounts' not in users[user_id]:
            users[user_id]['special_discounts'] = {}
        
        users[user_id]['special_discounts'][srv_id] = discount
        
        if save_data(users, USERS_FILE):
            bot.send_message(
                message.chat.id,
                f"✅ Set {discount}% discount for user {user_id} on service {services[srv_id]['name']}",
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save user data")
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Invalid discount. Please enter a number between 0-100.",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith('remove_special_'))
def remove_special_user(call):
    try:
        user_id = call.data.split('_')[2]
        users = load_data(USERS_FILE)
        
        if user_id in users:
            users[user_id]['is_special'] = False
            if 'special_discounts' in users[user_id]:
                del users[user_id]['special_discounts']
            
            if save_data(users, USERS_FILE):
                bot.edit_message_text(
                    f"✅ Removed special status from {user_id}",
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                raise Exception("Failed to save user data")
        else:
            bot.answer_callback_query(call.id, "User not found", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

# Enhanced Custom Discounts
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['EDIT']} Custom Discounts")
def custom_discounts_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(f"{EMOJI['ADD']} Set Discount"),
        KeyboardButton(f"{EMOJI['REMOVE']} Remove Discount"),
        KeyboardButton(f"{EMOJI['INFO']} View Discounts"),
        KeyboardButton(f"{EMOJI['BACK']} Back")
    )
    bot.send_message(
        message.chat.id,
        "💲 *Custom Discounts* - Select Option:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['ADD']} Set Discount")
def set_discount_start(message):
    msg = bot.send_message(
        message.chat.id,
        "📝 Enter details in format:\n\nUser ID\nService ID\nDiscount Percentage\n\nExample:\n123456789\n1\n25",
        reply_markup=back_keyboard()
    )
    bot.register_next_step_handler(msg, process_set_discount)

def process_set_discount(message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return custom_discounts_menu(message)
        
        parts = message.text.split('\n')
        if len(parts) < 3:
            raise ValueError("Incomplete details")
            
        user_id = parts[0].strip()
        service_id = parts[1].strip()
        discount = float(parts[2].strip())
        
        if discount < 0 or discount > 100:
            raise ValueError("Discount must be 0-100")
        
        users = load_data(USERS_FILE)
        services = load_data(SERVICES_FILE)
        
        if service_id not in services:
            raise ValueError("Service not found")
        
        if user_id not in users:
            users[user_id] = {
                'username': f"user_{user_id}",
                'balance': 0,
                'orders': [],
                'total_spent': 0,
                'join_date': time.time()
            }
        
        if 'custom_discounts' not in users[user_id]:
            users[user_id]['custom_discounts'] = {}
        
        users[user_id]['custom_discounts'][service_id] = discount
        
        if save_data(users, USERS_FILE):
            bot.send_message(
                message.chat.id,
                f"✅ Set {discount}% discount for user {user_id} on {services[service_id]['name']}",
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save user data")
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}\n\nPlease use format:\nUser ID\nService ID\nDiscount Percentage",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['INFO']} View Discounts")
def view_discounts(message):
    try:
        users = load_data(USERS_FILE)
        services = load_data(SERVICES_FILE)
        
        has_discounts = False
        text = "💲 *Custom Discounts*\n━━━━━━━━━━━━━━━━\n"
        
        for user_id, user in users.items():
            if 'custom_discounts' in user and user['custom_discounts']:
                has_discounts = True
                text += f"👤 User: @{user.get('username', user_id)}\n"
                for service_id, discount in user['custom_discounts'].items():
                    service_name = services.get(service_id, {}).get('name', f"Service {service_id}")
                    text += f"📦 {service_name}: {discount}%\n"
                text += "━━━━━━━━━━━━━━━━\n"
        
        if not has_discounts:
            text += "No custom discounts set"
        
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading discounts: {str(e)}",
            reply_markup=main_menu()
        )

# Enhanced Services Management
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['PRICE']} Services")
def services_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(f"{EMOJI['ADD']} Add Service"),
        KeyboardButton(f"{EMOJI['EDIT']} Edit Service"),
        KeyboardButton(f"{EMOJI['DELETE']} Delete Service"),
        KeyboardButton(f"{EMOJI['BACK']} Back")
    )
    bot.send_message(
        message.chat.id,
        "📦 *Services Management* - Select Option:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['ADD']} Add Service")
def add_service(message):
    msg = bot.send_message(
        message.chat.id, 
        "📝 Send service details in format:\n\n"
        "📌 Service Name\n"
        f"💵 Price per 1000 ({CURRENCY})\n"
        "📂 Category\n"
        "🔢 Min Quantity\n"
        "🔢 Max Quantity\n"
        "🌐 API ID\n"
        "💲 Default Discount (%)\n"
        "⭐ Special Discount (%)\n"
        "📝 Description\n\n"
        "Example:\n"
        "Twitter Followers\n"
        "80\n"
        "Twitter\n"
        "100\n"
        "10000\n"
        "1234\n"
        "5\n"
        "15\n"
        "High quality Twitter followers with fast delivery",
        reply_markup=back_keyboard()
    )
    bot.register_next_step_handler(msg, process_add_service)

def process_add_service(message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return services_menu(message)
        
        parts = message.text.split('\n')
        if len(parts) < 8:
            raise ValueError("Incomplete details")
            
        name = parts[0].strip()
        price = float(parts[1].strip())
        category = parts[2].strip()
        min_qty = int(parts[3].strip())
        max_qty = int(parts[4].strip())
        api_id = int(parts[5].strip())
        def_discount = float(parts[6].strip())
        spc_discount = float(parts[7].strip())
        description = parts[8].strip() if len(parts) > 8 else ""
        
        services = load_data(SERVICES_FILE)
        
        # Generate a new service ID
        new_id = str(max((int(k) for k in services.keys()), default=0) + 1)
        
        services[new_id] = {
            "name": name,
            "price_per_1000": price,
            "category": category,
            "min": min_qty,
            "max": max_qty,
            "api_id": api_id,
            "default_discount": def_discount,
            "special_discount": spc_discount,
            "description": description
        }
        
        if save_data(services, SERVICES_FILE):
            bot.send_message(
                message.chat.id, 
                f"✅ Added new service:\n\n📦 {name}\n💵 {CURRENCY_SYMBOL}{price} per 1000\n📂 {category}\n🔢 Qty: {min_qty}-{max_qty}\n🌐 API ID: {api_id}\n💲 Discounts: Default {def_discount}%, Special {spc_discount}%", 
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save service data")
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"❌ Error: {str(e)}\n\nPlease follow the correct format.", 
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['EDIT']} Edit Service")
def edit_service_start(message):
    services = load_data(SERVICES_FILE)
    
    markup = InlineKeyboardMarkup()
    for srv_id, service in services.items():
        markup.add(InlineKeyboardButton(
            f"{service['name']} ({CURRENCY_SYMBOL}{service['price_per_1000']}/1k)", 
            callback_data=f"edit_srv_{srv_id}"
        ))
    
    markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_services"))
    
    bot.send_message(
        message.chat.id,
        "📦 Select service to edit:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srv_'))
def edit_service_select(call):
    try:
        srv_id = call.data.split('_')[2]
        services = load_data(SERVICES_FILE)
        service = services.get(srv_id)
        
        if not service:
            bot.answer_callback_query(call.id, "Service not found", show_alert=True)
            return
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(f"{EMOJI['EDIT']} Name", callback_data=f"edit_srvname_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['EDIT']} Price", callback_data=f"edit_srvprice_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['EDIT']} Category", callback_data=f"edit_srvcat_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['EDIT']} Min/Max", callback_data=f"edit_srvqty_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['EDIT']} Discounts", callback_data=f"edit_srvdisc_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['EDIT']} Description", callback_data=f"edit_srvdesc_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_edit_services")
        )
        
        bot.edit_message_text(
            f"✏️ *Editing Service*\n━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: {srv_id}\n"
            f"📛 Name: {service['name']}\n"
            f"💵 Price: {CURRENCY_SYMBOL}{service['price_per_1000']} per 1000\n"
            f"📂 Category: {service['category']}\n"
            f"🔢 Quantity: {service['min']}-{service['max']}\n"
            f"🌐 API ID: {service['api_id']}\n"
            f"💲 Discounts: Default {service['default_discount']}%, Special {service['special_discount']}%\n"
            f"📝 Description: {service.get('description', 'N/A')}\n"
            f"━━━━━━━━━━━━━━━━",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srvname_'))
def edit_service_name(call):
    try:
        srv_id = call.data.split('_')[2]
        user_states[call.message.chat.id] = {'editing': 'name', 'srv_id': srv_id}
        
        bot.send_message(
            call.message.chat.id,
            f"✏️ Enter new name for service:",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srvprice_'))
def edit_service_price(call):
    try:
        srv_id = call.data.split('_')[2]
        user_states[call.message.chat.id] = {'editing': 'price', 'srv_id': srv_id}
        
        bot.send_message(
            call.message.chat.id,
            f"💵 Enter new price per 1000 ({CURRENCY}):",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srvcat_'))
def edit_service_category(call):
    try:
        srv_id = call.data.split('_')[2]
        user_states[call.message.chat.id] = {'editing': 'category', 'srv_id': srv_id}
        
        bot.send_message(
            call.message.chat.id,
            f"📂 Enter new category:",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srvqty_'))
def edit_service_quantity(call):
    try:
        srv_id = call.data.split('_')[2]
        user_states[call.message.chat.id] = {'editing': 'quantity', 'srv_id': srv_id}
        
        bot.send_message(
            call.message.chat.id,
            f"🔢 Enter new min and max quantity (format: min max):",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srvdisc_'))
def edit_service_discounts(call):
    try:
        srv_id = call.data.split('_')[2]
        user_states[call.message.chat.id] = {'editing': 'discounts', 'srv_id': srv_id}
        
        bot.send_message(
            call.message.chat.id,
            f"💲 Enter new default and special discounts (format: default special):",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('edit_srvdesc_'))
def edit_service_description(call):
    try:
        srv_id = call.data.split('_')[2]
        user_states[call.message.chat.id] = {'editing': 'description', 'srv_id': srv_id}
        
        bot.send_message(
            call.message.chat.id,
            f"📝 Enter new description:",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.message_handler(func=lambda m: m.chat.id in user_states and 'editing' in user_states[m.chat.id])
def process_service_edit(message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            del user_states[message.chat.id]
            return services_menu(message)
        
        state = user_states[message.chat.id]
        editing = state['editing']
        srv_id = state['srv_id']
        services = load_data(SERVICES_FILE)
        
        if srv_id not in services:
            raise ValueError("Service not found")
        
        if editing == 'name':
            services[srv_id]['name'] = message.text
            success_msg = f"✅ Updated name to: {message.text}"
        elif editing == 'price':
            services[srv_id]['price_per_1000'] = float(message.text)
            success_msg = f"✅ Updated price to: {CURRENCY_SYMBOL}{message.text}"
        elif editing == 'category':
            services[srv_id]['category'] = message.text
            success_msg = f"✅ Updated category to: {message.text}"
        elif editing == 'quantity':
            min_qty, max_qty = message.text.split()
            services[srv_id]['min'] = int(min_qty)
            services[srv_id]['max'] = int(max_qty)
            success_msg = f"✅ Updated quantity range to: {min_qty}-{max_qty}"
        elif editing == 'discounts':
            def_disc, spc_disc = message.text.split()
            services[srv_id]['default_discount'] = float(def_disc)
            services[srv_id]['special_discount'] = float(spc_disc)
            success_msg = f"✅ Updated discounts to: Default {def_disc}%, Special {spc_disc}%"
        elif editing == 'description':
            services[srv_id]['description'] = message.text
            success_msg = f"✅ Updated description"
        else:
            raise ValueError("Invalid edit type")
        
        if save_data(services, SERVICES_FILE):
            del user_states[message.chat.id]
            bot.send_message(
                message.chat.id,
                success_msg,
                reply_markup=main_menu()
            )
        else:
            raise Exception("Failed to save service data")
    except ValueError as e:
        bot.send_message(
            message.chat.id,
            f"❌ Invalid input: {str(e)}",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data == 'back_edit_services')
def back_to_edit_services(call):
    services = load_data(SERVICES_FILE)
    
    markup = InlineKeyboardMarkup()
    for srv_id, service in services.items():
        markup.add(InlineKeyboardButton(
            f"{service['name']} ({CURRENCY_SYMBOL}{service['price_per_1000']}/1k)", 
            callback_data=f"edit_srv_{srv_id}"
        ))
    
    markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_services"))
    
    bot.edit_message_text(
        "📦 Select service to edit:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['DELETE']} Delete Service")
def delete_service_start(message):
    services = load_data(SERVICES_FILE)
    
    markup = InlineKeyboardMarkup()
    for srv_id, service in services.items():
        markup.add(InlineKeyboardButton(
            f"{service['name']} ({CURRENCY_SYMBOL}{service['price_per_1000']}/1k)", 
            callback_data=f"del_srv_{srv_id}"
        ))
    
    markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_services"))
    
    bot.send_message(
        message.chat.id,
        "🗑️ Select service to delete:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith('del_srv_'))
def confirm_delete_service(call):
    try:
        srv_id = call.data.split('_')[2]
        services = load_data(SERVICES_FILE)
        service = services.get(srv_id)
        
        if not service:
            bot.answer_callback_query(call.id, "Service not found", show_alert=True)
            return
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(f"{EMOJI['DELETE']} Confirm Delete", callback_data=f"confirm_del_{srv_id}"),
            InlineKeyboardButton(f"{EMOJI['BACK']} Cancel", callback_data="back_del_services")
        )
        
        bot.edit_message_text(
            f"⚠️ *Confirm Delete*\n━━━━━━━━━━━━━━━━\n"
            f"📦 Service: {service['name']}\n"
            f"🆔 ID: {srv_id}\n"
            f"💵 Price: {CURRENCY_SYMBOL}{service['price_per_1000']} per 1000\n"
            f"📂 Category: {service['category']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Are you sure you want to delete this service?",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('confirm_del_'))
def delete_service(call):
    try:
        srv_id = call.data.split('_')[2]
        services = load_data(SERVICES_FILE)
        
        if srv_id not in services:
            bot.answer_callback_query(call.id, "Service not found", show_alert=True)
            return
        
        service_name = services[srv_id]['name']
        del services[srv_id]
        
        if save_data(services, SERVICES_FILE):
            bot.edit_message_text(
                f"✅ Deleted service: {service_name}",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            raise Exception("Failed to save service data")
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == 'back_del_services')
def back_to_delete_services(call):
    services = load_data(SERVICES_FILE)
    
    markup = InlineKeyboardMarkup()
    for srv_id, service in services.items():
        markup.add(InlineKeyboardButton(
            f"{service['name']} ({CURRENCY_SYMBOL}{service['price_per_1000']}/1k)", 
            callback_data=f"del_srv_{srv_id}"
        ))
    
    markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_services"))
    
    bot.edit_message_text(
        "🗑️ Select service to delete:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data == 'back_services')
def back_to_services_menu(call):
    try:
        bot.edit_message_text(
            "📦 *Services Management* - Select Option:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        services_menu(call.message)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

# Enhanced Orders Management
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['ORDERS']} Orders")
def orders_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(f"{EMOJI['PROCESSING']} Pending Orders"),
        KeyboardButton(f"{EMOJI['COMPLETED']} Completed Orders"),
        KeyboardButton(f"{EMOJI['REFRESH']} Refresh All"),
        KeyboardButton(f"{EMOJI['BACK']} Back")
    )
    bot.send_message(
        message.chat.id,
        "📦 *Orders Management* - Select Option:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['PROCESSING']} Pending Orders")
def show_pending_orders(message):
    try:
        orders = load_data(ORDERS_FILE)
        pending_orders = [o for o in orders if isinstance(o, dict) and o.get('status') == 'Processing']
        
        if not pending_orders:
            bot.send_message(
                message.chat.id,
                "ℹ️ No pending orders found",
                reply_markup=main_menu()
            )
            return
        
        bot.send_message(
            message.chat.id,
            f"🔄 *Pending Orders* ({len(pending_orders)}):",
            parse_mode="Markdown"
        )
        
        for order in pending_orders[:10]:  # Limit to 10 orders per message
            text = format_order_text(order)
            markup = create_order_markup(order)
            bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
        
        if len(pending_orders) > 10:
            bot.send_message(
                message.chat.id,
                f"Showing 10 of {len(pending_orders)} pending orders",
                reply_markup=main_menu()
            )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading orders: {str(e)}",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['COMPLETED']} Completed Orders")
def show_completed_orders(message):
    try:
        orders = load_data(ORDERS_FILE)
        completed_orders = [o for o in orders if isinstance(o, dict) and o.get('status') == 'Completed']
        
        if not completed_orders:
            bot.send_message(
                message.chat.id,
                "ℹ️ No completed orders found",
                reply_markup=main_menu()
            )
            return
        
        bot.send_message(
            message.chat.id,
            f"✅ *Completed Orders* ({len(completed_orders)}):",
            parse_mode="Markdown"
        )
        
        for order in completed_orders[:10]:  # Limit to 10 orders per message
            text = format_order_text(order)
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
        
        if len(completed_orders) > 10:
            bot.send_message(
                message.chat.id,
                f"Showing 10 of {len(completed_orders)} completed orders",
                reply_markup=main_menu()
            )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading orders: {str(e)}",
            reply_markup=main_menu()
        )

def format_order_text(order):
    status_info = ""
    if order.get('status_data'):
        sd = order['status_data']
        status_info = f"\n📊 Progress: {sd.get('start_count', 'N/A')}/{order['qty']} (Remains: {sd.get('remains', 'N/A')})"
    
    return f"""
📦 *Order Details*
━━━━━━━━━━━━━━━━
🆔 API Order ID: `{order.get('api_order_id', 'N/A')}`
👤 User: @{order.get('username', 'N/A')} ({order.get('user_id', 'N/A')})
📦 Service: {order.get('service', 'N/A')}
🔢 Quantity: {order.get('qty', 'N/A')}
💸 Price: {CURRENCY_SYMBOL}{order.get('price', 'N/A'):.2f}
🔄 Status: {order.get('status', 'Processing')}{status_info}
📅 Date: {datetime.fromtimestamp(order.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━
"""

def create_order_markup(order):
    markup = InlineKeyboardMarkup()
    if order.get('status') == 'Processing':
        markup.row(
            InlineKeyboardButton(f"{EMOJI['COMPLETED']} Complete", callback_data=f"complete_{order['api_order_id']}"),
            InlineKeyboardButton(f"{EMOJI['INFO']} Refresh", callback_data=f"refresh_{order['api_order_id']}")
        )
    return markup

@bot.callback_query_handler(func=lambda c: c.data.startswith(('complete_', 'refresh_')))
def handle_order_action(call):
    try:
        action, order_id = call.data.split('_')
        orders = load_data(ORDERS_FILE)
        users = load_data(USERS_FILE)
        
        order = next((o for o in orders if isinstance(o, dict) and o.get('api_order_id') == order_id), None)
        if not order:
            bot.answer_callback_query(call.id, "Order not found", show_alert=True)
            return
        
        if action == 'complete':
            order['status'] = 'Completed'
        
        # Update in users data
        user_id = order['user_id']
        if user_id in users:
            for user_order in users[user_id].get('orders', []):
                if user_order.get('api_order_id') == order_id:
                    user_order.update(order)
        
        if save_data(orders, ORDERS_FILE) and save_data(users, USERS_FILE):
            if order['status'] == 'Completed':
                # Notify user
                try:
                    bot.send_message(
                        order['user_id'],
                        f"🎉 Your order has been completed!\n\n"
                        f"📦 Order ID: {order_id}\n"
                        f"🔄 Status: Completed\n\n"
                        f"Thank you for your purchase!"
                    )
                except:
                    pass
            
            # Update the message
            text = format_order_text(order)
            markup = create_order_markup(order)
            
            try:
                if hasattr(call.message, 'caption'):
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
            except:
                pass
            
            bot.answer_callback_query(call.id, "Order updated!")
        else:
            raise Exception("Failed to save data")
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

# Enhanced Users Management
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['USERS']} Users")
def users_menu(message):
    try:
        users = load_data(USERS_FILE)
        markup = InlineKeyboardMarkup()
        
        # Show first 10 users with pagination
        user_ids = list(users.keys())
        for user_id in user_ids[:10]:
            user = users[user_id]
            btn_text = f"👤 @{user.get('username', user_id)}"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"userinfo_{user_id}"))
        
        if len(user_ids) > 10:
            markup.add(InlineKeyboardButton(f"{EMOJI['NEXT']} Next Page", callback_data="users_next_1"))
        
        markup.add(InlineKeyboardButton(f"{EMOJI['SEARCH']} Search Users", callback_data="search_users"))
        
        bot.send_message(
            message.chat.id,
            "👥 *Users List* - Select a user:",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading users: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith('users_next_'))
def show_next_users_page(call):
    try:
        page = int(call.data.split('_')[2])
        users = load_data(USERS_FILE)
        user_ids = list(users.keys())
        
        markup = InlineKeyboardMarkup()
        start_index = page * 10
        end_index = start_index + 10
        
        for user_id in user_ids[start_index:end_index]:
            user = users[user_id]
            btn_text = f"👤 @{user.get('username', user_id)}"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"userinfo_{user_id}"))
        
        # Add navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(f"{EMOJI['PREV']} Prev", callback_data=f"users_prev_{page-1}"))
        if end_index < len(user_ids):
            nav_buttons.append(InlineKeyboardButton(f"{EMOJI['NEXT']} Next", callback_data=f"users_next_{page+1}"))
        
        if nav_buttons:
            markup.row(*nav_buttons)
        
        markup.add(InlineKeyboardButton(f"{EMOJI['SEARCH']} Search Users", callback_data="search_users"))
        
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == 'search_users')
def search_users_callback(call):
    msg = bot.send_message(
        call.message.chat.id,
        "🔍 Enter username or user ID to search:",
        reply_markup=back_keyboard()
    )
    bot.register_next_step_handler(msg, process_user_search_callback, call.message)

def process_user_search_callback(message, original_message):
    try:
        if message.text == f"{EMOJI['BACK']} Back":
            return users_menu(message)
        
        search_query = message.text.strip()
        users = load_data(USERS_FILE)
        
        markup = InlineKeyboardMarkup()
        found = False
        
        for user_id, user in users.items():
            if (search_query.lower() in user.get('username', '').lower()) or (search_query.lower() in user_id.lower()):
                found = True
                btn_text = f"👤 @{user.get('username', user_id)}"
                markup.add(InlineKeyboardButton(btn_text, callback_data=f"userinfo_{user_id}"))
        
        if not found:
            bot.send_message(
                message.chat.id,
                "❌ No users found matching your search",
                reply_markup=main_menu()
            )
            return
        
        markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back to All Users", callback_data="back_to_all_users"))
        
        bot.edit_message_text(
            f"🔍 Search results for '{search_query}':",
            original_message.chat.id,
            original_message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data == 'back_to_all_users')
def back_to_all_users(call):
    users_menu(call.message)

@bot.callback_query_handler(func=lambda c: c.data.startswith('userinfo_'))
def show_user_info(call):
    try:
        user_id = call.data.split('_')[1]
        users = load_data(USERS_FILE)
        user = users.get(user_id)
        
        if not user:
            bot.answer_callback_query(call.id, "User not found", show_alert=True)
            return
        
        orders = load_data(ORDERS_FILE)
        user_orders = [o for o in orders if isinstance(o, dict) and o.get('user_id') == user_id]
        
        text = f"""
👤 *User Information*
━━━━━━━━━━━━━━━━
🆔 ID: `{user_id}`
📛 Username: @{user.get('username', 'N/A')}
💰 Balance: {CURRENCY_SYMBOL}{user.get('balance', 0):.2f}
💸 Total Spent: {CURRENCY_SYMBOL}{user.get('total_spent', 0):.2f}
📦 Orders: {len(user.get('orders', []))}
⭐ Special: {'Yes' if user.get('is_special', False) else 'No'}
📅 Joined: {datetime.fromtimestamp(user.get('join_date', time.time())).strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━
"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(f"{EMOJI['EDIT']} Edit Balance", callback_data=f"edit_balance_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['ORDERS']} View Orders", callback_data=f"view_orders_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data="back_to_users_list")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('view_orders_'))
def view_user_orders(call):
    try:
        user_id = call.data.split('_')[2]
        users = load_data(USERS_FILE)
        user = users.get(user_id)
        
        if not user:
            bot.answer_callback_query(call.id, "User not found", show_alert=True)
            return
        
        orders = load_data(ORDERS_FILE)
        user_orders = [o for o in orders if isinstance(o, dict) and o.get('user_id') == user_id]
        
        if not user_orders:
            bot.answer_callback_query(call.id, "No orders found for this user", show_alert=True)
            return
        
        markup = InlineKeyboardMarkup()
        for order in user_orders[:10]:  # Show first 10 orders
            order_id = order.get('api_order_id', 'N/A')
            service = order.get('service', 'N/A')
            btn_text = f"📦 {service} ({order_id[:6]}...)"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"order_details_{order_id}"))
        
        if len(user_orders) > 10:
            markup.add(InlineKeyboardButton(f"{EMOJI['NEXT']} Next Page", callback_data=f"user_orders_next_{user_id}_1"))
        
        markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data=f"userinfo_{user_id}"))
        
        bot.edit_message_text(
            f"📦 *Orders for user @{user.get('username', user_id)}* ({len(user_orders)}):",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith('order_details_'))
def show_order_details(call):
    try:
        order_id = call.data.split('_')[2]
        orders = load_data(ORDERS_FILE)
        order = next((o for o in orders if isinstance(o, dict) and o.get('api_order_id') == order_id), None)
        
        if not order:
            bot.answer_callback_query(call.id, "Order not found", show_alert=True)
            return
        
        text = format_order_text(order)
        markup = InlineKeyboardMarkup()
        
        if order.get('status') == 'Processing':
            markup.row(
                InlineKeyboardButton(f"{EMOJI['COMPLETED']} Complete", callback_data=f"complete_{order_id}"),
                InlineKeyboardButton(f"{EMOJI['INFO']} Refresh", callback_data=f"refresh_{order_id}")
            )
        
        markup.add(InlineKeyboardButton(f"{EMOJI['BACK']} Back", callback_data=f"view_orders_{order['user_id']}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

# Enhanced Fund Requests Management
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['REQUESTS']} Fund Requests")
def show_requests(message):
    try:
        requests = load_data(REQUESTS_FILE)
        if not isinstance(requests, list):
            requests = []
        
        pending_requests = [r for r in requests if isinstance(r, dict) and r.get('status') == 'pending']
        
        if not pending_requests:
            bot.send_message(
                message.chat.id,
                "ℹ️ No pending fund requests",
                reply_markup=main_menu()
            )
            return
        
        bot.send_message(
            message.chat.id,
            f"🔄 *Pending Fund Requests* ({len(pending_requests)}):",
            parse_mode="Markdown"
        )
        
        for req in pending_requests[:10]:  # Limit to 10 requests per message
            text = f"""
💰 *Fund Request*
━━━━━━━━━━━━━━━━
🆔 ID: `{req.get('request_id', 'N/A')}`
👤 User: @{req.get('username', 'N/A')} ({req.get('user_id', 'N/A')})
💵 Amount: {CURRENCY_SYMBOL}{req.get('amount', 0):.2f}
📟 Method: {req.get('method', 'N/A')}
📅 Date: {datetime.fromtimestamp(req.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━
"""
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton(f"{EMOJI['APPROVE']} Approve", callback_data=f"approve_{req['request_id']}"),
                InlineKeyboardButton(f"{EMOJI['DECLINE']} Decline", callback_data=f"decline_{req['request_id']}")
            )
            
            if req.get('screenshot'):
                try:
                    bot.send_photo(
                        message.chat.id,
                        req['screenshot'],
                        caption=text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                    continue
                except:
                    pass
            
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        
        if len(pending_requests) > 10:
            bot.send_message(
                message.chat.id,
                f"Showing 10 of {len(pending_requests)} pending requests",
                reply_markup=main_menu()
            )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error loading requests: {str(e)}",
            reply_markup=main_menu()
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith('approve_'))
def approve_request(call):
    try:
        request_id = call.data.split('_')[1]
        requests = load_data(REQUESTS_FILE)
        users = load_data(USERS_FILE)
        
        req = next((r for r in requests if isinstance(r, dict) and r.get('request_id') == request_id and r.get('status') == 'pending'), None)
        
        if not req:
            bot.answer_callback_query(call.id, "Request not found/already processed", show_alert=True)
            return
        
        # Update user balance
        user_id = req['user_id']
        amount = req['amount']
        
        if user_id not in users:
            users[user_id] = {'balance': 0, 'orders': [], 'total_spent': 0}
        
        users[user_id]['balance'] += amount
        
        # Update request status
        req['status'] = 'approved'
        
        # Save changes
        if not (save_data(users, USERS_FILE) and save_data([r for r in requests if not (r.get('request_id') == request_id and r.get('status') == 'approved')], REQUESTS_FILE)):
            raise Exception("Failed to save data")
        
        # Notify user
        try:
            bot.send_message(
                user_id,
                f"🎉 Fund Request Approved!\n\n"
                f"🆔 ID: {request_id}\n"
                f"💵 Amount: {CURRENCY_SYMBOL}{amount:.2f}\n"
                f"💰 New Balance: {CURRENCY_SYMBOL}{users[user_id]['balance']:.2f}"
            )
        except:
            pass
        
        # Update admin message
        try:
            if hasattr(call.message, 'caption'):
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=f"✅ APPROVED\n\n{call.message.caption}",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ APPROVED\n\n{call.message.text}",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
        except:
            pass
        
        bot.answer_callback_query(call.id, f"Approved {CURRENCY_SYMBOL}{amount:.2f}", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

# Enhanced Broadcast Functionality
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['BROADCAST']} Broadcast")
def broadcast_start(message):
    msg = bot.send_message(
        message.chat.id,
        "📢 Enter broadcast message (supports Markdown formatting):",
        reply_markup=cancel_keyboard()
    )
    bot.register_next_step_handler(msg, confirm_broadcast)

def confirm_broadcast(message):
    try:
        if message.text == f"{EMOJI['BACK']} Cancel":
            return main_menu(message)
        
        user_states[message.chat.id] = {'broadcast_message': message.text}
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            KeyboardButton(f"{EMOJI['APPROVE']} Confirm"),
            KeyboardButton(f"{EMOJI['BACK']} Cancel")
        )
        
        bot.send_message(
            message.chat.id,
            f"📢 *Broadcast Preview*\n━━━━━━━━━━━━━━━━\n{message.text}\n━━━━━━━━━━━━━━━━\n\nSend to all users?",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['APPROVE']} Confirm" and m.chat.id in user_states and 'broadcast_message' in user_states[m.chat.id])
def process_broadcast(message):
    try:
        broadcast_msg = user_states[message.chat.id]['broadcast_message']
        users = load_data(USERS_FILE)
        
        bot.send_message(
            message.chat.id,
            f"📢 Sending broadcast to {len(users)} users...",
            reply_markup=ReplyKeyboardRemove()
        )
        
        success = 0
        failed = 0
        
        for user_id in users:
            try:
                bot.send_message(
                    user_id,
                    broadcast_msg,
                    parse_mode="Markdown"
                )
                success += 1
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")
                failed += 1
        
        del user_states[message.chat.id]
        
        bot.send_message(
            message.chat.id,
            f"✅ Broadcast completed!\n\nSuccess: {success}\nFailed: {failed}",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Broadcast failed: {str(e)}",
            reply_markup=main_menu()
        )

# Support Handler
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['SUPPORT']} Support")
def support(message):
    text = """
🆘 *Support Center*
━━━━━━━━━━━━━━━━
✉️ Email: asifmufti922@gmail.com
📱 WhatsApp: https://wa.me/923225815922
📢 Telegram: @hafizhacker
⏰ 24/7 Support
━━━━━━━━━━━━━━━━
"""
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# Handle Back Button
@bot.message_handler(func=lambda m: m.text == f"{EMOJI['BACK']} Back")
def back_to_main(message):
    if message.chat.id in user_states:
        del user_states[message.chat.id]
    bot.send_message(
        message.chat.id,
        "🏠 Main Menu",
        reply_markup=main_menu()
    )

# Run Bot with error handling
if __name__ == "__main__":
    try:
        initialize_data()
        print("🟢 Admin Bot Running...")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        time.sleep(5)
        os.execv(__file__, sys.argv)