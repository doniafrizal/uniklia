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


api_path = '/api/method/uniklia.midtrans_payment.doctype.midtrans_settings.midtrans_settings'

class MidtransSettings(Document):
	supported_currencies = "IDR"

	def validate(self):
		create_payment_gateway('Midtrans')
		call_hook_method('payment_gateway_enabled', gateway='Midtrans')

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

		if self.use_sandbox:
			return_url = "https://app.sandbox.midtrans.com/snap/v2/vtweb/{0}"
		else:
			return_url = "https://app.midtrans.com/snap/v2/vtweb/{0}"

		kwargs.update({
			"token": response.get("token"),
			"redirect_url": response.get("redirect_url")
		})
		self.integration_request = create_request_log(kwargs, "Remote", "Midtrans", response.get("token"))

		return return_url.format(kwargs["token"])

	def execute_set_express_checkout(self, **kwargs):
		params, url = self.get_midtrans_params_and_url()

		snap = midtransclient.Snap(
			is_production=self.use_sanbox,
			server_key=params['server_key']
		)

		order_details = {
			"transaction_details": {
				"order_id": kwargs['order_id'],
				"gross_amount": kwargs['amount']
			}
		}

		response = snap.create_transaction(order_details)

		if response.get("status_code") != 200:
			frappe.throw(_("Looks like something is wrong with this site's Midtrans configuration."))

		return response
