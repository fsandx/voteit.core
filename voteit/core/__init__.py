from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.component import getGlobalSiteManager
from zope.component.globalregistry import provideAdapter
from zope.component.globalregistry import provideUtility
from zope.interface.verify import verifyClass

PROJECTNAME = 'voteit.core'
#Must be before all of this packages imports
VoteITMF = TranslationStringFactory(PROJECTNAME)

#voteit.core package imports
from voteit.core.security import groupfinder
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.bootstrap import bootstrap_voteit

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    zodb_uri = settings.get('zodb_uri')
    if zodb_uri is None:
        raise ValueError("No 'zodb_uri' in application configuration.")

    finder = PersistentApplicationFinder(zodb_uri, appmaker)
    def get_root(request):
        return finder(request.environ)
    globalreg = getGlobalSiteManager()
    config = Configurator(registry=globalreg)
    config.setup_registry(settings=settings,
                          root_factory=get_root,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy
                          )
    config.add_static_view('static', '%s:static' % PROJECTNAME)
    config.add_static_view('deform', 'deform:static')
    
    #config.add_translation_dirs('%s:locale/' % PROJECTNAME)

    config.scan(PROJECTNAME)
    
    #include specified poll plugins
    poll_plugins = settings.get('poll_plugins')

    if poll_plugins is not None:
        for poll_plugin in poll_plugins.strip().splitlines():
            config.include(poll_plugin)

    return config.make_wsgi_app()

def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
    return zodb_root['app_root']


def register_poll_plugin(plugin_class):
    """ Verify and register a Poll Plugin class. """
    verifyClass(IPollPlugin, plugin_class)
    provideUtility(plugin_class(), IPollPlugin, name = plugin_class.name)
