import colander
import deform

from voteit.core.validators import deferred_at_enabled_text
from voteit.core import VoteITMF as _
from betahaus.pyracont.decorators import schema_factory


@schema_factory('ProposalSchema')
class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"I propose:"),
                                validator=deferred_at_enabled_text,
                                widget=deform.widget.TextAreaWidget(rows=3, cols=40),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               widget=deform.widget.HiddenWidget(),
                               missing=u'')
