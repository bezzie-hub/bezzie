# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from erpnext.e_commerce.shopping_cart.cart import get_party
from bezzie.mob.v14.v1.cart import get_cart_address


# get sales orders list
@frappe.whitelist()
def get_sales_orders():
	try:
		data =[]
		party = get_party()
		sales_orders = frappe.get_all(
			"Sales Order",
			fields=["name","customer"],
			filters={
				"customer": party.name,
				"contact_email": frappe.session.user,
				"order_type": "Shopping Cart",
				"docstatus": 1,
			},
			order_by="modified desc",
		)

		for i in sales_orders:
			so = frappe.get_doc("Sales Order",i.get("name"))
			data.append(so)
		frappe.response["data"] =data
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

# get sales order
@frappe.whitelist()
def get_sales_order(sales_order):
	try:
		data={}
		order = frappe.get_doc("Sales Order", sales_order)
		if order.get("name"):
			data.update({"order":order})
			data.update({"shipping_address":get_cart_address(order.get("shipping_address_name"))})
			data.update({"billing_address":get_cart_address(order.get("customer_address"))})
		frappe.response["data"] =data
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"]=500
		frappe.local.response["message"] ="Something went wrong"

# tesing api 
@frappe.whitelist(allow_guest=True)
def ping_pong(ping):
    if ping == 'ping':
        frappe.response["test"] = "pong"
    else:
        frappe.response["test"] = "please ping"