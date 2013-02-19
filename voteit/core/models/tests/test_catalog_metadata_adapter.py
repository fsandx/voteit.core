import unittest

from pyramid import testing
from pyramid.traversal import resource_path
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.site import SiteRoot
from voteit.core.models.interfaces import ICatalogMetadata


class CatalogMetadataTests(unittest.TestCase):
    """ Testcase for CatalogMetadata adapter. The metadata is covered in the catalog tests.
    """
    def setUp(self):
        self.config = testing.setUp()
        self.root = SiteRoot() #Contains a catalog

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.catalog import CatalogMetadata
        return CatalogMetadata

    def _make_obj(self):
        from voteit.core.models.base_content import BaseContent
        return self._cut(BaseContent())

    def test_class_implementation(self):
        verifyClass(ICatalogMetadata, self._cut)

    def test_obj_implementation(self):
        obj = self._make_obj()
        verifyObject(ICatalogMetadata, obj)

    def test_add_and_get_metadata(self):
        obj = self._make_obj()
        
        dm = self.root.catalog.document_map
        
        doc_id = dm.add(resource_path(obj.context))
        dm.add_metadata(doc_id, obj())
        
        metadata = dm.get_metadata(doc_id)
        self.assertEqual(metadata['title'], obj.context.title)
        self.assertEqual(metadata['created'], obj.context.created)
        
    def test_returned_metadata(self):
        obj = self._make_obj()
        result = obj()
        
        self.assertEqual(result['title'], obj.context.title)
        self.assertEqual(result['created'], obj.context.created)
