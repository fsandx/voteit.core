from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from deform import Form
from pyramid.url import resource_url
from betahaus.pyracont.factories import createSchema
from voteit.core.models.schemas import button_login
from voteit.core.security import ADD_MEETING
from voteit.core.security import MODERATE_MEETING
from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting, ISiteRoot
from pyramid.traversal import resource_path


@view_action('main', 'navigation')
def navigation(context, request, va, **kwargs):
    response = dict(
        api = kwargs['api']
    )
    return render('../templates/navigation.pt', response, request = request)

@view_action('navigation', 'login', hello = 'bla')
def login_box(context, request, va, **kwargs):
    api = kwargs['api']

    #FIXME: Ticket system makes it a bit of a hassle to make login detached from registration.
    #We'll do that later. For now, let's just check if user is on login or registration page

    url = request.path_url
    if url.endswith('login') or url.endswith('register'):
        return u""
    login_schema = createSchema('LoginSchema').bind(context = context, request = request)
    action_url = resource_url(api.root, request) + 'login'
    login_form = Form(login_schema, buttons=(button_login,), action=action_url)
    api.register_form_resources(login_form)
    return login_form.render()

    
@view_action('navigation_sections', 'closed', title = _(u"Closed"), state = 'closed')
@view_action('navigation_sections', 'ongoing', title = _(u"Ongoing"), state = 'ongoing')
@view_action('navigation_sections', 'upcoming', title = _(u"Upcoming"), state = 'upcoming')
@view_action('navigation_sections', 'private', title = _(u"Private"), state = 'private',
             permission = MODERATE_MEETING, interface = IMeeting)
def navigation_section(context, request, va, **kwargs):
    api = kwargs['api']
    state = va.kwargs['state']

    response = {}
    response['api'] = api
    response['state'] = state
    response['section_title'] = va.title

    if request.cookies.get("%s-%s" % (context.uid, state)):
        response['closed_section'] = True
        return render('../templates/snippets/navigation_section.pt', response, request = request)

    #Meeting or root context?
    if ISiteRoot.providedBy(context):
        content_type = 'Meeting'
    else:
        content_type = 'AgendaItem'

    context_path = resource_path(context)
    query = dict(
        allowed_to_view = {'operator': 'or', 'query': api.context_effective_principals(context)},
        workflow_state = state,
        content_type = content_type,
        path = context_path,
    )
    
    def _count_query(path, content_type, unread = False):
        """ Returns number of an item, possbly unread only. """
        if unread:
            return api.search_catalog(path = path, content_type = content_type, unread = api.userid)[0]
        return api.search_catalog(path = path, content_type = content_type)[0]

    response['brains'] = api.get_metadata_for_query(**query)
    response['context_path'] = context_path
    response['count_query'] = _count_query
    response['closed_section'] = False
    return render('../templates/snippets/navigation_section.pt', response, request = request)