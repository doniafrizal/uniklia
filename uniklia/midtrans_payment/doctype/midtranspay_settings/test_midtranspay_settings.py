# -*- coding: utf-8 -*-
# Copyright (c) 2020, Uniklia and Contributors
# See license.txt

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
import unittest

payment_request = {
	"amount": 20000,
	"title": "Uniklia",
	"description": "Uniklia",
	"reference_doctype": "Payment Request",
	"reference_docname": "self.name",
	"payer_email": "doni@gmail.com",
	"payer_name": "Doni Afrizal",
	"order_id": "12345",
	"currency": "IDR"
}


class TestMidtransPaySettings(unittest.TestCase):
	def test_midtranspay_seeting(self):
		midtranspay_settings = make_midtranspay_settings()
		params, url = get_midtrans_params_and_url(midtranspay_settings)
		print(url)
		self.assertEquals(params['client_key'], 'SB-Mid-client-e4WY660O9Qo9w2sC')

		response = get_payment_url(midtranspay_settings, payment_request)
		print(response)


def make_midtranspay_settings():
	midtranspay_settings = frappe.get_doc({
		"doctype": "MidtransPay Settings",
		"merchant_id": "G942175325",
		"client_key": "Mid-client-EPvkHkw-wNz87GAz",
		"server_key": "Mid-server-MsPYMzqNUDDmMMVcjzRq72LW",
		"use_sandbox": True,
		"sandbox_client_key": "SB-Mid-client-e4WY660O9Qo9w2sC",
		"sandbox_server_key": "SB-Mid-server-2VHTaXRiX_K8KFLUhuUMxIEJ"
	})

	midtranspay_settings.insert()
	return midtranspay_settings


def get_midtrans_params_and_url(midtranspay_settings):
	params = {
		"client_key": midtranspay_settings.client_key,
		"server_key": midtranspay_settings.server_key
	}
	if midtranspay_settings.use_sandbox:
		params.update({
			"client_key": midtranspay_settings.sandbox_client_key,
			"server_key": midtranspay_settings.sandbox_server_key
		})

	api_url = "https://app.sandbox.midtrans.com/snap/v1" if midtranspay_settings.use_sandbox else "https://app.midtrans.com/snap/v1"

	return params, api_url


def get_payment_url(midtrans, payment_request):
	# setattr(self, "use_sandbox", cint(kwargs.get("use_sandbox", 0)))
	response = execute_set_express_checkout(midtrans, payment_request)

	# integration_request = create_request_log(payment_request, "Host", "MidtransPay")
	return response.get('redirect_url')


def execute_set_express_checkout(midtrans, payment_request):
	params, url = get_midtrans_params_and_url(midtrans)
	print(params)
	snap = midtransclient.Snap(
		is_production=False,
		server_key=params['server_key']
	)
	# print(snap.server_key)
	order_details = {
		"transaction_details": {
			"order_id": payment_request['order_id'],
			"gross_amount": payment_request['amount']
		}
	}
	# print(order_details)
	response = snap.create_transaction(order_details)

	return response
