import re

from betahaus.pyracont.decorators import transformator
from betahaus.pyracont import Transformation
from pyramid.traversal import find_root
from pyramid.traversal import find_interface

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.tags import TAG_PATTERN


#        text = sanitize(text)
#        text = auto_link(text, link='urls')
#        text = nl2br(text)
#        if self.meeting.get_field_value('tags_enabled', True):
#            text = tags2links(unicode(text), self.context, self.request)
#        text = at_userid_link(text, self.context, self.request)
#        return text



#    discussion_text_out = ('auto_link', 'nl2br', 'tag2links', 'at_userid_link'),


AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]+)', flags=re.UNICODE)


@transformator()
class AutoLink(Transformation):
    name = 'auto_link'
    
    def appstruct(self, appstruct, node_name, **kw):
        if node_name not in appstruct:
            return #nothing to do
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        from webhelpers.html.tools import auto_link
        return auto_link(text, link='urls')


@transformator()
class NL2BR(Transformation):
    name = 'nl2br'
    
    def appstruct(self, appstruct, node_name, **kw):
        if node_name not in appstruct:
            return #nothing to do
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        from webhelpers.html.converters import nl2br
        return nl2br(value)


@transformator()
class Tag2Links(Transformation):
    name = 'tag2links'
    
    def appstruct(self, appstruct, node_name, **kw):
        if node_name not in appstruct:
            return #nothing to do
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        from webhelpers.html import HTML
        request = kw['request']

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
        if node_name not in appstruct:
            return #nothing to do
        appstruct[node_name] = self.simple(appstruct[node_name], **kw)

    def simple(self, value, **kw):
        from webhelpers.html import HTML
        request = kw['request']

        users = find_root(request.context).users
        meeting = find_interface(request.context, IMeeting)
    
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
    