import deform
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_resend
from voteit.core.models.schemas import button_send
from voteit.core.models.schemas import button_delete
from voteit.core.validators import deferred_token_form_validator


class TicketView(BaseView):
    """ View for all things that have to do with meeting invitation tickets. """

    @view_config(name = 'ticket_login', context = IMeeting, renderer = "templates/ticket_login.pt", permission = NO_PERMISSION_REQUIRED)
    def ticket_login(self):
        """ If user is not logged in, display a registration button and the normal
            login form on the left hand side.
        """
        self.response['title'] = _(u"Login or register to gain access")
        self.response['came_from'] = self.request.GET.get('came_from', '')
        return self.response

    @view_config(name = 'ticket_claim', context = IMeeting, renderer = "templates/ticket_claim.pt", permission = NO_PERMISSION_REQUIRED)
    def ticket_claim(self):
        """ After login or registration, redirect back here, where information about the ticket will be displayed,
            and a confirmation that you want to use the ticket for the current user.
            
            While we use a regular deform form, it's not ment to be displayed or handle any validation.
        """
        if not self.api.userid:
            raise HTTPForbidden("Direct access to this view for unauthorized users not allowed.")
        schema = createSchema('ClaimTicketSchema', validator = deferred_token_form_validator)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_add, button_cancel))
        if self.request.GET.get('claim'):
            controls = self.request.params.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                msg = _(u"ticket_validation_fail",
                        default = u"Ticket validation failed. Either the ticket doesn't exist, was already used or the url used improperly. "
                                  u"If you need help, please contact the moderator that invited you to this meeting.")
                self.api.flash_messages.add(msg, type = 'error')
                url = self.request.resource_url(self.api.root)
                return HTTPFound(location = url)
            #Everything in order, claim ticket
            ticket = self.context.invite_tickets[appstruct['email']]
            ticket.claim(self.request)
            self.api.flash_messages.add(_(u"You've been granted access to the meeting. Welcome!"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        #No action, render page
        claim_action_query = dict(
            claim = '1',
            email = self.request.GET.get('email', ''),
            token = self.request.GET.get('token', ''),
        )
        #FIXME: Use logout button + redirect link to go back to claim ticket
        self.response['claim_action_url'] = self.request.resource_url(self.context, 'ticket_claim', query = claim_action_query)
        return self.response

    @view_config(name="ticket", context=IMeeting, permission = NO_PERMISSION_REQUIRED)
    def ticket_redirect(self):
        """ Handle incoming ticket url.
            Either redirect to information about registration, or the page about using the ticket.
            
            Note: Don't validate ticket until user has logged in. At least that makes bruteforcing it a bit harder.
        """
        email = self.request.GET.get('email', '')
        token = self.request.GET.get('token', '')
        #Authenticated users
        if self.api.userid:
            if email and token:
                url = self.request.resource_url(self.context, 'ticket_claim', query = {'email': email, 'token': token})
            else:
                url = self.request.resource_url(self.context)
                msg = _(u"ticket_link_wrong_parameters_error",
                        default = U"The ticket link did not contain a token and an email address. Perhaps you came to this page by mistake?")
                self.api.flash_messages.add(msg, type = 'error')
        #Unauthenticated users
        else:
            url = self.request.resource_url(self.context, 'ticket_login', query = {'came_from': self.request.url})
        return HTTPFound(location = url)

    @view_config(name="add_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def add_tickets(self):
        """ Add ticket invites to this meeting.
            Renders a form where you can paste email addresses and select which roles they
            should have once they register. When the form is submitted, it will also email
            users.
        """
        self.response['title'] = _(u"Send meeting invitations")
        post = self.request.POST
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        schema = createSchema('AddTicketsSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)
        if 'add' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            emails = appstruct['emails'].splitlines()
            message = appstruct['message']
            roles = appstruct['roles']
            added = 0
            rejected = 0
            for email in emails:
                result = self.context.add_invite_ticket(email, roles, message, sent_by = self.api.userid, overwrite = appstruct['overwrite'])
                if result:
                    added += 1
                else:
                    rejected += 1
            if not rejected:
                msg = _('added_tickets_text', default=u"Successfully added ${added} invites",
                        mapping={'added': added})
            elif not added:
                msg = _('no_tickets_added',
                        default = u"No tickets added - all you specified probably exist already. (Proccessed ${rejected})",
                        mapping = {'rejected': rejected})
                self.api.flash_messages.add(msg)
                url = self.request.resource_url(self.context, 'add_tickets')
                return HTTPFound(location = url)
            else:
                msg = _('added_tickets_text_some_rejected',
                        default=u"Successfully added ${added} invites but discarded ${rejected} since they already existed or were already used.",
                        mapping={'added': added, 'rejected': rejected})
            self.api.flash_messages.add(msg)
            url = self.request.resource_url(self.context, 'send_tickets', query = {'send': 'send', 'previous_invites': 0})
            return HTTPFound(location=url)
        #No action - Render add form
        self.response['form'] = form.render()
        return self.response

    @view_config(name = "send_tickets", context = IMeeting, renderer = "templates/send_tickets.pt", permission = security.MANAGE_GROUPS)
    def send_tickets(self):
        schema = createSchema('SendticketsSchema')
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons = (button_send,), method = 'GET')
        if 'send' in self.request.GET:
            controls = self.request.GET.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            #FIXME implement later
            del appstruct['remind_days']
            self.response['emails'] = self.context.get_ticket_names(previous_invites = appstruct['previous_invites'])
            self.response['tickets_to_send'] = len(self.response['emails'])
        return self.response

    @view_config(name="manage_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def manage_tickets(self):
        """ A form for handling and reviewing already sent tickets.
        """
        self.response['title'] = _(u"Current invitations")
        schema = createSchema('ManageTicketsSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_resend, button_delete, button_cancel,))
        self.api.register_form_resources(form)
        post = self.request.POST
        emails = ()

        if 'resend' in post or 'delete' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
                if appstruct['apply_to_all'] == True:
                    emails = [x.email for x in self.context.invite_tickets.values() if x.get_workflow_state() != u'closed']
                else:
                    emails = appstruct['emails']
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response

        if emails and 'resend' in post:
            for email in emails:
                self.context.invite_tickets[email].send(self.request)
            
            self.api.flash_messages.add(_('resent_invites_notice',
                                          default=u"Resending ${count_emails} invites",
                                          mapping={'count_emails':len(emails)}))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)

        if emails and 'delete' in post:
            for email in emails:
                del self.context.invite_tickets[email]
            
            self.api.flash_messages.add(_('deleting_invites_notice',
                                          default=u"Deleting ${count_emails} invites",
                                          mapping={'count_emails':len(emails)}))

            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)

        #No action - Render add form
        self.response['form'] = form.render()
        return self.response


@view_config(name = "send_tickets", context = IMeeting, renderer = "json", permission = security.MANAGE_GROUPS, xhr = True)
def send_tickets_action(context, request):
    result = []
    post_vars = request.POST.dict_of_lists()
    for email in post_vars.get('emails', ()):
        context.invite_tickets[email].send(request)
        result.append(email)
        if len(result) > 19:
            break
    return {'sent': len(result), 'emails': result}
