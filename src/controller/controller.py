# src/database/ads.py
import sqlite3
import os
from src.model.Ads import Ads
from src.model.Product import Product
from src.model.Language import Language
from src.model.LanguageValue import LanguageValue
from src.model.Info import Info
from src.database.dbconnection import get_connection_from_pool, release_connection_to_pool

def insert_ads(ads_id, ads_content, ads_version):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		insert_query = """insert into ads (id, ads, version)
							values (?, ?, ?)"""
		data = (ads_id, ads_content, ads_version)
		cursor.execute(insert_query, data)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('insert_ad_fail', error)
		return False

# delete Ads
def delete_ads():
	
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		delete_query = '''delete from ads'''
		cursor.execute(delete_query)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('delete_ads_fail', error)
		return False
  
# delete Lanugae
def delete_language_list():
	
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		delete_query = '''delete from language_list'''
		cursor.execute(delete_query)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('delete_language_list_fail', error)
		return False

def insert_language_list(id, name, icon, version):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		insert_query = """insert into language_list (language_id, language_name, language_icon, version)
							values (?, ?, ?, ?)"""
		data = (id, name, icon, version)
		cursor.execute(insert_query, data)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('insert_language_list_fail', error)
		return False

# delete Lanugae
def delete_language_value():
	
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		delete_query = '''delete from language_value'''
		cursor.execute(delete_query)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('delete_language_value_fail', error)
		return False
  
def insert_language_value(lang_key, lang_value, lang_type):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		insert_query = """insert into language_value (lang_key, lang_value, lang_type)
							values (?, ?, ?)"""
		data = (lang_key, lang_value, lang_type)
		cursor.execute(insert_query, data)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('insert_language_value_fail', error)
		return False
  
# delete product
def delete_product():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		delete_query = '''delete from product'''
		cursor.execute(delete_query)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('delete_product_fail', error)
		return False

def update_product_stock(product_id, count):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		cursor.execute("SELECT stock FROM product WHERE id=?", (product_id,))
		current_stock = cursor.fetchone()[0]

		new_stock = current_stock - count
		cursor.execute("UPDATE product SET stock=? WHERE id=?", (new_stock, product_id))
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('delete_product_fail', error)
		return False
  
def insert_product(id, product_name, product_name_de, price, currency, description, description_de, category, theme, additional_info1, additional_info2, additional_info3, additional_info4, additional_info5, additional_info1_de, additional_info2_de, additional_info3_de, additional_info4_de, additional_info5_de, thumbnail, subinfoimage1, subinfoimage2, subinfoimage3, stock, box, version):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		insert_query = """insert into product (id, product_name, product_name_de, price, currency, description, description_de, category, theme, additional_info1, additional_info2, additional_info3, additional_info4, additional_info5, additional_info1_de, additional_info2_de, additional_info3_de, additional_info4_de, additional_info5_de, thumbnail, subinfoimage1, subinfoimage2, subinfoimage3, stock, box, version)
							values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
		data = (id, product_name, product_name_de, price, currency, description, description_de, category, theme, additional_info1, additional_info2, additional_info3, additional_info4, additional_info5, additional_info1_de, additional_info2_de, additional_info3_de, additional_info4_de, additional_info5_de, thumbnail, subinfoimage1, subinfoimage2, subinfoimage3, stock, box, version)
		cursor.execute(insert_query, data)

		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('insert_product_fail', error)
		return False

def insert_git(id, comment, git, status, version):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		insert_query = """insert into git (id, comment, git, status, version)
							values (?, ?, ?, ?, ?)"""
		data = (id, comment, git, status, version)
		cursor.execute(insert_query, data)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('insert_git_fail', error)
		return False
  
# get Ad
def get_ads():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		select_query = '''select * from ads'''
		cursor.execute(select_query)
		record = cursor.fetchone()

		ad = None
		if record:
			ad = convert_to_ad(record)

		#conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return ad

	except sqlite3.Error as error:
		print('get_ad_fail', error)
		return None

# get all products
def get_products():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		select_query = '''
			SELECT *
			FROM product
			ORDER BY 
				CASE 
					WHEN category = 'ecig' THEN 1
					WHEN category = 'snack' THEN 2
					WHEN category = 'drink' THEN 3
					ELSE 4
				END ASC
		'''
		cursor.execute(select_query)
		records = cursor.fetchall()

		products = []
		index = 0
		for record in records:
			product = convert_to_product(record, index)
			products.append(product)
			index = index + 1

		#conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return products

	except sqlite3.Error as error:
		print('get_prodcuts_fail', error)
		return []

# get all languages
def get_languages():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		select_query = '''select * from language_list order by version asc'''
		cursor.execute(select_query)
		records = cursor.fetchall()

		languages = []
		for record in records:
			language = convert_to_language(record)
			languages.append(language)

		#conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return languages

	except sqlite3.Error as error:
		print('get_languages_fail', error)
		return []

# get all language values
def get_language_values(lang_type):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		select_query = '''select * from language_value where lang_type = ?'''
		data = (lang_type,)
		cursor.execute(select_query, data)
		records = cursor.fetchall()

		langValues = []
		for record in records:
			value = convert_to_lang_value(record)
			langValues.append(value)

		#conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return langValues

	except sqlite3.Error as error:
		print('get_langs_fail', error)
		return []

# get git history
def get_git():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		select_query = '''select * from git order by info_no asc'''
		cursor.execute(select_query)
		records = cursor.fetchall()

		histories = []
		index = 0
		for record in records:
			history = convert_to_product(record, index)
			histories.append(history)
			index = index + 1

		#conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return histories

	except sqlite3.Error as error:
		print('get_pgit_fail', error)
		return []

def delete_info():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		delete_query = '''delete from info'''
		cursor.execute(delete_query)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('delete_info_fail', error)
		return False
  
def insert_info(info_no, info_comment):
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		insert_query = """insert into info (info_no, info_comment)
							values (?, ?)"""
		data = (info_no, info_comment)
		cursor.execute(insert_query, data)
		
		conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return True

	except sqlite3.Error as error:
		print('insert_info_fail', error)
		return False
  
# get info list
def get_infos():
	try:
		conn = get_connection_from_pool()
		cursor = conn.cursor()

		select_query = '''select * from info'''
		cursor.execute(select_query)
		records = cursor.fetchall()

		infos = []
		for record in records:
			info = convert_to_info(record)
			infos.append(info)

		#conn.commit()
		cursor.close()
		release_connection_to_pool(conn)
		return infos

	except sqlite3.Error as error:
		print('get_info_fail', error)
		return []

def convert_to_ad(record):
	ads = Ads(record[0], record[1], record[2])
	return ads

def convert_to_product(record, index):
	product = Product(index, record[0], record[1], record[2], record[3], record[4], 
				   	record[5], record[6], record[7], record[8], record[9], record[10], 
       				record[11], record[12], record[13], record[14], record[15], record[16], record[17], record[18], record[19], record[20], record[21], record[22], record[23], record[24], record[25])
	return product

def convert_to_lang_value(record):
	language = LanguageValue(record[0], record[1], record[2])
	return language

def convert_to_language(record):
	language = Language(record[0], record[1], record[2], record[3])
	return language

def convert_to_info(record):
	language = Info(record[0], record[1])
	return language