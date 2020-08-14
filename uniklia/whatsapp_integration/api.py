# -*- coding: utf-8 -*-
# Copyright (c) 2017, Diamo and contributors
# For license information, please see license.txt
from __future__ import unicode_literals

import frappe
from frappe import _
from twilio.rest import Client
import messagebird
from six import string_types
import frappe
from frappe import _
from frappe.utils.print_format import download_pdf
from frappe.core.doctype.sms_settings.sms_settings import validate_receiver_nos


@frappe.whitelist(allow_guest=True)
def get_pdf_for_whatsapp(doctype, name, key):
    doc = frappe.get_doc(doctype, name)
    if not key == doc.get_signature():
        return 403
    download_pdf(doctype, name, format=None, doc=None, no_letterhead=0)


def get_url_for_whatsapp(doctype, name):
    doc = frappe.get_doc(doctype, name)
    return "{url}/api/method/uniklia/whatsapp_integration.api.get_pdf_for_whatsapp?doctype={doctype}&name={name}&key={key}".format(
        url=frappe.utils.get_url(),
        doctype=doctype,
        name=name,
        key=doc.get_signature()
    ).replace(" ", "%20")


@frappe.whitelist()
def send_whatsapp(receiver_list, msg, doctype="", name=""):
    import json
    if isinstance(receiver_list, string_types) and doctype != "SMS Center":
        receiver_list = json.loads(receiver_list)
        if not isinstance(receiver_list, list):
            receiver_list = [receiver_list]
    elif doctype == "SMS Center":
        sms = frappe.get_doc("SMS Center")
        sms.receiver_list = receiver_list
        receiver_list = sms.get_receiver_nos()

    receiver_list = validate_receiver_nos(receiver_list)

    wp_settings = frappe.get_doc("Whatsapp Settings")
    client = messengerbird.Client(wp_settings.test_key) if wp_settings.use_test_key else messengerbird.Client(wp_settings.live_key)
    errors = []

    message_kwargs = {
        "from_": 'whatsapp:{}'.format(wp_settings.your_whatsapp_number),
        'channelId': wp_settings.channel_id,
        'type': 'text',
        'content': {
            'text': msg
        }
    }

    attachment_kwargs = {}
    if doctype and doctype != "SMS Center":
        attachment_kwargs = {
            "from_": 'whatsapp:{}'.format(wp_settings.your_whatsapp_number),
            "media_url": get_url_for_whatsapp(doctype, name),
            "body": "{name}.pdf".format(name=name)
        }

    for rec in receiver_list:
        if attachment_kwargs:
            attachment_kwargs.update({"to": 'whatsapp:{}'.format(rec)})
            resp = _send_whatsapp(attachment_kwargs, client)
            if not resp:
                errors.append(rec)
                continue

        if not msg:
            continue

        message_kwargs.update({"to": 'whatsapp:{}'.format(rec)})
        resp = _send_whatsapp(message_kwargs, client)
        if not resp:
            errors.append(rec)

    if errors:
        frappe.msgprint(_("The message wasn't correctly delivered to: {}".format(", ".join(errors))))

    return "The message was correctly delivered"


def _send_whatsapp(message_dict, client):
    response = client.conversation_create_message(**message_dict)
    return response.id
