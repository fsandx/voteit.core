import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core.validators import html_string_validator
from voteit.core.widgets import RecaptchaWidget
from voteit.core import VoteITMF as _

@colander.deferred
def deferred_access_policy_widget(node, kw):
    request = kw['request']
    view_group = request.registry.getUtility(IViewGroup, name = 'request_meeting_access')
    choices = []
    for (name, va) in view_group.items():
        choices.append((name, va.title))
    if not choices:
        raise ValueError("Can't find anything in the request_meeting_access view group. There's no way to select any policy on how to gain access to the meeting.")
    return deform.widget.RadioChoiceWidget(values = choices)

@schema_factory('MeetingSchema')
class MeetingSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                description = _(u"meeting_title_description",
                                                default=u"Set a title for the meeting that separates it from previous meetings"),
                                validator=html_string_validator,)
    description = colander.SchemaNode(
        colander.String(),
        title = _(u"Description"),
        description = _(u"meeting_description_description",
                        default=u"The description is visible on the first page of the meeting. You can include things like information about the meeting, how to contact the moderator and your logo."),
        missing = u"",
        widget=deform.widget.RichTextWidget())
    meeting_mail_name = colander.SchemaNode(colander.String(),
                                            title = _(u"Name visible on system mail sent from this meeting"),
                                            default = _(u"VoteIT"),)
    meeting_mail_address = colander.SchemaNode(colander.String(),
                                            title = _(u"Email address to send from"),
                                            default = u"noreply@somehost.voteit",
                                            validator = colander.All(colander.Email(msg = _(u"Invalid email address.")), html_string_validator,),)
    access_policy = colander.SchemaNode(colander.String(),
                                        title = _(u"Meeting access policy"),
                                        widget = deferred_access_policy_widget,
                                        default = "invite_only",)


#FIXME: Captcha add schema
#class CaptchaAddMeetingSchema(MeetingSchema):
#
#        settings = request.registry.settings
#        if settings.get('captcha_public_key', None) and settings.get('captcha_private_key', None):
#            captcha = colander.SchemaNode(colander.String(),
#                                          #FIXME: write a good title and description here
#                                          title=_(u"Verify you are human"),
#                                          description = _(u"meeting_captcha_description",
#                                                          default=u"This is to prevent spambots from creating meetings"),
#                                          missing=u"",
#                                          widget=RecaptchaWidget(),)

