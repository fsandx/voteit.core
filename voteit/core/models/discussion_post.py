import colander
import deform
from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from betahaus.pyracont.decorators import content_factory

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.base_content import BaseContent
from voteit.core.models.unread_aware import UnreadAware


ACL =  {}
ACL['open'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_MODERATOR, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_OWNER, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
               (Allow, security.ROLE_VIEWER, (security.VIEW,)),
               DENY_ALL,
               ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_OWNER, security.VIEW),
                 (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]


@content_factory('DiscussionPost', title=_(u"Discussion Post"))
class DiscussionPost(BaseContent, UnreadAware):
    """ Discussion post content
    """
    implements(IDiscussionPost, ICatalogMetadataEnabled)
    content_type = 'DiscussionPost'
    display_name = _(u"Discussion Post")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_DISCUSSION_POST
    schemas = {'add': 'DiscussionPostSchema'}


    @property
    def __acl__(self):
        #FIXME: Check meeting etc
        return ACL['open']

    #Override title, it will be used to generate a name for this content. (Like an id)
    def _get_title(self):
        return self.get_field_value('text')

    def _set_title(self, value):
        pass #Not used

    title = property(_get_title, _set_title)
