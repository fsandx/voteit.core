import re

from BeautifulSoup import BeautifulSoup
from betahaus.pyracont import check_unique_name
from pyramid.security import has_permission
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from translationstring import TranslationString
from webhelpers.html.tools import strip_tags
import colander

from voteit.core import VoteITMF as _
from voteit.core.exceptions import TokenValidationError
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.user import USERID_REGEXP
from voteit.core.security import MANAGE_GROUPS
from voteit.core.security import MEETING_ROLES
from voteit.core.security import ROOT_ROLES
from voteit.core.security import VIEW
from voteit.core.security import find_authorized_userids


AT_USERID_PATTERN = re.compile(r'(\A|\s)@('+USERID_REGEXP+r')')
NEW_USERID_PATTERN = re.compile(r'^'+USERID_REGEXP+r'$')


# def password_validation(node, value):
#     """ check that password is
#         - at least 6 chars and at most 100.
#     """
#     if len(value) < 6:
#         raise colander.Invalid(node, _(u"Too short. At least 6 chars required."))
#     if len(value) > 100:
#         raise colander.Invalid(node, _(u"Less than 100 chars please."))


def html_string_validator(node, value):
    """
        checks that input doesn't contain html tags
    """
    # removes tags and new lines and replaces <br> with newlines
    svalue = strip_tags(value)
    # removes newlines
    svalue = re.sub(r"\r?\n", " ", svalue)
    value = re.sub(r"\r?\n", " ", value)
    # removes duplicated whitespaces
    svalue = ' '.join(svalue.split())
    value = ' '.join(value.split())
    # if the original value and the stript value is not the same rais exception
    if not svalue == value:
        raise colander.Invalid(node, _(u"HTML is not allowed."))


def multiple_email_validator(node, value):
    """
        checks that each line of value is a correct email
    """
    validator = colander.Email()
    invalid = []
    for email in value.splitlines():
        try:
            validator(node, email)
        except colander.Invalid:
            invalid.append(email)
    if invalid:
        emails = ", ".join(invalid)
        raise colander.Invalid(node, _(u"The following adresses is invalid: ${emails}", mapping={'emails': emails}))


class AtEnabledTextArea(object):
    """ Validator which succeeds if @-sign points to a user that exists in this meeting.
        Also checks that text doesn't contain evil chars :)
    """
    def __init__(self, context):
        self.context = context

    def __call__(self, node, value):
        #First, check for bad chars, since it requires less CPU
        html_string_validator(node, value)
        invalid = set()
        matched_userids = set()
        #Note: First match object will be blankspace, second the userid.
        [matched_userids.add(x[1]) for x in re.findall(AT_USERID_PATTERN, value)]
        if not matched_userids:
            return
        #Check that user exists in meeting
        meeting = find_interface(self.context, IMeeting)
        valid_userids =  find_authorized_userids(meeting, (VIEW,))
        for userid in matched_userids:
            #Check if requested userid has permission in meeting
            if not userid in valid_userids:
                invalid.add(userid)
            if invalid:
                userids = ", ".join(invalid)
                raise colander.Invalid(node, _(u"userid_validator_error",
                                               default=u"The following userids is invalid: ${userids}. Remember that userids are case sensitive.",
                                               mapping={'userids': userids}))

@colander.deferred
def deferred_at_enabled_text(node, kw):
    context = kw['context']
    return AtEnabledTextArea(context)


# class NewUniqueUserID(object):
#     """ Check if UserID is unique globally in the site and that UserID conforms to correct standard. """
#     
#     def __init__(self, context):
#         self.context = context
# 
#     def __call__(self, node, value):
#         if not NEW_USERID_PATTERN.match(value):
#             msg = _('userid_char_error',
#                     default=u"UserID must be 3-30 chars, start with lowercase a-z and only contain lowercase a-z, numbers, minus and underscore.")
#             raise colander.Invalid(node, msg)
#         
#         root = find_root(self.context)
#         if value in root.users:
#             msg = _('already_registered_error',
#                     default=u"UserID already registered. If it was registered by you, try to retrieve your password.")
#             raise colander.Invalid(node, msg)
        

# @colander.deferred
# def deferred_new_userid_validator(node, kw):
#     context = kw['context']
#     return NewUniqueUserID(context)
# 
# 
# class UniqueEmail(object):
#     """ Check that email address is valid and unique.
#         If context is a User, it's okay to set the same email address.
#         (Otherwise it wouldn't be possible to submit the form with our own address :)
#     """
#     def __init__(self, context):
#         self.context = context
# 
#     def __call__(self, node, value):
#         value = value.lower() #Make sure it'slowercase
#         default_email_validator = colander.Email(msg=_(u"Invalid email address."))
#         default_email_validator(node, value)
#         #context can be IUser or IUsers
#         users = find_root(self.context).users
#         #User with email exists?
#         match = users.get_user_by_email(value)
#         if match and self.context != match:
#             #Something was found, and it isn't this context - I.e. some other user
#             msg = _(u"email_not_unique_error",
#                     default=u"Another user has already registered with that email address. If you've lost your password, request a new one instead.")
#             raise colander.Invalid(node, 
#                                    msg)
# 
# 
# @colander.deferred
# def deferred_unique_email_validator(node, kw):
#     context = kw['context']
#     return UniqueEmail(context)
# 
# 
# class CheckPasswordToken(object):
#     def __init__(self, context):
#         assert IUser.providedBy(context)
#         self.context = context
#     
#     def __call__(self, node, value):
#         token = self.context.get_token()
#         msg = _(u"check_password_token_error",
#                 default="Password token doesn't match. Won't allow password change.")
#         exc = colander.Invalid(node, msg)
#         if token is None:
#             raise exc
#         try:
#             token.validate(value)
#         except TokenValidationError:
#             raise exc


# @colander.deferred
# def deferred_password_token_validator(node, kw):
#     context = kw['context']
#     return CheckPasswordToken(context)


class TokenFormValidator(object):
    def __init__(self, context):
        assert IMeeting.providedBy(context)
        self.context = context
    
    def __call__(self, form, value):
        email = value['email']
        token = self.context.invite_tickets.get(email)
        if not token:
            exc = colander.Invalid(form, 'Incorrect email')
            exc['token'] = _(u"Couldn't find any invitation for this email address.")
            raise exc

        if token.token != value['token']:
            exc = colander.Invalid(form, _(u"Email matches, but token doesn't"))
            exc['token'] = _(u"Check this field - token doesn't match")
            raise exc


@colander.deferred
def deferred_token_form_validator(form, kw):
    context = kw['context']
    return TokenFormValidator(context)


# @colander.deferred
# def deferred_existing_userid_validator(node, kw):
#     context = kw['context']
#     return GlobalExistingUserId(context)
# 
# 
# class GlobalExistingUserId(object):
#     def __init__(self, context):
#         self.context = context
#     
#     def __call__(self, node, value):
#         root = find_root(self.context)
#         userids = tuple(root.users.keys())
#         if value not in userids:
#             msg = _(u"globally_existing_userid_validation_error",
#                     default=u"UserID not found")
#             raise colander.Invalid(node, 
#                                    msg)
# 
# 
# @colander.deferred
# def deferred_existing_userid_or_email_validator(node, kw):
#     context = kw['context']
#     return ExistingUserIdOrEmail(context)
# 
# 
# class ExistingUserIdOrEmail(object):
#     def __init__(self, context):
#         self.context = context
#     
#     def __call__(self, node, value):
#         if '@' in value:
#             #assume email
#             root = find_root(self.context)
#             user = root['users'].get_user_by_email(value)
#             if not IUser.providedBy(user):
#                 msg = _(u"email_to_user_validation_error",
#                         default=u"I couldn't find any user with this email.")
#                 raise colander.Invalid(node, msg)
#         else:
#             userid_validator = GlobalExistingUserId(self.context)
#             userid_validator(node, value)


def richtext_validator(node, value):
    """
        checks that input doesn't contain forbidden html tags
    """
    INVALID_TAGS = ['textarea', 'select', 'option', 'input', 'button', 'script']
    soup = BeautifulSoup(value)
    invalid = False
    for tag in soup.findAll(True):
        if tag.name in INVALID_TAGS:
            invalid = True
    if invalid:
        raise colander.Invalid(node, _(u"Contains forbidden HTML tags."))


# @colander.deferred
# def deferred_context_roles_validator(node, kw):
#     context = kw['context']
#     request = kw['request']
#     return ContextRolesValidator(context, request)
# 
# 
# class ContextRolesValidator(object):
#     """ Check that the roles a user tries to assign is allowed in this context.
#     """
#     
#     def __init__(self, context, request):
#         self.context = context
#         self.request = request
#     
#     def __call__(self, node, value):
#         if not has_permission(MANAGE_GROUPS, self.context, self.request):
#             raise colander.Invalid(node, _(u"You can't change groups in this context"))
#         roles = []
#         if ISiteRoot.providedBy(self.context):
#             roles.extend([x[0] for x in ROOT_ROLES])
#         elif IMeeting.providedBy(self.context):
#             roles.extend([x[0] for x in MEETING_ROLES])
#         for v in value:
#             if v not in roles:
#                 raise colander.Invalid(node, _(u"wrong_context_for_roles_error",
#                                                default = u"Group ${group} can't be assigned in this context",
#                                                mapping = {'group': v}))


# @colander.deferred
# def deferred_check_context_unique_name(node, kw):
#     """ Check that a name isn't used within context, or that it's a view within this context.
#     """
#     context = kw['context']
#     request = kw['request']
#     return ContextUniqueNameValidator(context, request)


# class ContextUniqueNameValidator(object):
#     """ Make sure that a name in a context doesn't exist, or is a view.
#     """
#     def __init__(self, context, request):
#         self.context = context
#         self.request = request
#     
#     def __call__(self, node, value):
#         if not check_unique_name(self.context, self.request, value):
#             raise colander.Invalid(node, _(u"not_unique_name_within_context",
#                                             default = u"Something with the name '${value}' already exists within this context. Pick another name!",
#                                             mapping = {'value': value}))


class NotOnlyDefaultTextValidator(object):
    """ Validator which fails if only default text or only tag is pressent
    """
    def __init__(self, context, request, default_deferred):
        self.context = context
        #self.api = api
        self.request = request
        self.default_deferred = default_deferred

    def __call__(self, node, value):
        # since colander.All doesn't handle deferred validators we call the validator for AtEnabledTextArea here 
        at_enabled_validator = AtEnabledTextArea(self.context)
        at_enabled_validator(node, value)
        default = self.default_deferred(node, {'context': self.context, 'request': self.request})
        if isinstance(default, TranslationString):
            default = self.request.localizer.translate(default)
            #default = self.api.translate(default)
        if value.strip() == default.strip():
            raise colander.Invalid(node, _(u"only_default_text_validator_error",
                                           default=u"Only the default content is not valid",))


# class LoginPasswordValidator(object):
#     """ Make sure a user exist and check that users password. This is a validator for a form,
#         since it checks the field userid and password.
#         
#         Displaying information about bad password or userid might not be a good idea, so we won't do that now.
#     """
#     def __init__(self, context):
#         assert ISiteRoot.providedBy(context)
#         self.context = context
#     
#     def __call__(self, form, value):
#         password = value['password']
#         userid = value['userid'] #Might be an email address!
#         exc = colander.Invalid(form, u"Login invalid") #Raised if trouble
#         exc['userid'] = _(u"Use either email address or userid to login.")
#         exc['password'] = _(u"Password is case sensitive.")
#         #First, retrieve user object
#         if u'@' in userid:
#             user = self.context.users.get_user_by_email(userid)
#         else:
#             user = self.context.users.get(userid)
#         if user is None:
#             raise exc
#         #Validate password
#         pw_field = user.get_custom_field('password')
#         if not pw_field.check_input(password):
#             raise exc
# 
# @colander.deferred
# def deferred_login_password_validator(form, kw):
#     context = kw['context']
#     root = find_root(context)
#     return LoginPasswordValidator(root)


class CSRFTokenValidator(object):
    """ Validate CSRF token. Important for all forms regarding security.
    """
    def __init__(self, api):
        self.api = api
    
    def __call__(self, node, value):
        token = self.api.request.session.get_csrf_token()
        if not value or value != token:
            msg = _(u"csrf_token_error_notice",
                    default = u"Security token did not match. This may happen when you take a long "
                              u"time before completing a form, or during a server restart. "
                              u"Reload this page and try again. If you like to keep your information, copy it from this form. "
                              u"If you ended up on this page while filling in a form on another site, someone tried to hack your account. "
                              u"Please report this to the moderators immediately.")
            #Add to flash message as well, hidden fields won't display validation errors!
            self.api.flash_messages.add(msg, type = 'error')
            raise colander.Invalid(node, msg)


@colander.deferred
def deferred_csrf_token_validator(node, kw):
    api = kw['api']
    return CSRFTokenValidator(api)
