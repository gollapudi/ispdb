# -*- coding: utf-8 -*-

import os
from lxml import etree

from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import assert_equal

from ispdb.config import models


# Utility Functions.

def make_config(value):
    "Get the dictionary for a sample config."
    return {
            "asking_or_adding": "adding",
            "domain-TOTAL_FORMS": "1",
            "domain-INITIAL_FORMS": "0",
            "domain-0-id": "",
            "domain-0-name": "test%s.com" % value,
            "domain-0-DELETE": "False",
            "display_name": "test%s" % value,
            "display_short_name": "test%s" % value,
            "incoming_type": "imap",
            "incoming_hostname": "foo",
            "incoming_port": "22%s" % value,
            "incoming_socket_type": "plain",
            "incoming_authentication": "password-cleartext",
            "incoming_username_form": "%EMAILLOCALPART%",
            "outgoing_hostname": "bar",
            "outgoing_port": "22%s" % value,
            "outgoing_socket_type": "STARTTLS",
            "outgoing_username_form": "%EMAILLOCALPART%",
            "outgoing_authentication": "password-cleartext",
            "docurl-INITIAL_FORMS": "0",
            "docurl-TOTAL_FORMS": "1",
            "docurl-MAX_NUM_FORMS": "",
            "docurl-0-id": "",
            "docurl-0-DELETE": "False",
            "docurl-0-url": "http://test%s.com/" % value,
            "desc_0-INITIAL_FORMS": "0",
            "desc_0-TOTAL_FORMS": "1",
            "desc_0-MAX_NUM_FORMS": "",
            "desc_0-0-id": "",
            "desc_0-0-DELETE": "False",
            "desc_0-0-language": "en",
            "desc_0-0-description": "test%s" % value,
            "enableurl-INITIAL_FORMS": "0",
            "enableurl-TOTAL_FORMS": "1",
            "enableurl-MAX_NUM_FORMS": "",
            "enableurl-0-id": "",
            "enableurl-0-DELETE": "False",
            "enableurl-0-url": "http://test%s.com/" % value,
            "inst_0-INITIAL_FORMS": "0",
            "inst_0-TOTAL_FORMS": "1",
            "inst_0-MAX_NUM_FORMS": "",
            "inst_0-0-id": "",
            "inst_0-0-DELETE": "False",
            "inst_0-0-language": "en",
            "inst_0-0-description": "test%s" % value
           }


def check_returned_xml(response, id_count):
    "Make sure the response xml has the right values."
    assert_equal(response.status_code, 200)
    assert_equal(response["Content-Type"], "text/xml")

    content = etree.XML(response.content)
    assert_equal(len(content.findall("provider")), id_count)

    ids = content.findall("provider/id")
    assert_equal(len(ids), id_count)
    for (n, i) in enumerate(ids):
        assert_equal(int(i.text), n + 1)

    exports = content.findall("provider/export")
    assert_equal(len(exports), id_count)
    for (n, i) in enumerate(exports):
        assert_equal(i.text, "/export_xml/%d/" % (n + 1))


def check_returned_html(response, id_count):
    assert_equal(response.template[0].name, "config/list.html")
    configs = response.context[0]["configs"]
    assert_equal(len(configs), id_count)


class ListTest(TestCase):
    "A class to test the list view."

    test2dict = make_config("2")
    test3dict = make_config("3")

    fixtures = ['login_testdata.json']

    def test_empty_xml_reponse(self):
        response = self.client.get(reverse("ispdb_list", args=["xml"]), {})
        check_returned_xml(response, 0)

    def test_single_xml_reponse(self):
        self.client.login(username='test_admin', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        assert_equal(response.status_code, 302)
        domain = models.DomainRequest.objects.get(name="test2.com")
        assert isinstance(domain, models.DomainRequest)
        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"approved": "mark valid", "comment": "I liked this domain"})
        domain = models.Domain.objects.get(name="test2.com")
        assert isinstance(domain, models.Domain)
        response = self.client.get(reverse("ispdb_list", args=["xml"]), {})
        check_returned_xml(response, 1)

    def test_two_xml_reponses(self):
        self.client.login(username='test_admin', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        domain = models.DomainRequest.objects.get(name="test2.com")
        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"approved": "mark valid", "comment": "I liked this domain"})
        domain = models.Domain.objects.get(name="test2.com")
        assert isinstance(domain, models.Domain)
        response = self.client.post(reverse("ispdb_add"), ListTest.test3dict)
        domain = models.DomainRequest.objects.get(name="test3.com")
        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"approved": "mark valid", "comment": "I liked this domain"})
        domain = models.Domain.objects.get(name="test3.com")
        assert isinstance(domain, models.Domain)
        response = self.client.get(reverse("ispdb_list", args=["xml"]), {})
        check_returned_xml(response, 2)

    def test_xml_reponse_invalid_domain(self):
        self.client.login(username='test_admin', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        assert_equal(response.status_code, 302)
        domain = models.DomainRequest.objects.get(name="test2.com")
        assert isinstance(domain, models.DomainRequest)
        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"denied": "mark invalid", "comment": "I didn't like this domain"})
        response = self.client.get(reverse("ispdb_list", args=["xml"]), {})
        check_returned_xml(response, 0)

    def test_empty_reponse(self):
        response = self.client.get(reverse("ispdb_list"), {})
        check_returned_html(response, 0)

    def test_single_reponse(self):
        self.client.login(username='test_admin', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        assert_equal(response.status_code, 302)
        domain = models.DomainRequest.objects.get(name="test2.com")
        assert isinstance(domain, models.DomainRequest)

        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"approved": "mark valid",
             "comment": "Always enter a comment here"
            }
        )
        response = self.client.get(reverse("ispdb_list"), {})
        check_returned_html(response, 1)

    def test_two_reponses(self):
        self.client.login(username='test_admin', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        domain = models.DomainRequest.objects.get(name="test2.com")
        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"approved": "mark valid", "comment": "I liked this domain"})

        response = self.client.post(reverse("ispdb_add"), ListTest.test3dict)
        domain = models.DomainRequest.objects.get(name="test3.com")
        response = self.client.post(
            reverse("ispdb_approve", kwargs={"id": domain.config.id}),
            {"denied": "mark invalid", "comment": "I didn't like this domain"})
        response = self.client.get(reverse("ispdb_list"), {})
        check_returned_html(response, 2)

    def test_one_dot_zero_xml_response(self):
        self.client.login(username='test', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        domain = models.DomainRequest.objects.get(name="test2.com")
        assert isinstance(domain, models.DomainRequest)

        response = self.client.post(reverse("ispdb_export_xml",
                                            kwargs={"id": domain.config.id}))
        etree.XML(response.content)
        etree.RelaxNG(file=os.path.join(os.path.dirname(__file__),
                                        'relaxng_schema.xml'))

    def test_one_dot_one_xml_response(self):
        self.client.login(username='test', password='test')
        response = self.client.post(reverse("ispdb_add"), ListTest.test2dict)
        domain = models.DomainRequest.objects.get(name="test2.com")
        assert isinstance(domain, models.DomainRequest)
        response = self.client.post(reverse("ispdb_export_xml",
                kwargs={"version": "1.1", "id": domain.config.id}))
        doc = etree.XML(response.content)

        xml_schema = etree.RelaxNG(file=os.path.join(os.path.dirname(__file__),
                                                     'relaxng_schema.1.1.xml'))
        xml_schema.assertValid(doc)
