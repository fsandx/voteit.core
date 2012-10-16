import re

from betahaus.pyracont.decorators import transformator
from betahaus.pyracont import Transformation
from pyramid.traversal import find_root
from pyramid.traversal import find_interface
from repoze.folder import unicodify
from webhelpers.html.tools import auto_link
from webhelpers.html import HTML

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.tags import TAG_PATTERN


AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]+)', flags=re.UNICODE)
NL_PATTERN = re.compile(R"\r\n|\n|\r")


@transformator()
class AutoLink(Transformation):
    name = 'auto_link'
    
    def appstruct(self, appstruct, node_name, **kw):
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        # making sure that value is unicode
        value = unicodify(value)
        
        return auto_link(value, link='urls')


@transformator()
class NL2BR(Transformation):
    name = 'nl2br'
    
    def appstruct(self, appstruct, node_name, **kw):
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        # making sure that value is unicode
        value = unicodify(value)
        
        value = re.sub(NL_PATTERN, "\n", value)
        value = value.replace("\n", "<br />\n")
        return value


@transformator()
class Tag2Links(Transformation):
    name = 'tag2links'
    
    def appstruct(self, appstruct, node_name, **kw):
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        request = kw['request']
        context = request.context
        
        # making sure that value is unicode
        value = unicodify(value)
        
        meeting = find_interface(context, IMeeting)
        if not meeting.get_field_value('tags_enabled', True):
            return value

        def handle_match(matchobj):
            pre, tag, post = matchobj.group(1, 2, 3)
            link = {'href': request.resource_url(request.context, '', query={'tag': tag}).replace(request.application_url, ''),
                    'class': "tag",}
            return pre + HTML.a('#%s' % tag, **link) + post
    
        return re.sub(TAG_PATTERN, handle_match, value)


@transformator()
class AtUseridLink(Transformation):
    name = 'at_userid_link'
    
    def appstruct(self, appstruct, node_name, **kw):
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        request = kw['request']
        context = request.context

        # making sure that value is unicode
        value = unicodify(value)
        
        users = find_root(context).users
        meeting = find_interface(context, IMeeting)
    
        def handle_match(matchobj):
            # The pattern contains a space so we only find usernames that 
            # has a whitespace in front, we save the spaced so we can but 
            # it back after the transformation
            space, userid = matchobj.group(1, 2)
            #Force lowercase userid
            userid = userid.lower()
            if userid in users: 
                user = users[userid]
        
                tag = {}
                tag['href'] = request.resource_url(meeting, '_userinfo', query={'userid': userid}).replace(request.application_url, '')
                tag['title'] = user.title
                tag['class'] = "inlineinfo"
                return space + HTML.a('@%s' % userid, **tag)
            else:
                return space + '@' + userid
    
        return re.sub(AT_PATTERN, handle_match, value)
    