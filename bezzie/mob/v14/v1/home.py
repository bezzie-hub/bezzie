# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe

from bezzie.mob.v14.v1.products_list import (get_products,
                                            query_builder)
# get home page
@frappe.whitelist(allow_guest=True)
def home_page():
	try:
		data={}
		fp = frappe.get_all("Featured Products",fields=["item"])
		fp = [row.item for row in fp]
		pp = frappe.get_all("Popular Products",fields=["item"])
		pp = [row.item for row in pp]
		query_args = query_builder(start=0)
		data.update({"whats_new":get_products(query_args).get("items")})
		query_args = query_builder(field_filters ={"item_code":fp})
		data.update({"featured":get_products(query_args).get("items")})
		query_args = query_builder(field_filters ={"item_code":pp})
		data.update({"popular":get_products(query_args).get("items")})          
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
		frappe.local.response["data"] =data
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

    # frappe.response["category"] = get_products_with_category(start=0,item_group=tc)

# get E Commerce Settings
@frappe.whitelist(allow_guest=True)
def get_settings():   
	try:
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
		frappe.local.response["data"] = frappe.get_cached_doc("E Commerce Settings")
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"
    
# tesing api 
@frappe.whitelist(allow_guest=True)
def ping_pong(ping):
    if ping == 'ping':
        frappe.response["test"] = "pong"
    else:
        frappe.response["test"] = "please ping"
    

