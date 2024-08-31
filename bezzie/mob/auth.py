# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import re
import random
import string
import frappe
import base64
from frappe.utils.password import update_password, check_password
from frappe.website.utils import is_signup_disabled
from erpnext.e_commerce.shopping_cart.cart import get_party
from frappe.utils import validate_email_address, validate_name, validate_phone_number


def user_login(username, password):
	try:
		login_manager = frappe.auth.LoginManager()
		login_manager.authenticate(user=username, pwd=password)
		login_manager.post_login()
	except frappe.exceptions.AuthenticationError:
		frappe.clear_messages()
		frappe.local.response["status_code"] =401
		frappe.local.response["message"] ="Invalid username/password"
		return

	api_generate = generate_keys(frappe.session.user)
	user = frappe.get_doc('User', frappe.session.user)
	token = base64.b64encode(('{}:{}'.format(user.api_key, api_generate)).encode('utf-8')).decode('utf-8')
	frappe.local.response["status_code"] =200
	frappe.local.response["data"] ={
			"session":frappe.session.user,
			"auth_key": token,
			"full_name":user.full_name,
			"mobile_no":user.mobile_no,
			"email":user.email,
			"username":username
		}

def generate_keys(user):
	user_details = frappe.get_doc('User', user)
	api_secret = frappe.generate_hash(length=15)
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.flags.ignore_permissions = True
	user_details.flags.ignore_password_policy = True
	user_details.save()
	return api_secret


def user_sign_up(email, full_name,mobile_number,password):
	val={}
	if not validate_email_address(email):
		val.update({"email":"email id is invalid"})

	if not validate_name(full_name):
		val.update({"full_name":"full name is invalid"})

	if not validate_phone_number(mobile_number):
		val.update({"mobile_number":"Mobile Number is invalid"})
	if not validate_password(password):
		val.update({"password":"Should have at least one number, one uppercase and one lowercase character, one special symbol('$', '@', '#', '%') and between 6 to 20 characters long."})
	if val:
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] ="Validation Error"
		frappe.local.response["data"] =val
		return
	auth ={}
	if is_signup_disabled():
		auth.update({"diabled":"Sign Up is disabled"})
	if frappe.db.exists("User",  {"mobile_no": mobile_number}):
		auth.update({"mobile_no":"Mobile Number Already Used"})
	if frappe.db.exists("User",  {"email": email}):
		auth.update({"user_reg":"User Email Already Registered"})	
	if frappe.db.get_creation_count("User", 60) > 300:
		auth.update({"creation_count":"Too many users signed up recently, so the registration is disabled. Please try back in an hour"})
	if auth:
		frappe.local.response["status_code"] =401
		frappe.local.response["message"] ="Invalid user credentils"
		frappe.local.response["data"] =auth
		return
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": full_name,
				"enabled": 1,
				"send_welcome_email":0,
				"new_password": password,
				"mobile_no":mobile_number,
				"user_type": "Website User",
			}
		)
		user.flags.ignore_permissions = True
		user.flags.ignore_password_policy = True
		user.insert()
		
		frappe.response["message"] = "User Signup Success"
		# default role shound be customer
		default_role = frappe.db.get_single_value("Portal Settings", "default_role")
		if default_role:
			user.add_roles(default_role)
		get_party(email)
		user_login(email, password)


def get_user_profile():
	try:
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Success"
		frappe.local.response["data"]=frappe.db.get_value('User', frappe.session.user, ['email', 'full_name','mobile_no'], as_dict=1)
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


def delete_user_profile(username):
	
	try:
		frappe.delete_doc("User", username,ignore_permissions=True)
		# frappe.db.delete("User", {"name": username})
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="User Deleted Successfully"
		frappe.local.response["data"]={}
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

def user_forgot_password(username,token,password,re_password):
	
	try:
		if not frappe.db.exists("User",username):
			frappe.local.response["status_code"] =401
			frappe.local.response["message"] ="Invalid Username"
			frappe.local.response["data"] ={}
			return
		val={}
		fc = frappe.cache()
		token_json = fc.get_value("{0}_token".format(username))
		if not token_json:
			val.update({"token":"Token not found"})
		if token_json:
			if token_json.get("token") != token:
				val.update({"token":"Token not Match"})

			if not token_not_expired(token_json):
				val.update({"token":"Token expired"})

		if not validate_password(password):
			val.update({"password":"Should have at least one number, one uppercase and one lowercase character, one special symbol('$', '@', '#', '%') and between 6 to 20 characters long."})
		
		if password != re_password:
			val.update({"re_password":"password doesn't Match"})
		
		if val:
			frappe.local.response["status_code"] =403
			frappe.local.response["message"] ="Validation Error"
			frappe.local.response["data"] =val
			return
		
		update_password(username,password)
		# Delete consumed otp
		fc.delete_key(username + "_token")
		
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Password Reset Successfully"

	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

def user_reset_password(username,old_password,password,re_password):
	try:
		if not frappe.db.exists("User",username):
			frappe.local.response["status_code"] =401
			frappe.local.response["message"] ="Invalid Username"
			frappe.local.response["data"] ={}
			return
		val={}
		if not validate_password(password):
			val.update({"password":"Should have at least one number, one uppercase and one lowercase character, one special symbol('$', '@', '#', '%') and between 6 to 20 characters long."})
		
		if password != re_password:
			val.update({"re_password":"password doesn't Match"})
		
		if val:
			frappe.local.response["status_code"] =403
			frappe.local.response["message"] ="Validation Error"
			frappe.local.response["data"] =val
			return
		
		check_password(username, old_password)
		update_password(username,password)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="Password Reset Successfully"
	
	except frappe.exceptions.AuthenticationError:
		frappe.clear_messages()
		frappe.local.response["status_code"] =403
		frappe.local.response["message"] ="Validation Error"
		frappe.local.response["data"] ={"old_password":"Current password doesn't Match"}
		return
	
	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"

def user_send_otp(username):
	try:
		if not frappe.db.exists("User",username):
			frappe.local.response["status_code"] =401
			frappe.local.response["message"] ="Invalid Username"
			frappe.local.response["data"] ={}
			return
		key = username + "_otp"	
		otp_length = 6 # 6 digit OTP
		fc = frappe.cache()
		
		if fc.get_value(key) and otp_not_expired(fc.get_value(key)): # check if an otp is already being generated
				otp_json = fc.get_value(key)
		else:
			otp_json = generate_otp(key,otp_length)
			fc.set_value(key, otp_json)
		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="OTP sent Successfully"
		frappe.local.response["data"] =otp_json

	except:
		frappe.local.response["status_code"] =500
		frappe.local.response["message"] ="Something went wrong"


def user_validate_otp(username,otp):

	try:
		val={}
		fc = frappe.cache()
		otp_json = fc.get_value("{0}_otp".format(username))
		if not otp_json:
			val.update({"otp":"OTP not found"})
		if otp_json:
			if otp_json.get("otp") != otp:
				val.update({"otp":"OTP not Match"})

			if not otp_not_expired(otp_json):
				val.update({"otp":"OTP expired"})
		if val:
			frappe.local.response["status_code"] =403
			frappe.local.response["message"] ="Validation Error"
			frappe.local.response["data"] =val
			return
		# Delete consumed otp
		fc.delete_key(username + "_otp")

		key = username + "_token"	
		token_length = 30
		
		if fc.get_value(key) and token_not_expired(fc.get_value(key)):
				token_json = fc.get_value(key)
		else:
			token_json = generate_token(key,token_length)
			fc.set_value(key, token_json)

		frappe.local.response["status_code"] =200
		frappe.local.response["message"] ="OTP Varification Success"
		frappe.local.response["data"] =token_json
	except:
		frappe.local.response["status_code"] =500 
		frappe.local.response["message"] ="Something went wrong"


def generate_otp(key,otp_length):
	otp = ''.join(["{}".format(random.randint(0, 9)) for i in range(0, otp_length)])
	otp = '111111' # SHOULD remove in production
	return {"id": key, "otp": otp, "timestamp": str(frappe.utils.get_datetime().utcnow())}

def otp_not_expired(otp_json):
	flag = True
	diff = frappe.utils.get_datetime().utcnow() - frappe.utils.get_datetime(otp_json.get("timestamp"))
	if int(diff.seconds) / 60 >= 5:
		flag = False

	return flag

def generate_token(key,token_length):
	# token = ''.join(["{}".format(random.randint(0, 9)) for i in range(0, token_length)])
	token = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(0, token_length))
	
	# token = '111111' # SHOULD remove in production
	return {"id": key, "token": token, "timestamp": str(frappe.utils.get_datetime().utcnow())}

def token_not_expired(token_json):
	flag = True
	diff = frappe.utils.get_datetime().utcnow() - frappe.utils.get_datetime(token_json.get("timestamp"))
	if int(diff.seconds) / 60 >= 5:
		flag = False
	return flag

def validate_password(password):
	'''
	Should have at least one number.
	Should have at least one uppercase and one lowercase character.
	Should have at least one special symbol.
	Should be between 6 to 20 characters long.
	'''
	SpecialSym =['$', '@', '#', '%']
	val = True
	if len(password) < 6:
		val = False
	if len(password) > 20:
		val = False
	if not any(char.isdigit() for char in password):
		val = False
	if not any(char.isupper() for char in password):
		val = False
	if not any(char.islower() for char in password):
		val = False
	if not any(char in SpecialSym for char in password):
		val = False
	if val:
		return val