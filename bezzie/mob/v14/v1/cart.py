# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import validate_email_address, validate_name, validate_phone_number
from frappe.utils.data import cint

from erpnext.e_commerce.shopping_cart.cart import _get_cart_quotation, get_address_docs, get_party, update_cart
from erpnext.e_commerce.shopping_cart.cart import get_cart_quotation
from erpnext.e_commerce.shopping_cart.cart import apply_coupon_code
from erpnext.e_commerce.shopping_cart.cart import place_order
from erpnext.e_commerce.shopping_cart.cart import update_cart_address ,get_shipping_addresses,get_billing_addresses
from erpnext.e_commerce.shopping_cart.cart import add_new_address
from erpnext.utilities.product import get_web_item_qty_in_stock

from frappe.utils import getdate, today

from frappe.exceptions import DataError, ValidationError

# tesing api 
@frappe.whitelist()
def add_to_cart(item_code,qty,with_items): 
	try:
		item_stock = get_web_item_qty_in_stock(item_code, "website_warehouse")
		if qty > item_stock.stock_qty:
			raise ValidationError
		frappe.response["data"] = update_cart(item_code, qty, with_items)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except ValidationError:
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] =("Only {0} in Stock for item {1}").format(item_stock.stock_qty,item_code)
		frappe.response["data"] = item_stock.update({"in_stock":0,"requested_qty":qty})
	except AttributeError:
		frappe.local.response["status_code"] =204
		frappe.local.response["message"] ="Cart is empty"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

# get cart quotation
@frappe.whitelist()
def get_cart():
    
	try:
		data={}
		cart = get_cart_quotation()
		
		if cart.get("doc").get("name"):
			it = cart.get("doc").get("items")
			items = [x.as_dict() for x in it]
			for item in items:
				item_stock = get_web_item_qty_in_stock(item.item_code, "website_warehouse")
				item.update({
						"in_stock": 1,
						"in_stock_qty": item_stock.stock_qty,
						"is_stock_item": item_stock.is_stock_item,
						"requested_qty": item.qty
					})
				if item.qty > item_stock.stock_qty:
					item.update({
						"in_stock": 0,
						"in_stock_qty": item_stock.stock_qty
					})
			data.update({"cart_id":cart.get("doc").get("name")})
			data.update({"cart":cart.get("doc")})
			data.update({"items":items})
			data.update({"shipping_address":get_cart_address(cart.get("doc").get("shipping_address_name")) if cart.get("doc").get("shipping_address_name") else ''})
			data.update({"billing_address":get_cart_address(cart.get("doc").get("customer_address")) if cart.get("doc").get("customer_address") else ''})
			data.update({"shipping_rules":cart.get("shipping_rules")})
			frappe.response["data"] = data
			frappe.local.response["status_code"] =200
			frappe.local.response["message"] ="Success"
		else:
			frappe.local.response["status_code"] =204
			frappe.local.response["message"] ="Cart is empty"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

    
@frappe.whitelist()
def apply_couponcode(code):
	try:
		validate_coupon_code(code)
		cc= apply_coupon_code(applied_code=code, applied_referral_sales_partner=None)
		frappe.local.response["data"] =cc.get("name")
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except ValidationError:
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] ="Invalid Coupon Code"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

def validate_coupon_code(code):
	coupon_list = frappe.get_all("Coupon Code", filters={"coupon_code": code})
	if not coupon_list:
		raise ValidationError
	coupon_name = coupon_list[0].name
	coupon = frappe.get_doc("Coupon Code", coupon_name)

	if coupon.valid_from:
		if coupon.valid_from > getdate(today()):
			raise ValidationError
	if coupon.valid_upto:
		if coupon.valid_upto < getdate(today()):
			raise ValidationError
	if coupon.used >= coupon.maximum_use:
		raise ValidationError

# shipping addresses 
@frappe.whitelist()
def shipping_addresses_list():
	try:
		party = get_party()
		addresses = get_address_docs(party=party)
		data = [
				{
					"name": address.name,
					"custom_full_name":address.custom_full_name,
					"title": address.address_title,
					"address_title" :address.address_title,
					"address_line1":address.address_line1,
					"address_line2":address.address_line2,
					"city":address.city,
					"state":address.state,
					"country":address.country,
					"address_type":address.address_type,
					"pincode":address.pincode,
					"phone":address.phone
				}
				for address in addresses
				if address.address_type == "Shipping"
			]
		frappe.response["data"] = data
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

# shipping addresses 
@frappe.whitelist()
def billing_addresses_list():
	try:
		party = get_party()
		addresses = get_address_docs(party=party)
		data = [
				{
					"name": address.name, 
					"custom_full_name":address.custom_full_name,
					"title": address.address_title,
					"address_title" :address.address_title,
					"address_line1":address.address_line1,
					"address_line2":address.address_line2,
					"city":address.city,
					"state":address.state,
					"country":address.country,
					"address_type":address.address_type,
					"pincode":address.pincode,
					"phone":address.phone
				}
				for address in addresses
				if address.address_type == "Billing"
			]
		frappe.response["data"] = data
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"



# update_address  of cart  "address_type":"billing" or "shipping"
@frappe.whitelist()
def cart_update_address(address_type, address_name):
	try:
		update_cart_address(address_type, address_name)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except ValidationError:
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] ="Invalid Address"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


# get sales orders list
@frappe.whitelist()
def get_all_country():
	try:
		country = frappe.get_all(
			"Country",
			fields=["name","code"],
			order_by="name",
		)

		# for i in sales_orders:
		# 	so = frappe.get_doc("Sales Order",i.get("name"))
		# 	data.append(so)
		frappe.response["data"] =country
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


# add a new  address
@frappe.whitelist()
def add_address(**kwargs):
	try:
		val={}
		if not kwargs.get("custom_full_name"):
			val.update({"custom_full_name":"Full Name is Mandatory"})
		if not kwargs.get("address_line1"):
			val.update({"address_line1":"Address Line  is Mandatory"})
		if frappe.db.exists("Address", {"address_title": "{0}-{1}".format(kwargs.get("custom_full_name"),kwargs.get("address_line1"))}):
			val.update({"custom_full_name":"Full Name already exists Please change Full Name "})
		if not kwargs.get("city"):
			val.update({"city":"City is Mandatory"})
		if not kwargs.get("country"):
			val.update({"country":"Country is Mandatory"})
		if not kwargs.get("address_type"):
			val.update({"address_type":"Address Type is Mandatory"})
		if not validate_phone_number(kwargs.get("phone")):
			val.update({"phone":"Mobile Number is invalid"})
		if val:
			raise ValidationError
		
		kwargs.update({
			"address_title":"{0}-{1}".format(kwargs.get("custom_full_name"),kwargs.get("address_line1")),
			"is_primary_address":1,
	 		"is_shipping_address":1,
			"custom_full_name":kwargs.get("custom_full_name")
			})
		frappe.response["data"] = add_new_address(doc = kwargs)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except ValidationError:
		frappe.local.response["status_code"] =403
		frappe.local.response["data"] =val
		frappe.local.response["message"] ="Validation Error"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

# update address
@frappe.whitelist()
def update_address(**kwargs):
	try:
		val={}
		if not kwargs.get("address_line1"):
			val.update({"address_line1":"Address Line  is Mandatory"})
		if not kwargs.get("city"):
			val.update({"city":"City is Mandatory"})
		if not kwargs.get("country"):
			val.update({"country":"Country is Mandatory"})
		if not kwargs.get("address_type"):
			val.update({"address_type":"Address Type is Mandatory"})
		if not validate_phone_number(kwargs.get("phone")):
			val.update({"phone":"Mobile Number is invalid"})
		if val:
			raise ValidationError

		kwargs.update({"is_primary_address":1,"is_shipping_address":1})
		address = frappe.get_doc("Address",kwargs.get("name"))
		address.update(kwargs)
		address.save(ignore_permissions=True)

		frappe.response["data"] = address
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except ValidationError:
		frappe.local.response["status_code"] =403
		frappe.local.response["data"] =val
		frappe.local.response["message"] ="Validation Error"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


#delete address
@frappe.whitelist()
def delete_address(name):
	try:
		frappe.delete_doc("Address",name,ignore_permissions=True)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


#get address
@frappe.whitelist()
def get_cart_address(address_name):
		return  frappe.get_doc("Address",address_name)



# place order
@frappe.whitelist()
def place_cart_order():
	try:
		quotation = _get_cart_quotation()
		if not quotation.customer_address:
			raise DataError
		
		for item in quotation.items:
			item_stock = get_web_item_qty_in_stock(item.item_code, "website_warehouse")
			if item.qty > item_stock.stock_qty:
				raise ValidationError
			
		frappe.response["data"] = place_order() 
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except DataError:
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] ="Please select a Billing Address"
	except TypeError:
		frappe.local.response["status_code"] =204
		frappe.local.response["message"] ="Cart is empty"	
	except ValidationError:
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] ="Some Items are Out of Stock. Please Check Your Cart"
		frappe.response["data"] = {}
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
    