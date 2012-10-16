# -*- coding: utf-8 -*-

import unittest

from pyramid import testing
from betahaus.pyracont.interfaces import ITransformation
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.testing_helpers import bootstrap_and_fixture


class AutoLinkTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.transformation import AutoLink
        return AutoLink

    def test_verify_class(self):
        self.failUnless(verifyClass(ITransformation, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ITransformation, self._cut()))

    def test_appstruct(self):
        obj = self._cut()
        appstruct = {'text': 'www.betahaus.net and http://www.voteit.se'}
        expected = '<a href="http://www.betahaus.net">www.betahaus.net</a> and <a href="http://www.voteit.se">http://www.voteit.se</a>'
        obj.appstruct(appstruct, 'text')
        self.assertEqual(appstruct['text'], expected)

    def test_simple(self):
        obj = self._cut()
        text = "There's no place like https://127.0.0.1"
        expected = 'There&#39;s no place like <a href="https://127.0.0.1">https://127.0.0.1</a>'
        self.assertEqual(obj.simple(text), expected)

    def test_integration(self):
        self.config.scan('voteit.core.models.transformation')
        util = self.config.registry.queryUtility(ITransformation, 'auto_link')
        self.failUnless(util)
        

class NL2BRTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.transformation import NL2BR
        return NL2BR

    def test_verify_class(self):
        self.failUnless(verifyClass(ITransformation, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ITransformation, self._cut()))

    def test_appstruct(self):
        obj = self._cut()
        appstruct = {'text': "with\nsome\nlinebreaks"}
        expected = "with<br />\nsome<br />\nlinebreaks"
        obj.appstruct(appstruct, 'text')
        self.assertEqual(appstruct['text'], expected)

    def test_simple(self):
        obj = self._cut()
        expected = "with<br />\nsome<br />\nlinebreaks"
        self.assertEqual(obj.simple("with\nsome\nlinebreaks"), expected)

    def test_integration(self):
        self.config.scan('voteit.core.models.transformation')
        util = self.config.registry.queryUtility(ITransformation, 'nl2br')
        self.failUnless(util)


class AtUseridLinkTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest(context=self._fixture)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.models.transformation import AtUseridLink
        return AtUseridLink

    def test_verify_class(self):
        self.failUnless(verifyClass(ITransformation, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ITransformation, self._cut()))

    @property    
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_appstruct(self):
        obj = self._cut()
        appstruct = {'text': 'Hey @admin!'}
        obj.appstruct(appstruct, 'text', request=self.request)
        expected = 'Hey <a class="inlineinfo" href="/m/_userinfo?userid=admin" title="VoteIT Administrator">@admin</a>!'
        self.assertEqual(appstruct['text'], expected)  

    def test_simple(self):
        obj = self._cut()
        value = obj.simple('@admin', request=self.request)
        self.assertIn('/m/_userinfo?userid=admin', value)

    def test_several_names_with_nonexistent_user(self):
        obj = self._cut()
        value = obj.simple('@admin says hello to @john_doe', request=self.request)
        expected = '<a class="inlineinfo" href="/m/_userinfo?userid=admin" title="VoteIT Administrator">@admin</a> says hello to @john_doe'
        self.assertEqual(value, expected)


class Tags2LinksTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest(context=self._fixture)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.models.transformation import Tag2Links
        return Tag2Links

    def test_verify_class(self):
        self.failUnless(verifyClass(ITransformation, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ITransformation, self._cut()))

    @property
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_simple(self):
        obj = self._cut()
        value = obj.simple(u'#åäöÅÄÖ', request=self.request)
        self.assertIn(u'/m/ai/?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)

    def test_appstruct(self):
        obj = self._cut()
        appstruct = {'text': "I like #pizza!? and #some'other'things,"}
        obj.appstruct(appstruct, 'text', request=self.request)
        expected = 'I like <a class="tag" href="/m/ai/?tag=pizza">#pizza</a>!? and <a class="tag" href="/m/ai/?tag=some">#some</a>\'other\'things,'
        self.assertEqual(appstruct['text'], expected)

    def test_tags_disabled(self):
        obj = self._cut()
        from pyramid.traversal import find_interface
        from voteit.core.models.interfaces import IMeeting
        meeting = find_interface(self.request.context, IMeeting)
        meeting.set_field_value('tags_enabled', False)
        value = obj.simple(u'#åäöÅÄÖ', request=self.request)
        self.assertNotIn(u'/m/ai/?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)