# -*- coding: utf-8 -*-
# Copyright (c) 2020, Uniklia and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
import json
import pytz
import midtransclient
import base64
import requests
from frappe import _
from six.moves.urllib.parse import urlencode
from frappe.model.document import Document
from frappe.integrations.utils import create_request_log, make_post_request, create_payment_gateway
from frappe.utils import get_url, call_hook_method, cint, get_datetime


api_path = '/api/method/uniklia.midtrans_payment.doctype.midtranspay_settings.midtranspay_settings'

class MidtransPaySettings(Document):
	supported_currencies = "IDR"

	def validate(self):
		create_payment_gateway('MidtransPay')
		call_hook_method('payment_gateway_enabled', gateway='MidtransPay')

	def on_update(self):
		pass

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_(
				"Please select another payment method. Midtrans does not support transactions in currency '{0}'").format(
				currency))

	def get_midtrans_params_and_url(self):
		params = {
			"client_key": self.client_key,
			"server_key": self.server_key
		}

		if hasattr(self, "use_sandbox") and self.use_sandbox:
			params.update({
				"client_key": frappe.conf.sandbox_client_key,
				"server_key": frappe.conf.sandbox_server_key
			})

		api_url = "https://app.sandbox.midtrans.com/snap/v1" if self.use_sandbox else "https://app.midtrans.com/snap/v1"

		return params, api_url

	def get_payment_url(self, **kwargs):
		setattr(self, "use_sandbox", cint(kwargs.get("use_sandbox", 0)))

		response = self.execute_set_express_checkout(**kwargs)

		self.integration_request = create_request_log(kwargs, "Host", "MidtransPay")

		return response.get('redirect_url')

	def execute_set_express_checkout(self, **kwargs):
		params, url = self.get_midtrans_params_and_url()

		snap = midtransclient.Snap(
			is_production=False,
			server_key=params['server_key']
		)

		order_details = {
			"transaction_details": {
				"order_id": kwargs['order_id'],
				"gross_amount": kwargs['amount']
			}
		}

		response = snap.create_transaction(order_details)

		return response


def get_gateway_controller(doctype, docname):
	reference_doc = frappe.get_doc(doctype, docname)
	gateway_controller = frappe.db.get_value("Payment Gateway", reference_doc.payment_gateway, "gateway_controller")
	return gateway_controller

