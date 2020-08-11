# -*- coding: utf-8 -*-
# Copyright (c) 2020, Uniklia and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
import json
import pytz
import midtransclient
from frappe import _
from six.moves.urllib.parse import urlencode
from frappe.model.document import Document
from frappe.integrations.utils import create_request_log, make_post_request, create_payment_gateway
from frappe.utils import get_url, call_hook_method, cint, get_datetime


api_path = '/api/method/uniklia.midtrans_payment.doctype.midtrans_settings.midtrans_settings'

class MidtransSettings(Document):
	supported_currencies = "IDR"

	def __setup__(self):
		setattr(self, "use_sandbox", 0)

	def setup_sandbox_env(self, token):
		data = json.loads(frappe.db.get_value("Integration Request", token, "data"))
		setattr(self, "use_sandbox", cint(frappe._dict(data).use_sandbox) or 0)

	def validate(self):
		create_payment_gateway("Midtrans")
		call_hook_method('payment_gateway_enabled', gateway="Midtrans")
		if not self.flags.ignore_mandatory:
			self.validate_paypal_credentails()

	def on_update(self):
		pass

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_(
				"Please select another payment method. Midtrans does not support transactions in currency '{0}'").format(
				currency))

	def get_paypal_params_and_url(self):
		params = {
			"client_key": self.client_key,
			"server_key": self.server_key
		}

		if hasattr(self, "use_sandbox") and self.use_sandbox:
			params.update({
				"client_key": frappe.conf.sandbox_client_key,
				"server_key": frappe.conf.sandbox_server_key
			})

		api_url = "https://api-3t.sandbox.paypal.com/nvp" if (
					self.paypal_sandbox or self.use_sandbox) else "https://api-3t.paypal.com/nvp"

		return params, api_url

	def validate_paypal_credentails(self):
		params, url = self.get_paypal_params_and_url()
		params = urlencode(params)

		try:
			res = make_post_request(url=url, data=params.encode("utf-8"))

			if res["ACK"][0] == "Failure":
				raise Exception

		except Exception:
			frappe.throw(_("Invalid payment gateway credentials"))
