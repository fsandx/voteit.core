from logging import getLogger
from datetime import datetime

from betahaus.pyracont import BaseFolder
from zope.interface import implements
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from repoze.folder import unicodify

from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.security_aware import SecurityAware
from voteit.core.security import ROLE_OWNER

#FIXME: This should be changable some way.
#Things that should never be saved
RESTRICTED_KEYS = ('csrf_token', )


class BaseContent(BaseFolder, SecurityAware):
    __doc__ = IBaseContent.__doc__
    implements(IBaseContent)
    add_permission = None
    content_type = None
    allowed_contexts = ()
    schemas = {}

    def __init__(self, **kwargs):
        """ Initialize class. note that the superclass will create field storage etc
            on init, so it's important to run super.
            creators is required in kwargs, this class will try to extract it from
            current request if it isn't present.
            Also, owner role will be set for the first in the creators-tuple.
        """
        if 'creators' not in kwargs:
            request = get_current_request()
            if request is None:
                #request will be None in some tests
                userid = None
            else:
                userid = authenticated_userid(request)

            if userid is None:
                logger = getLogger('voteit.core')
                logger.warn("Can't find userid for '%s'. Unable to set owner for this object." % self)
            else:
                kwargs['creators'] = (userid,)

        #Set owner - if it is in kwargs now
        if 'creators' in kwargs:
            userid = kwargs['creators'][0]
            self.add_groups(userid, (ROLE_OWNER,))

        super(BaseContent, self).__init__(**kwargs)

    def set_field_value(self, key, value):
        """ Override BaseFolders set_field_value.
            This method aborts if key is in RESTRICTED_KEYS
        """
        if key in RESTRICTED_KEYS:
            return
        super(BaseContent, self).set_field_value(key, value)

    def _get_title(self):
        return self.get_field_value('title', u"")
    def _set_title(self, value):
        self.set_field_value('title', value)
    title = property(_get_title, _set_title)

    def _get_description(self):
        return self.get_field_value('description', u"")        
    def _set_description(self, value):
        self.set_field_value('description', value)
    description = property(_get_description, _set_description)

    def _get_creators(self):
        return self.get_field_value('creators', ())
    def _set_creators(self, value):
        value = tuple(value)
        self.set_field_value('creators', value)
    creators = property(_get_creators, _set_creators)
        
    def _get_created(self):
        return self.get_field_value('created', None)
    def _set_created(self, value):
        assert isinstance(value, datetime)
        self.set_field_value('created', value)
    created = property(_get_created, _set_created)
    
    def _get_modified(self):
        return self.get_field_value('modified', None)
    def _set_modified(self, value):
        assert isinstance(value, datetime)
        self.set_field_value('modified', value)
    modified = property(_get_modified, _set_modified)

    def _get_uid(self):
        return self.get_field_value('uid', None)
    def _set_uid(self, value):
        value = unicodify(value)
        self.set_field_value('uid', value)
    uid = property(_get_uid, _set_uid)

    def get_content(self, content_type=None, iface=None, states=None, sort_on=None, sort_reverse=False, limit=None):
        """ See IBaseContent """
        results = set()

        for candidate in self.values():
            
            #Specific content_type?
            if content_type is not None:
                if getattr(candidate, 'content_type', '') != content_type:
                    continue
            
            #Specific interface?
            if iface is not None:
                if not iface.providedBy(candidate):
                    continue
            
            #Specific workflow state?
            if states is not None:
                #All objects might not have a workflow. In that case they won't have the method get_workflow_state
                try:
                    curr_state = candidate.get_workflow_state()
                    if isinstance(states, basestring):
                        #states is a string - a single state
                        if not curr_state == states:
                            continue
                    else:
                        #states is an iterable
                        if not curr_state in states:
                            continue
                except AttributeError:
                    continue
            
            results.add(candidate)

        if sort_on is None:
            return tuple(results)
        
        def _sorter(obj):
            return getattr(obj, sort_on)

        results = tuple(sorted(results, key = _sorter, reverse = sort_reverse))
        
        if limit:
            results = results[-limit:]

        return results
