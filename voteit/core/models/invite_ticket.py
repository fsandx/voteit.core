from random import choice
from uuid import uuid4
import string

from arche.utils import send_email
from arche.utils import utcnow
from persistent.list import PersistentList
from pyramid.exceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from repoze.folder import Folder
from six import string_types
from zope.interface import implementer

from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IInviteTicket
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.workflow_aware import WorkflowAware


SELECTABLE_ROLES = (security.ROLE_MODERATOR,
                    security.ROLE_DISCUSS,
                    security.ROLE_PROPOSE,
                    security.ROLE_VOTER,
                    security.ROLE_VIEWER,)


@implementer(IInviteTicket)
class InviteTicket(Folder, WorkflowAware):
    """ Invite ticket. Send these to give access to new users.
        See :mod:`voteit.core.models.interfaces.IInviteTicket`.
        All methods are documented in the interface of this class.
    """
    type_name = 'InviteTicket'
    add_permission = None
    css_icon = 'glyphicon glyphicon-send'

    @property
    def content_type(self):
        return self.type_name #b/c

    def __init__(self, email, roles, sent_by = None):
        self.email = email.lower()
        for role in roles:
            if role not in SELECTABLE_ROLES:
                raise ValueError("InviteTicket got '%s' as a role, and that isn't selectable." % role)
        self.roles = roles
        self.created = utcnow()
        self.closed = None
        self.claimed_by = None
        self.sent_by = sent_by
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.sent_dates = PersistentList()
        self.uid = unicode(uuid4())
        super(InviteTicket, self).__init__()

    def claim(self, request):
        #Is the ticket open?
        if self.get_workflow_state() != 'open':
            raise HTTPForbidden("Access already granted with this ticket")
        #Find required resources and do some basic validation
        meeting = find_interface(self, IMeeting)
        assert meeting
        userid = request.authenticated_userid
        if userid is None:
            raise HTTPForbidden("You can't claim a ticket unless you're authenticated.")
        meeting.add_groups(userid, self.roles)
        self.claimed_by = userid
        self.set_workflow_state(request, 'closed')
        self.closed = utcnow()

def send_invite_ticket(ticket, request, message = ""):
    if ticket.closed: #Just as a precaution
        return
    meeting = find_interface(ticket, IMeeting)
    html = render_invite_ticket(ticket, request, message = message)
    subject = _(u"Invitation to ${meeting_title}", mapping = {'meeting_title': meeting.title})
    if send_email(request, subject = subject, recipients = ticket.email, html = html, send_immediately = True):
        ticket.sent_dates.append(utcnow())

def render_invite_ticket(ticket, request, message = "", **kw):
    """ Render invite ticket email html.
        Uses ticket as a context.
    """
    assert IInviteTicket.providedBy(ticket)
    #FIXME: Include meeting logo in mail?
    roles = dict(security.MEETING_ROLES)
    meeting = find_interface(ticket, IMeeting)
    root = find_root(meeting)
    assert IMeeting.providedBy(meeting)
    response = {}
    response['access_link'] = request.resource_url(meeting, 'ticket',
                                                   query = {'email': ticket.email, 'token': ticket.token})
    response['message'] = message
    response['meeting'] = meeting
    response['context'] = ticket
    response['contact_mail'] = meeting.get_field_value('meeting_mail_address')
    response['sender_profile'] = root.users.get(ticket.sent_by)
    response['roles'] = [roles.get(x) for x in ticket.roles]
    return render('voteit.core:templates/email/invite_ticket_email.pt', response, request = request)

def includeme(config):
    config.add_content_factory(InviteTicket)
