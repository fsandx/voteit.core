# -*- coding: utf-8 -*-

import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


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
    
    @property    
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_function(self):
        from voteit.core.interfaces import IWorkflowStateChange
        obj = self._cut()
        value = obj.simple('@admin', request=self.request)
        self.assertIn('/m/_userinfo?userid=admin', value)


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
        
    @property
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_function(self):
        obj = self._cut()
        value = obj.simple(u'#åäöÅÄÖ', request=self.request)
        self.assertIn(u'/m/ai/?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)