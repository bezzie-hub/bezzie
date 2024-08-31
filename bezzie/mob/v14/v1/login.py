# Copyright (c) 2022, D-codE and contributors
# For license information, please see license.txt

import frappe

from bezzie.mob.auth import get_user_profile, user_forgot_password, user_login, user_reset_password, user_send_otp, user_sign_up, user_validate_otp


# login up using email id and password
@frappe.whitelist( allow_guest=True )
def login(username, password):
	user_login(username, password)

# Sigin up using email id and password
@frappe.whitelist(allow_guest=True)
def sign_up(email, full_name,mobile_number,password):
	user_sign_up(email, full_name,mobile_number,password)

#get user profile
@frappe.whitelist()
def get_profile():
	get_user_profile()

@frappe.whitelist(allow_guest=True)
def forgot_password(username,token,password,re_password):
	user_forgot_password(username,token,password,re_password)


@frappe.whitelist(allow_guest=True)
def reset_password(username,old_password,password,re_password):
	user_reset_password(username,old_password,password,re_password)

@frappe.whitelist(allow_guest=True)
def send_otp(username):
	user_send_otp(username)

@frappe.whitelist(allow_guest=True)
def validate_otp(username,otp):
	user_validate_otp(username,otp)

# tesing api 
@frappe.whitelist()
def ping_pong(ping):
    if ping == 'ping':
        frappe.response["test"] = "pong"
    else:
        frappe.response["test"] = "please ping"
    


