# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe

from webshop.webshop.shopping_cart.product_info import get_product_info_for_website
from webshop.webshop.doctype.item_review.item_review import add_item_review, get_item_reviews, get_customer
from webshop.webshop.variant_selector.utils import get_attributes_and_values, get_next_attribute_and_values

# from frappe.website.doctype.website_slideshow.website_slideshow import get_slideshow




# get product details
@frappe.whitelist(allow_guest=True)
def get_product_details(item_code):
	try:
		data={}
		web_item_name, item_group,brand,description = frappe.db.get_value("Website Item", 
											   {"item_code":item_code},
											   ["web_item_name", "item_group","brand","description"])
		pinf=get_product_info_for_website(item_code).get("product_info")
		pinf.update({
				"item_code":item_code,
				"item_name":web_item_name,
				"item_group":item_group,
				"brand":brand,
				"description":description,
			})
		data.update({"product_info":pinf})
		data.update({"slideshow":get_slideshow(item_code).get("slides")})
		data.update({"attributes":get_attributes_and_values(item_code)})
		frappe.response["data"]=data
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except Exception as e:
		frappe.local.response["status_code"] =e
		frappe.local.response["message"] ="Something went wrong"

# get product reviews
@frappe.whitelist(allow_guest=True)  
def get_reviews(item_code,start,end):
	try:
		if frappe.db.get_value("Website Item", {"item_code": item_code}):
			web_item = frappe.db.get_value("Website Item", {"item_code": item_code})
		frappe.response["data"]= get_item_reviews(web_item, start=start, end=end, data=None)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

# add a product review
@frappe.whitelist() 
def add_review(item_code,title, rating, comment=None):
	try:
		if frappe.db.get_value("Website Item", {"item_code": item_code}):
			web_item = frappe.db.get_value("Website Item", {"item_code": item_code})
		add_item_review(web_item, title, rating, comment)
		frappe.response["data"]= "Review Added Successfully"
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
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


def get_slideshow(item_code):
	if not frappe.db.get_value("Website Item", {"item_code": item_code},"slideshow"):
		img = frappe.db.get_value("Website Item", {"item_code": item_code},["website_image"])
		return {"slides":[{"image":img}]}
	slideshow = frappe.db.get_value("Website Item", {"item_code": item_code},"slideshow")
    
	slideshow = frappe.get_doc("Website Slideshow",slideshow)
	img = frappe.db.get_value("Website Item", {"item_code": item_code},["website_image"])
	slides = slideshow.get({"doctype": "Website Slideshow Item"}),
	slides[0].insert(0,{"image":img})
	return {
		"slides": slides[0],
		# "slideshow_header": slideshow.header or "",
	}
