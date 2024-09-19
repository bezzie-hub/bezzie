# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from erpnext.accounts.doctype.payment_request.payment_request import make_payment_request


# make payemnt 
@frappe.whitelist()
def make_payment(sales_order_id):
	try:  
		frappe.local.response["data"] = make_payment_request(dt="Sales Order",dn=sales_order_id)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except TypeError:
		frappe.local.response["status_code"] =204
		frappe.local.response["message"] ="Cart is empty"	
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

