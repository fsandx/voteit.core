from calendar import timegm

from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from repoze.catalog.indexes.path import CatalogPathIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from zope.interface import implements
from zope.component import adapts
from zope.component import getAdapter
from pyramid.traversal import find_resource
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from pyramid.security import principals_allowed_by_permission

from voteit.core.models.interfaces import ICatalogMetadataEnabled,\
    ISecurityAware
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.models.interfaces import ICatalogMetadata
from voteit.core.security import NEVER_EVER_PRINCIPAL
from voteit.core.security import VIEW


SEARCHABLE_TEXT_INDEXES = ('title',
                           'description',)

class CatalogMetadata(object):
    """ An adapter to fetch metadata for the catalog.
        See ICatalogMetadata
    """
    implements(ICatalogMetadata)
    adapts(ICatalogMetadataEnabled)
    
    def __init__(self, context):
        self.context = context

    def __call__(self):
        """ Return a dict of metadata values for an object. """
        #FIXME: Should fields be configurable, or should we just fetch all?
        result = {
            'title':self.context.title,
            'created':self.context.created,
        }
        return result


def update_indexes(catalog, reindex=True):
    """ Add or remove indexes. If reindex is True, also reindex all content if
        an index has been added or removed.
        Will return a set of indexes changed regardless.
    """
    indexes = {
        'title': CatalogFieldIndex(get_title),
        'sortable_title': CatalogFieldIndex(get_sortable_title),
        'description': CatalogFieldIndex(get_description),
        'uid': CatalogFieldIndex(get_uid),
        'content_type': CatalogFieldIndex(get_content_type),
        'workflow_state': CatalogFieldIndex(get_workflow_state),
        'path': CatalogPathIndex(get_path),
        'creators': CatalogKeywordIndex(get_creators),
        'created': CatalogFieldIndex(get_created),
        'allowed_to_view': CatalogKeywordIndex(get_allowed_to_view),
        'searchable_text' : CatalogTextIndex(get_searchable_text),
        'start_time' : CatalogFieldIndex(get_start_time),
        'end_time' : CatalogFieldIndex(get_end_time),
    }
    
    changed_indexes = set()
    
    # add indexes
    for name, index in indexes.iteritems():
        if name not in catalog:
            catalog[name] = index
            if reindex:
                changed_indexes.add(name)
    
    # remove indexes
    for name in catalog.keys():
        if name not in indexes:
            del catalog[name]
            if reindex:
                changed_indexes.add(name)
    
    if reindex:
        reindex_indexes(catalog)

    return changed_indexes


def reindex_indexes(catalog):
    root = find_root(catalog)
    for path, docid in catalog.document_map.address_to_docid.items():

        #FIXME: Handle key error. Output where?
        obj = find_resource(root, path)
        reindex_object(catalog, obj)
        
        #FIXME: Commit will be handled by the regular transactionmanager
        #if this is part of a request. Should we turn this into a script?


def index_object(catalog, obj):
    """ Index an object and add metadata. """
    obj_id = catalog.document_map.add(resource_path(obj))
    catalog.index_doc(obj_id, obj)
    
    #Add metadata
    if ICatalogMetadataEnabled.providedBy(obj):
        metadata = getAdapter(obj, ICatalogMetadata)
        catalog.document_map.add_metadata(obj_id, metadata())


def reindex_object(catalog, obj):
    """ Reindex an object and update metadata. """
    obj_id = catalog.document_map.docid_for_address(resource_path(obj))
    catalog.reindex_doc(obj_id, obj)

    #Add metadata
    if ICatalogMetadataEnabled.providedBy(obj):
        metadata = getAdapter(obj, ICatalogMetadata)
        catalog.document_map.add_metadata(obj_id, metadata())


def unindex_object(catalog, obj):
    """ Remove an index and its metadata. """
    obj_id = catalog.document_map.docid_for_address(resource_path(obj))
    catalog.unindex_doc(obj_id)

    #Remove metadata
    if ICatalogMetadataEnabled.providedBy(obj):
        catalog.document_map.remove_metadata(obj_id)


def reindex_object_security(catalog, obj):
    """ Update security information in the catalog.
        Will update all contained objects as well.
    """
    reindex_object(catalog, obj)
    #Recurse
    #FIXME: We may want to only touch the security related index here, and no metadata.
    for contained in obj.values():
        if ISecurityAware.providedBy(contained):
            reindex_object_security(catalog, contained)

#Indexes
def get_title(object, default):
    return object.title

def get_sortable_title(object, default):
    return object.title.lower()

def get_description(object, default):
    return object.description

def get_uid(object, default):
    return object.uid

def get_content_type(object, default):
    return object.content_type

def get_workflow_state(object, default):
    if not IWorkflowAware.providedBy(object):
        return default
    return object.get_workflow_state()

def get_path(object, default):
    return resource_path(object)

def get_creators(object, default):
    return object.creators and tuple(object.creators) or ()

def get_created(object, default):
    """ The created time is stored in the catalog as unixtime.
        See the time.gmtime and calendar.timegm Python modules for more info.
        http://docs.python.org/library/calendar.html#calendar.timegm
        http://docs.python.org/library/time.html#time.gmtime
    """
    return timegm(object.created.timetuple())

def get_allowed_to_view(object, default):
    principals = principals_allowed_by_permission(object, VIEW)
    if not principals:
        # An empty value tells the catalog to match anything, whereas when
        # there are no principals with permission to view we want for there
        # to be no matches.
        principals = [NEVER_EVER_PRINCIPAL,]
    return principals

def get_searchable_text(object, default):
    """ Searchable text is basically all textfields that should be
        searchable appended to each other.
    """
    text = u''
    for index in SEARCHABLE_TEXT_INDEXES:
        res = getattr(object, index, None)
        if res:
            text += u' %s' % res
    text = text.strip()
    return text and text or default

def get_start_time(object, default):
    value = object.get_field_value('start_time', default)
    if value != default:
        return timegm(value.timetuple())
    return default

def get_end_time(object, default):
    value = object.get_field_value('end_time', default)
    if value != default:
        return timegm(value.timetuple())
    return default
