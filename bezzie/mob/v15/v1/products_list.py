# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt


import frappe

from webshop.webshop.api import get_product_filter_data
from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.shopping_cart.product_info import get_product_info_for_website
from webshop.webshop.doctype.item_review.item_review import add_item_review, get_item_reviews, get_customer
from webshop.webshop.variant_selector.utils import get_attributes_and_values, get_next_attribute_and_values



def query_builder(field_filters=None,attribute_filters=None,start=None,item_group=None,search=""):
	
	return {
            "field_filters": field_filters if field_filters else {},
			"attribute_filters": attribute_filters if attribute_filters else {},
			"start": start,
			"item_group":item_group,
			"search":search   
			}

def tune_data(data,start):
	if data:
		frappe.response["data"] = data.get("items")
		# frappe.response["settings"] = data.get("settings")
		frappe.response["filter_fields"] = data.get("filter_fields")
		frappe.response["items_count"] = data.get("items_count")
		# frappe.response["products_per_page"] = data.get("settings").get("products_per_page")
		frappe.response["start_from"] = start
	
# Get All The Products listed as website item without any filters
@frappe.whitelist(allow_guest=True)
def get_all_products(field_filters=None,attribute_filters=None,start=None,item_group=None):
	try:

		query_args=query_builder(field_filters,attribute_filters,start,item_group)
		data = get_product_filter_data(query_args)
		tune_data(data,start)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"
	# ''' will see later (OPTIONAL)
	# 	this is used for fetching the ecommerce 
	# 	artibute and field filters for all product list page  
	
	# '''
	# filter_obj = ProductFiltersBuilder()
	# frappe.response["field_filters"] = filter_obj.get_field_filters()
	# frappe.response["attribute_filters"] = filter_obj.get_attribute_filters()


# Get Products listed as website item with filters
@frappe.whitelist(allow_guest=True)
def get_products_with_filters(field_filters=None,attribute_filters=None,start=None,item_group=None,search=None):
	try:
		query_args=query_builder(field_filters,attribute_filters,start,item_group,search)
		data = get_product_filter_data(query_args)
		tune_data(data,start)

		''' will see later (OPTIONAL)
			this is used for fetching the ecommerce 
			artibute and field filters for all product list page  
		
		'''
		filter_obj = ProductFiltersBuilder(item_group)
		frappe.response["field_filters"] = filter_obj.get_field_filters()
		frappe.response["attribute_filters"] = filter_obj.get_attribute_filters()
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"
	


# Get Products listed as category(mainly using Item Code)
@frappe.whitelist(allow_guest=True)
def get_products_with_category(field_filters=None,attribute_filters=None,start=None,item_group=None):
	
	try:
		query_args=query_builder(start=start,item_group=item_group)
		data = get_product_filter_data(query_args)
		tune_data(data,start)

		''' will see later (OPTIONAL)
			this is used for fetching the ecommerce 
			artibute and field filters for all product list page  
		
		'''
		filter_obj = ProductFiltersBuilder(item_group)
		frappe.response["field_filters"] = filter_obj.get_field_filters()
		frappe.response["attribute_filters"] = filter_obj.get_attribute_filters()
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"
	
# Get Products listed as category
@frappe.whitelist(allow_guest=True)
def get_category_tabs():
	try:
		item_group = frappe.qb.DocType("Item Group")
		ig = (frappe.qb.from_(item_group).select(item_group.name,item_group.image,item_group.is_group).where(item_group.is_group==1).run(
			as_dict=True))

		for i in ig:
			child = frappe.get_all(
					"Item Group",
					fields=["name","image"],
					filters={
						"parent_item_group": i.get("name"),
					},
				) 
			i.update({"childs":child})
			
		frappe.local.response["data"]= ig
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"
	
@frappe.whitelist(allow_guest=True)
def get_all_category():

	try:

		settings = frappe.get_cached_doc("Webshop Settings")
		categories_enabled = settings.enable_field_filters

		if categories_enabled:
			categories = [row.fieldname for row in settings.filter_fields]
			tabs = get_category_records(categories)

		frappe.local.response["data"]= tabs
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"
	

def get_category_records(categories: list):
	categorical_data = {}
	website_item_meta = frappe.get_meta("Website Item", cached=True)

	for c in categories:
		if c == "item_group":
			categorical_data["item_group"] = frappe.db.get_all(
				"Item Group",
				filters={"parent_item_group": "All Item Groups", "show_in_website": 1},
				fields=["name", "parent_item_group", "is_group", "image", "route"],
			)

			continue

		field_type = website_item_meta.get_field(c).fieldtype

		if field_type == "Table MultiSelect":
			child_doc = website_item_meta.get_field(c).options
			for field in frappe.get_meta(child_doc, cached=True).fields:
				if field.fieldtype == "Link" and field.reqd:
					doctype = field.options
		else:
			doctype = website_item_meta.get_field(c).options

		fields = ["name"]

		try:
			meta = frappe.get_meta(doctype, cached=True)
			if meta.get_field("image"):
				fields += ["image"]

			data = frappe.db.get_all(doctype, fields=fields)
			categorical_data[c] = data
		except BaseException:
			frappe.throw(_("DocType {} not found").format(doctype))
			continue
	# print(categorical_data)
	return categorical_data


@frappe.whitelist(allow_guest=True)
def search_products(start,search):
	# return search(query)
	try:
		query_args=query_builder(start=start,search=search)
		data = get_products(query_args)
		tune_data(data,start)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


# a universal product list api
def get_products(query_args):
	return get_product_filter_data(query_args)




# tesing api 
@frappe.whitelist(allow_guest=True)
def ping_pong(ping):
    if ping == 'ping':
        frappe.response["test"] = "pong"
    else:
        frappe.response["test"] = "please ping"


########################################################################



# list product with group search and using other filterss
@frappe.whitelist(allow_guest=True)
def get_product_listing(search,field_filters,attribute_filters,item_group,start,from_filters,page_length):

	query_args={
		"search":search,
		"field_filters":field_filters ,
		"attribute_filters": attribute_filters,
		"item_group": item_group,
		"start": start,
		"from_filters": from_filters,
		"page_length":page_length
	     }
	result = get_product_filter_data(query_args)
	# return result
	frappe.response["items"] = result.get("items")
	frappe.response["sub_categories"] = result.get("sub_categories")
	frappe.response["start"] = start
	frappe.response["page_length"] = page_length
	frappe.response["items_count"] = result.get("items_count")

# Product listing based on filters
@frappe.whitelist(allow_guest=True)
def product_listing(**kwargs):

	kwargs = frappe._dict(kwargs)

	search = "",
	field_filters = {},
	attribute_filters = {},
	item_group = None,
	start = 0,
	from_filters = False,
	page_length = 1

	# if kwargs.search:
	# 	search = kwargs.search

	# if kwargs.field_filters:
	# 	field_filters = kwargs.field_filters

	# if kwargs.attribute_filters:
	# 	attribute_filters = kwargs.attribute_filters
		
	# if kwargs.item_group:
	# 	item_group = kwargs.item_group

	# if kwargs.start:
	# 	start = kwargs.start

	# if kwargs.from_filters:
	# 	from_filters = kwargs.from_filters

	# if kwargs.page_length:
	# 	page_length = kwargs.page_length

	return frappe._dict( {
		"search":search,
		"field_filters":field_filters ,
		"attribute_filters": attribute_filters,
		"item_group": item_group,
		"start": start,
		"from_filters": from_filters,
		"page_length":page_length
	})

	return get_product_filter_data(query_args)


# view product
@frappe.whitelist(allow_guest=True)
def get_product_info(item_code):
    return get_product_info_for_website(item_code)

@frappe.whitelist(allow_guest=True)
def get_product_review(web_item):
    return get_item_reviews(web_item) 


@frappe.whitelist()
def add_product_review(web_item,title,rating,comment):
    return add_item_review(web_item,title,rating,comment)

@frappe.whitelist(allow_guest=True)
def get_attributes_and_value(item_code):
    return get_attributes_and_values(item_code)


@frappe.whitelist(allow_guest=True)
def get_next_attribute_and_value(item_code,selected_attributes):
    return get_next_attribute_and_values(item_code,selected_attributes)



@frappe.whitelist(allow_guest=True)
def get_slideshow(slideshow):
	if not slideshow:
		return {}

	slideshow = frappe.get_doc("Website Slideshow", slideshow)
	slides = slideshow.get({"doctype": "Website Slideshow Item"})
	values={}
	for index, slide in enumerate(slides):
		values[f"slide_{index + 1}_image"] = slide.image
		values[f"slide_{index + 1}_title"] = slide.heading
	return {
		"slides":values,
		"slideshow_header": slideshow.header or "",
	}

@frappe.whitelist(allow_guest=True)
def get_item_code_from_web_item(web_item):
	if frappe.db.get_value("Website Item", web_item, "item_code"):
		return frappe.db.get_value("Website Item", web_item, "item_code")