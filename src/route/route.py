# src/route/route.py
import os
from flask import render_template, jsonify
from src.controller.controller import get_products, get_languages, get_language_values, get_infos, update_product_stock
from src.globals import *
from src.api.api import Api
import qrcode
import json
import secrets
import hashlib
import requests
from datetime import timedelta
from flask_jwt_extended import create_access_token
from flask_socketio import emit

api = Api()

def create_qr_code_image(selected_product):
    (amount, price, count) = get_globals()
    serialno = os.getenv('SERIALNO')
    random_number = secrets.token_hex(32)
    hash_object = hashlib.sha256(random_number.encode())
    hashed_value = hash_object.hexdigest()
    
    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Data to be encoded in the QR code
    # Create a dictionary
    data = {
        "serial_no": serialno,
        "product_id": selected_product.product_id,
        "price": price,
        "count": count,
        "hashed_value": hashed_value
    }

    expires = timedelta(minutes=2)

    jwt_token = create_access_token(identity=data, expires_delta=expires)

    # Add data to the QR code
    qr.add_data(jwt_token)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    full_path = os.path.join("static/download/qr", 'my_qrcode.png')
    os.makedirs("static/download/qr", exist_ok=True)

    img.save(full_path)
    return hashed_value

def send_machine_order_request(selected_product):
    (amount, price, count) = get_globals()
    serialno = os.getenv('SERIALNO')
    api_server = os.getenv('WEB_API_SERVER')
    random_number = secrets.token_hex(32)
    hash_object = hashlib.sha256(random_number.encode())
    hashed_value = hash_object.hexdigest()
    
    order_data = {
        "serial_no": serialno,
        "product_id": selected_product.product_id,
        "price": price,
        "count": count,
        "hashed_value": hashed_value
    }

    try:
        response = requests.post(f'{api_server}/client/sell', json=order_data, verify=False)
        if response.status_code == 200:
            responseData = json.loads(response.text)
            print(responseData)
            set_current_order(hashed_value)
            return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def send_purchase_confirm_request():
    serialno = os.getenv('SERIALNO')
    api_server = os.getenv('WEB_API_SERVER')
    current_order = get_current_order()
    
    request_params = {
        "order_hash": current_order,
        "serial_no": serialno,
    }

    try:
        response = requests.post(f'{api_server}/client/confirmpurchase', json=request_params, verify=False)
        if response.status_code == 200:
            responseData = json.loads(response.text)
            print(responseData)
            return True
        elif response.status_code == 400:
            error_response = response.json()
            error_message = error_response.get('error', 'Unknown error')
            print(f"Error from backend: {error_message}")
            return False
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False


def check_machine_license():
    api_server = os.getenv('WEB_API_SERVER')
    serialno = os.getenv('SERIALNO')

    try:
        params={'serialno': serialno}
        response = requests.post(f'{api_server}/client/licensecheck', json=params, verify=False)

        if response.status_code == 200:
            responseData = json.loads(response.text)
            return responseData['isLicensed']
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False


def setup_routes(app, socketio, debug_mode):
    (amount, price, count) = get_globals()
    isLicensed = check_machine_license()

    @app.route('/check_updates')
    def checkupdates():
        updates_available = get_updates_avaiable()
        if updates_available == True:
            set_updates_available(False)
            return jsonify({'updates_available': True})
        return jsonify({'updates_available': False})
    
    @app.route('/check_license')
    def checklicense():
        isLicensed = check_machine_license()
        if isLicensed == True:
            return jsonify({'isLicensed': True})
        return jsonify({'isLicensed': False})

    @app.route('/')
    def adspage():
        return render_template('ads.html')
    
    @app.route('/product/<int:product_id>/<string:language_id>')
    def productpage(product_id, language_id):
        isLicensed = check_machine_license()
        infos = get_infos()
        languages = get_languages()
        products = get_products()
        lang_name = ""
        for lang in languages:
            if lang.language_id == language_id :
                lang_name = lang.language_name

        if language_id == '0':
            language_id = languages[0].language_id
            lang_name = "English"
        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}

        products_length = len(products)
        selected_product = products[product_id % products_length]
        
        products.remove(selected_product)
        products.insert(0, selected_product)
        
        categoryStaringIndexes = []
        index = 0
        for product in products:
            print(product.category)
            if len(categoryStaringIndexes) == 0 and product.category == 'ecig' :
               categoryStaringIndexes.append(index)
            if len(categoryStaringIndexes) == 1 and product.category == 'snack' :
               categoryStaringIndexes.append(index)
            if len(categoryStaringIndexes) == 2 and product.category == 'drink' :
               categoryStaringIndexes.append(index)
            index = index + 1
        
        # in case there are only one typed products, use this value
        categoryStaringIndexes.append(0)
        categoryStaringIndexes.append(0)
        
        return render_template('product.html', deposit_money=amount, infos=infos, product=selected_product, products=products, products_length=products_length, languages=languages, lang_mapping=lang_mapping, language_id=language_id, categoryIndexes=json.dumps(categoryStaringIndexes), lang_name=lang_name, isLicensed=isLicensed)
    
    @app.route('/product_detail/<int:product_id>/<string:language_id>')
    def productdetailpage(product_id, language_id):
        products = get_products()
        infos = get_infos()
        languages = get_languages()
        lang_name = ""
        for lang in languages:
            if lang.language_id == language_id :
                lang_name = lang.language_name

        if language_id == '0':
            language_id = languages[0].language_id
            lang_name = "English"
        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}

        products_length = len(products)
        selected_product = products[product_id % products_length]
                
        return render_template('product_detail.html', deposit_money=amount, infos=infos, product=selected_product, products=products, products_length=products_length, languages=languages, lang_mapping=lang_mapping, language_id=language_id, lang_name=lang_name, isLicensed=isLicensed)

    @app.route('/cart/<int:product_id>/<string:language_id>')
    def cartpage(product_id, language_id):
        products = get_products()
        languages = get_languages()
        lang_name = ""
        for lang in languages:
            if lang.language_id == language_id :
                lang_name = lang.language_name

        if language_id == '0':
            language_id = languages[0].language_id
            lang_name = "English"
        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}

        products_length = len(products)
        selected_product = products[product_id % products_length]
                
        return render_template('cart.html', deposit_money=amount, product=selected_product, lang_mapping=lang_mapping, language_id=language_id, lang_name=lang_name)
    
    @app.route('/payment/<int:product_id>/<string:language_id>/<string:product_price>/<string:product_count>')
    def paymentpage(product_id, language_id, product_price, product_count):
        products = get_products()
        set_product_price(int(product_price))
        set_product_count(int(product_count))
        
        products_length = len(products)
        selected_product = products[product_id % products_length]

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
                
        return render_template('payment.html', deposit_money=amount, product=selected_product, language_id=language_id, lang_mapping=lang_mapping)

    @app.route('/qr/<int:product_id>/<string:language_id>')
    def qrpage(product_id, language_id):
        serialno = os.getenv('SERIALNO')
        products = get_products()
        products_length = len(products)
        selected_product = products[product_id % products_length]
        
        socket_server = os.getenv('SOCKET_SERVER')
        hashed_value = create_qr_code_image(selected_product)
        set_current_order(hashed_value)

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
      
        return render_template('qr.html', socket_server=socket_server, hash_value=hashed_value, serial=serialno, amount=amount, price=price*count, product=selected_product, debug=debug_mode, language_id=language_id, lang_mapping=lang_mapping)
    
    @app.route('/funding/<int:product_id>/<string:language_id>')
    def fundingpage(product_id, language_id):
        (amount, price, count) = get_globals()
        products = get_products()
        products_length = len(products)
        selected_product = products[product_id % products_length]

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}

        # send order request to server
        order_result = send_machine_order_request(selected_product)

        return render_template('funding.html', product=selected_product, amount=amount, price=price*count, debug=debug_mode, language_id=language_id, lang_mapping=lang_mapping, order_result=order_result)
    
    @app.route('/verification/<int:product_id>/<string:language_id>')
    def verificationpage(product_id, language_id):
        products = get_products()   
        products_length = len(products)
        selected_product = products[product_id % products_length]

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
        
        return render_template('verification.html', product=selected_product, debug=debug_mode, language_id=language_id, lang_mapping=lang_mapping)
    
    @app.route('/verification_success/<int:product_id>/<string:language_id>')
    def verificationsuccesspage(product_id, language_id):
        products = get_products()
        products_length = len(products)
        selected_product = products[product_id % products_length]

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
        
        return render_template('verification_success.html', product=selected_product, language_id=language_id, lang_mapping=lang_mapping)
    
    @app.route('/verification_fail/<int:product_id>/<string:language_id>')
    def verificationfailpage(product_id, language_id):
        products = get_products()
        products_length = len(products)
        selected_product = products[product_id % products_length]

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
        
        return render_template('verification_fail.html', product=selected_product, language_id=language_id, lang_mapping=lang_mapping)
    
    @app.route('/purchase_success/<int:product_id>/<string:language_id>')
    def purchasesuccesspage(product_id, language_id):
        (amount, price, count) = get_globals()
        products = get_products()
        languages = get_languages()
        reset_globals()
        products_length = len(products)
        selected_product = products[product_id % products_length]
        total_amount = price * count

        db_updated = update_product_stock(selected_product.product_id, count)
        server_confirmed = send_purchase_confirm_request()

        if db_updated == False:
            print("[VM/route] Failed to update db")
        
        if server_confirmed == False:
            print("[VM/route] Failed to confirm purchase in server")

        lang_name = ""
        for lang in languages:
            if lang.language_id == language_id :
                lang_name = lang.language_name

        if language_id == '0':
            language_id = languages[0].language_id
            lang_name = "English"
        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
        
        return render_template('purchase_success.html', product=selected_product, language_id=language_id, lang_mapping=lang_mapping, lang_name=lang_name, amount=total_amount, count=count)
    
    @app.route('/purchase_fail/<int:product_id>/<string:language_id>')
    def purchasefailpage(product_id, language_id):
        products = get_products()
        products_length = len(products)
        selected_product = products[product_id % products_length]

        language_values = get_language_values(language_id)
        lang_mapping = {language_value.lang_key: language_value.lang_value for language_value in language_values}
        
        return render_template('purchase_fail.html', product=selected_product, language_id=language_id, lang_mapping=lang_mapping)

    @socketio.on('connect')
    def api_connect():
        emit('connect')

    @socketio.on('api_call')
    def api_controller(message):
        print(message)
        if message['method'] == 'motor_working':
            api.item_out(message['box'])
        elif message['method'] == 'can_continue':
            response = api.can_continue()
            emit('res_can_continue', json.dumps(response))
        elif message['method'] == 'reset_amount':
            api.reset_amount()
        elif message['method'] == 'start_verification_client':
            api.start_verification_client()
            emit('res_start_verification_client')
        elif message['method'] == 'verification_status':
            response = api.verification_status()
            emit('res_verification_status', json.dumps(response))
