# -*- coding: utf-8 -*-
# Copyright (c) 2020, Uniklia and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestCourierList(unittest.TestCase):
	def test_courier_list(self):
		courier_list = make_courier_list()


def make_courier_list():
	courier_list = frappe.get_doc({
		"doctype": "Courier List",
		"kurir_id": 1
	})

	courier_list.insert()
	return courier_list


