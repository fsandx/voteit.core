from pyramid.traversal import resource_path
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from webhelpers.html.render import sanitize
from HTMLParser import HTMLParseError

from voteit.core.models.catalog import reindex_object
from voteit.core.models.catalog import resolve_catalog_docid


def evolve(root):
    print "Removing HTML from discussion posts and proposals"
    catalog = root.catalog 

    count, result = catalog.query(Eq('path', resource_path(root)) & \
                                  Any('content_type', ('DiscussionPost', 'Proposal', )))

    print "Processing %s objects" % count
    for docid in result:
        # get object
        obj = resolve_catalog_docid(catalog, root, docid)
        try:
            obj.title = unicode(sanitize(obj.title))
        except Exception, e:
            print u"could not sanitize title\n%s" % obj.title
            obj.title = unicode(raw_input("Enter manualy sanitized title: "), 'utf-8')
        reindex_object(catalog, obj)