# import unittest
# 
# from pyramid import testing
# 
# from voteit.core.testing_helpers import bootstrap_and_fixture
# 
# 
# class MeetingActionsComponentTests(unittest.TestCase):
#         
#     def setUp(self):
#         self.config = testing.setUp()
# 
#     def tearDown(self):
#         testing.tearDown()
#         
#     def _fixture(self):
#         from voteit.core.models.meeting import Meeting
#         root = bootstrap_and_fixture(self.config)
#         root['m'] = meeting = Meeting()
#         return meeting
#     
#     def _api(self, context=None, request=None):
#         from voteit.core.views.api import APIView
#         context = context and context or testing.DummyResource()
#         request = request and request or testing.DummyRequest()
#         return APIView(context, request)
# 
#     def _va(self, name=None, title=None, kwargs={}):
#         class ViewAction():
#             def __init__(self, name, title, kwargs):
#                 self.name = name
#                 self.title = title
#                 self.kwargs = kwargs
#         return ViewAction(name, title, kwargs)
# 
#     def test_meeting_actions(self):
#         self.config.testing_securitypolicy(userid='dummy',
#                                            permissive=True)
#         self.config.scan('voteit.core.views.components.meeting_actions')
#         self.config.scan('voteit.core.views.components.help_actions')
#         self.config.scan('voteit.core.views.components.moderator_actions')
#         context = self._fixture()
#         request = testing.DummyRequest()
#         va = self._va(title='')
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import meeting_actions
#         response = meeting_actions(context, request, va, api=api)
#         self.assertIn('Participants', response)
#         self.assertIn('Meeting', response)
#         self.assertIn('Polls', response)
#         
#     def test_polls_menu(self):
#         self.config.testing_securitypolicy(userid='dummy',
#                                            permissive=True)
#         from voteit.core.models.agenda_item import AgendaItem
#         from voteit.core.models.proposal import Proposal
#         from voteit.core.models.poll import Poll
#         self.config.include('voteit.core.plugins.majority_poll')
#         self.config.include('voteit.core.testing_helpers.register_catalog')
#         request = testing.DummyRequest()
#         self.config = testing.setUp(request = request)
#         context = self._fixture()
#         context.set_workflow_state(request, 'ongoing')
#         context['ai'] = ai = AgendaItem()
#         ai.set_workflow_state(request, 'upcoming')
#         ai.set_workflow_state(request, 'ongoing')
#         ai['p1'] = p1 = Proposal(title='Proposal 1')
#         ai['p2'] = p2 = Proposal(title='Proposal 2')
#         ai['poll'] = Poll(title='Poll')
#         ai['poll'].set_field_value('poll_plugin', 'majority_poll')
#         ai['poll'].set_field_value('proposals', set((p1.uid, p2.uid)))
#         ai['poll'].set_workflow_state(request, 'upcoming')
#         ai['poll'].set_workflow_state(request, 'ongoing')
#         va = self._va('Poll')
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import polls_menu
#         response = polls_menu(context, request, va, api=api)
#         self.assertIn('http://example.com/m/meeting_poll_menu', response)
#         
#     def test_polls_menu_no_meeting(self):
#         context = bootstrap_and_fixture(self.config)
#         request = testing.DummyRequest()
#         va = self._va(title='Poll')
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import polls_menu
#         response = polls_menu(context, request, va, api=api)
#         self.assertEqual('', response)
#         
#     def test_generic_menu(self):
#         self.config.scan('voteit.core.views.components.meeting_actions')
#         context = self._fixture()
#         request = testing.DummyRequest()
#         va = self._va(name='admin_menu', title='Admin menu')
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import generic_menu
#         response = generic_menu(context, request, va, api=api)
#         self.assertIn('<a href="#" class="menu_header">', response)
#         
#     def test_generic_menu_menu_css_cls(self):
#         self.config.scan('voteit.core.views.components.meeting_actions')
#         context = self._fixture()
#         request = testing.DummyRequest()
#         va = self._va(name='admin_menu', title='Admin menu', kwargs={'menu_css_cls': 'dummy-css-class'})
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import generic_menu
#         response = generic_menu(context, request, va, api=api)
#         self.assertIn('dummy-css-class', response)
#         
#     def test_generic_menu_meeting_only(self):
#         self.config.scan('voteit.core.views.components.meeting_actions')
#         context = bootstrap_and_fixture(self.config)
#         request = testing.DummyRequest()
#         va = self._va(name='admin_menu', title='Admin menu', kwargs={'meeting_only': True})
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import generic_menu
#         response = generic_menu(context, request, va, api=api)
#         self.assertEqual('', response)
#         
#     def test_generic_menu_link(self):
#         context = self._fixture()
#         request = testing.DummyRequest()
#         va = self._va(title='Meeting poll settings', kwargs={'link': 'dummy'})
#         api = self._api(context, request)
#         from voteit.core.views.components.meeting_actions import generic_menu_link
#         response = generic_menu_link(context, request, va, api=api)
#         self.assertIn('<li><a href="http://example.com/m/dummy">Meeting poll settings</a></li>', response)
#         
#     def test_meeting_poll_menu(self):
#         self.config.testing_securitypolicy(userid='dummy',
#                                            permissive=True)
#         from voteit.core.models.agenda_item import AgendaItem
#         from voteit.core.models.proposal import Proposal
#         from voteit.core.models.poll import Poll
#         self.config.include('voteit.core.plugins.majority_poll')
#         self.config.include('voteit.core.testing_helpers.register_catalog')
#         request = testing.DummyRequest()
#         context = self._fixture()
#         context.set_workflow_state(request, 'ongoing')
#         context['ai'] = ai = AgendaItem()
#         ai.set_workflow_state(request, 'upcoming')
#         ai.set_workflow_state(request, 'ongoing')
#         ai['p1'] = p1 = Proposal(title='Proposal 1')
#         ai['p2'] = p2 = Proposal(title='Proposal 2')
#         ai['p3'] = p3 = Proposal(title='Proposal 3')
#         ai['p4'] = p4 = Proposal(title='Proposal 4')
#         
#         ai['poll1'] = poll1 = Poll(title='Poll1')
#         poll1.set_field_value('poll_plugin', 'majority_poll')
#         poll1.set_field_value('proposals', set(p1.uid))
#         
#         ai['poll2'] = poll2 = Poll(title='Poll2')
#         poll2.set_field_value('poll_plugin', 'majority_poll')
#         poll2.set_field_value('proposals', set(p2.uid))
#         poll2.set_workflow_state(request, 'upcoming')
#         
#         ai['poll3'] = poll3 = Poll(title='Poll3')
#         poll3.set_field_value('poll_plugin', 'majority_poll')
#         poll3.set_field_value('proposals', set(p3.uid))
#         poll3.set_workflow_state(request, 'upcoming')
#         poll3.set_workflow_state(request, 'ongoing')
#         
#         ai['poll4'] = poll4 = Poll(title='Poll4')
#         poll4.set_field_value('poll_plugin', 'majority_poll')
#         poll4.set_field_value('proposals', set(p4.uid))
#         poll4.set_workflow_state(request, 'upcoming')
#         poll4.set_workflow_state(request, 'ongoing')
#         poll4.set_workflow_state(request, 'closed')
#         
#         from voteit.core.views.components.meeting_actions import MeetingActionsMenuBody
#         view_obj = MeetingActionsMenuBody(context, request)
#         response = view_obj.meeting_poll_menu()
#         self.assertIn('results', response)
#         self.assertIn('private', response['results'])
#         self.assertIn('upcoming', response['results'])
#         self.assertIn('ongoing', response['results'])
#         self.assertIn('closed', response['results'])
#         self.assertEqual(len(response['results']['private']), 1)
#         self.assertEqual(len(response['results']['upcoming']), 1)
#         self.assertEqual(len(response['results']['ongoing']), 1)
#         self.assertEqual(len(response['results']['closed']), 1)
