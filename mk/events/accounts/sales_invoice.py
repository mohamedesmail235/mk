# -*- coding: utf-8 -*-
import frappe
from erpnext import get_region
from pyqrcode import create as qr_create
import io
import os
from base64 import b64encode
from frappe import _
from frappe.utils.data import add_to_date, get_time, getdate

def create_qr_code(doc, method):
	"""Create QR Code after inserting Sales Inv
	"""

	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return
	# if QR Code field not present, do nothing
	if not hasattr(doc, 'qr_code'):
		return

	# Don't create QR Code if it already exists
	qr_code = doc.get("qr_code")
	# if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
	# 	return

	meta = frappe.get_meta('Sales Invoice')

	for field in meta.fields:
		if field.fieldname == 'qr_code':
			from urllib.parse import urlencode
			''' TLV conversion for
			1. Seller's Name
			2. VAT Number
			3. Time Stamp
			4. Invoice Amount
			5. VAT Amount
			'''
			tlv_array = []
			# Sellers Name

			'''TODO: Fix arabic conversion'''
			# seller_name = frappe.db.get_value(
			# 	'Company',
			# 	doc.company,
			# 	'company_name_in_arabic')

			# if not seller_name:
			# 	frappe.throw(_('Arabic name missing for {} in the company document'.format(doc.company)))

			seller_name = doc.company
			tag = bytes([1]).hex()
			length = bytes([len(seller_name)]).hex()
			value = seller_name.encode('utf-8').hex()

			tlv_array.append(''.join([tag, length, value]))

			# VAT Number
			tax_id = frappe.db.get_value('Company', doc.company, 'tax_id')
			if not tax_id:
				frappe.throw(_('Tax ID missing for {} in the company document'.format(doc.company)))

			# tax_id = '310122393500003'  #
			tag = bytes([2]).hex()
			length = bytes([len(tax_id)]).hex()
			value = tax_id.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# Time Stamp
			posting_date = getdate(doc.posting_date)
			time = get_time(doc.posting_time)
			seconds = time.hour * 60 * 60 + time.minute * 60 + time.second
			time_stamp = add_to_date(posting_date, seconds=seconds)
			time_stamp = time_stamp.strftime('%Y-%m-%dT%H:%M:%SZ')

			# time_stamp = '2022-04-25T15:30:00Z'  #
			tag = bytes([3]).hex()
			length = bytes([len(time_stamp)]).hex()
			value = time_stamp.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))
			invoice_amount = str(doc.grand_total)
			if hasattr(doc,"custom_grantee_value"):
				# Invoice Amount
				invoice_amount = str(((doc.net_total)+(doc.total_taxes_and_charges - (doc.total_advance*0.15)))  - (doc.total_advance+doc.custom_grantee_value))

			# invoice_amount = '1000.00'  #
			tag = bytes([4]).hex()
			length = bytes([len(invoice_amount)]).hex()
			value = invoice_amount.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# VAT Amount
			vat_amount = str((doc.total_taxes_and_charges - (doc.total_advance*0.15) ))

			# vat_amount = '150.00'  #
			tag = bytes([5]).hex()
			length = bytes([len(vat_amount)]).hex()
			value = vat_amount.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# Joining bytes into one
			tlv_buff = ''.join(tlv_array)

			# base64 conversion for QR Code
			base64_string = b64encode(bytes.fromhex(tlv_buff)).decode()
			# Creating public url to print format
			default_print_format = frappe.db.get_value('Property Setter',
													   dict(property='default_print_format', doc_type=doc.doctype),
													   "value")

			# System Language
			language = frappe.get_system_settings('language')

			params = urlencode({
				'format': default_print_format or 'Standard',
				'_lang': language,
				'key': doc.get_signature()
			})

			# creating qr code for the url
			url = f"{frappe.utils.get_url()}/{doc.doctype}/{doc.name}?{params}"
			qr_image = io.BytesIO()
			url = qr_create(url, error='L')
			url = qr_create(base64_string, error='L')
			url.png(qr_image, scale=2, quiet_zone=1)
			import random
			rand_no = random.randint(1, 10)
			# making file
			filename = f"QR-CODE-{doc.name}-{rand_no}.png".replace(os.path.sep, "__")
			_file = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"is_private": 0,
				"content": qr_image.getvalue(),
				"attached_to_doctype": doc.get("doctype"),
				"attached_to_name": doc.get("name"),
				"attached_to_field": "qr_code"
			})

			delete_qr_code_file(doc,None)
			_file.save()
			frappe.db.commit()
			# assigning to document
			doc.db_set('qr_code', _file.file_url)
			doc.db_set('ksa_einv_qr', _file.file_url)
			doc.notify_update()
			break




			"""qr_image = io.BytesIO()

			xml = qr_create(xml,error='L',mode='binary', encoding='utf-8',)
			xml.png(qr_image, scale=2, quiet_zone=1)

			# making file
			filename = f"QR-CODE-{doc.name}.png".replace(os.path.sep, "__")
			_file = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"content": qr_image.getvalue(),
				"is_private": 1
			})

			_file.save()

			# assigning to document
			doc.db_set('qr_code', _file.file_url)
			doc.notify_update()

			break"""

def delete_qr_code_file(doc, method):
	"""Delete QR Code on deleted sales invoice"""

	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return

	if hasattr(doc, 'qr_code'):
		if doc.get('qr_code'):
			file_doc = frappe.get_list('File', {
				# 'file_url': doc.qr_code,
				'attached_to_doctype': doc.doctype,
				'attached_to_name': doc.name
			})
			if len(file_doc):
				for file in file_doc:
					frappe.delete_doc('File', file.name)
					frappe.db.commit()

def update_is_return_reason(doc, method):
	if not doc.get('is_return_reason'):
		return
	if doc.is_return==1:
		doc.is_return_reason="مرتجع"
