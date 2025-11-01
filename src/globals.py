# globals.py

# Define your global variables here
total_money = 0
product_price = 0
product_count = 0
verification_status = 0
current_order = ""
updates_available = False

# Function to set global variables
def set_total_money(var1):
    global total_money
    if var1 != 0:
        total_money += var1

def set_product_price(var1):
    global product_price
    if var1 != 0:
        product_price = var1

def set_product_count(var1):
    global product_count
    if var1 != 0:
        product_count = var1

def get_globals():
    return total_money, product_price, product_count

def reset_globals():
    global total_money, product_count, product_price, verification_status
    total_money = 0
    product_count = 0
    product_price = 0
    verification_status = 0

def set_verification_success():
    global verification_status
    verification_status = 1
    
def set_verification_failed():
    global verification_status
    verification_status = 2
    
def get_verification_status():
    return verification_status

def set_current_order(order_hash):
    global current_order
    current_order = order_hash

def get_current_order():
    return current_order

def set_updates_available(isAvailable):
    global updates_available
    updates_available = isAvailable

def get_updates_avaiable():
    return updates_available
