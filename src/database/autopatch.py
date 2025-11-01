import threading
import os
import requests
import time
import json
import base64
import zipfile
import shutil
import subprocess
from src.controller.controller import   insert_ads, delete_ads,\
                                        delete_language_list, delete_language_value,\
                                        insert_language_list, insert_language_value,\
                                        delete_product, insert_product, insert_git, insert_info, delete_info
from src.globals import set_updates_available

import warnings
from urllib3.exceptions import InsecureRequestWarning
from __init__ import __version__

# Disable the warning
warnings.simplefilter('ignore', InsecureRequestWarning)

class DatabaseUpdater:
    def __init__(self, api_server):
        self.api_server = api_server
        self.update_thread = threading.Thread(target=self.check_for_updates)
        self.update_thread.start()
    
    def download_code(self, api_server, params):
        try:
            print("[VM/autopatch]: Source code downloading...")
            response = requests.post(f'{api_server}/client/code', json=params, verify=False)

            if response.status_code != 200:
                print('[VM/autopatch]: Failed to download code file from server')
                return False
            
            code_path = "/tmp/latestapp.zip"
            with open(code_path, 'wb') as f:
                f.write(response.content)
            
            # Extract the zip file to a temporary folder
            extract_path = "/tmp/latestapp"
            with zipfile.ZipFile(code_path, 'r') as zip_ref:
                # Get the folder name inside the zip file
                folder_name = zip_ref.namelist()[0]
                zip_ref.extractall(extract_path)
            
            # Move the files from the extracted folder to the current app base folder
            src = os.path.join(extract_path, folder_name)
            dest = os.getcwd()
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dest, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    if os.path.exists(d):
                        os.remove(d)
                    shutil.copy2(s, d)
            
            # Clean up temporary files
            shutil.rmtree(extract_path)
            os.remove(code_path)

            # Restart Flask app
            subprocess.run(['sudo', 'systemctl', 'restart', 'vendingapp.service'])
   
        except requests.exceptions.RequestException as e:
            print('[VM/autopatch]: Failed to update code:', e)
            return False
    
    def download_ads(self, api_server, params):
        try:
            print("[VM/autopatch]: Ads downloading...")
            response = requests.post(f'{api_server}/client/ads', json=params, verify=False)
            responseData = response.json()
            adsData = responseData['details']
            delete_ads()
            ad_path = "static/video/ads/ad.mp4"
            ad_content=adsData['content']
            with open(ad_path, "wb") as f:
                f.write(base64.b64decode(ad_content))
            insert_ads(adsData['id'], ad_content, adsData['version'])
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            
    def download_language(self, api_server, params):
        try:
            print("[VM/autopatch]: Language downloading...")
            response = requests.post(f'{api_server}/client/language', json=params, verify=False)
            responseData = response.json()
            langData = responseData['details']
                    
            delete_language_list()
            langList = langData['language_list']
            for lang in langList:
                insert_language_list(lang['language_id'], lang['language_name'], lang['language_icon'], lang['version'])
            
            delete_language_value()
            langValueList = langData['language_value_list']
            for langValue in langValueList:
                insert_language_value(langValue['language_key'], langValue['language_value'], langValue['language_type'])

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            
    def download_git(self, api_server, params):
        try:
            print("[VM/autopatch]: Git downloading...")
            response = requests.post(f'{api_server}/client/git', json=params, verify=False)
            responseData = response.json()
            githistory = responseData['details']

            for git in githistory:
                insert_git(git['_id'], git['comment'], git['git'], git['status'], git['updated_at'])
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            
    def download_product(self, api_server, params):
        try:
            print("[VM/autopatch]: Products downloading...")
            response = requests.post(f'{api_server}/client/product', json=params, verify=False)
            responseData = response.json()
            productList = responseData['details']

            delete_product()
            for product in productList:
                insert_product(product['id'], product['product_name'], product['product_name_de'], product['price'], product['currency'], product['description'], product['description_de'], product['category'], product['theme'], product['additional_info1'], product['additional_info2'], product['additional_info3'], product['additional_info4'], product['additional_info5'], product['additional_info1_de'], product['additional_info2_de'], product['additional_info3_de'], product['additional_info4_de'], product['additional_info5_de'], product['thumbnail'], product['subinfoimage1'], product['subinfoimage2'], product['subinfoimage3'], product['stock'], product['box'], product['version'])
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def download_info(self, api_server, params):
        try:
            print("[VM/autopatch]: Info downloading...")
            response = requests.post(f'{api_server}/client/info', json=params, verify=False)
            responseData = response.json()
            infoList = responseData['details']
            
            delete_info()
            for info in infoList:
                insert_info(info['name'], info['value'])
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def check_for_updates(self):
        while True:
            try:
                serialno = os.getenv('SERIALNO')
                params={'serialno': serialno, 'version': __version__}
                response = requests.post(f'{self.api_server}/client/ping', json=params, verify=False)

                if response.status_code == 200:
                    responseData = json.loads(response.text)
                    print("[VM/autopatch]: Checking updates...")
                    # after latest code is downloaded, it should be overwritten to current
                    # code base and restart app
                    if 'code' in responseData['data'] :
                        self.download_code(self.api_server, params)

                    if 'language' in responseData['data'] :
                        self.download_language(self.api_server, params)
                        set_updates_available(True)
                    # if machine setting is changed, then download all parts again except languages
                    # which are not included in machine settings
                    if 'machine' in responseData['data'] :
                        self.download_ads(self.api_server, params)
                        self.download_product(self.api_server, params)
                        self.download_info(self.api_server, params)
                        set_updates_available(True)
                        continue
                    # download only updated parts
                    if 'ads' in responseData['data'] :
                        self.download_ads(self.api_server, params)
                        set_updates_available(True)
                    # if 'git' in responseData['data'] :
                    #     self.download_git(self.api_server, params)
                    #     set_updates_available(True)
                    if 'product' in responseData['data'] :
                        self.download_product(self.api_server, params)
                        set_updates_available(True)
                elif response.status_code == 400:
                    errorData = response.json()
                    print(f"Error: {errorData['error']}")
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
            
            time.sleep(10)
            pass
