from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from django.template.loader import render_to_string


class GadgetDoesNotExist(ValueError):
    pass


class GadgetInfo(object):
    def __init__(self, gadget):
        self.gadget = gadget
        self.name = getattr(gadget, 'title', gadget.__class__.__name__)
        self.group = getattr(gadget, 'group')
        self.description = gadget.__class__.__doc__


def make_gadget_key(gadget_class):
    return '%s.%s' % (gadget_class.__module__, gadget_class.__name__)


class Library(object):
    """
    A gadgets library
    """

    def __init__(self):
        self.gadgets = {}

    def register_gadget(self, gadget_class):
        gadget = gadget_class()
        self.gadgets[make_gadget_key(gadget_class)] = GadgetInfo(gadget)

    def unregister_gadget(self, gadget_class):
        self.gadgets.pop(make_gadget_key(gadget_class))

    def add_gadget_info(self, gadgetinfo):
        self.gadgets[make_gadget_key(gadgetinfo.gadget.__class__)] = gadgetinfo

    def get_by_class(self, gadget_class):
        return self.gadgets[make_gadget_key(gadget_class)]

    # decorators (shortcuts)

    def gadget(self, gadget_class):
        self.register_gadget(gadget_class)
        return gadget_class



all_gadgets = Library()


def autodiscover():
    from django.conf import settings
    for app in settings.INSTALLED_APPS:
        try:
            mod = __import__(app, {}, {}, ['gadgets'])
            gadgets = getattr(mod, 'gadgets', None)
            if gadgets and hasattr(gadgets, 'register'):
                for gadgetinfo in gadgets.register.gadgets.values():
                    all_gadgets.add_gadget_info(gadgetinfo)
        except ImportError:
            pass


def load_gadget(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
        try:
            cls = getattr(mod, attr)
        except AttributeError:
            raise ImportError('Widget class %s not found in module %s'
                                    % (attr, mod))
    except ImportError:
        raise ImportError(
            'Module %s does not exist. Cannot load widget %s' % (module, attr))

    return cls



class Gadget(object):
    """
    main gadget class
    """
    title = 'Untitled'
    defaults = []

    editable = False
    moveable = True
    removable = True
    collapsible = False
    selectable = True
    refresh = None


    template_name = 'dashboard/gadget.html'
    edit_template_name = 'dashboard/gadget_edit.html'

    def get_title(self, user, config):
        return config.get('title', self.title)

    def get_context(self, user, config):
        return {}

    def render(self, gadget, request):
        from django.conf import settings
        config = gadget.get_config()
        user = gadget.dashboard.owner
        allconfig = dict(self.defaults)
        allconfig.update(config)

        ctx = self.get_context(user, allconfig)
        ctx.update({
            'MEDIA_URL': settings.MEDIA_URL,
            'request': request, # fix me someday
            'user': request.user, # fix me someday
            'model': gadget,
            'gadget': self,
            'widget': {
                'id': gadget.auto_id(),
                'title': self.get_title(user, allconfig),
                'config': allconfig,
                'editable': self.editable,
                'removable': self.removable,
                'moveable': self.moveable,
                },
            })
        return render_to_string(self.template_name, ctx)

    def render_edit_form(self, gadget):
        if not self.config_form or not self.editable:
            return ''

        initial = dict(self.defaults)
        initial['title'] = self.get_title(gadget.dashboard.owner, gadget.get_config())

        ctx = {
            'form': self.config_form(gadget, initial=initial),
            }

        return render_to_string(self.edit_template_name, ctx)


    @property
    def config_form(self):
        from forms import ConfigForm
        return ConfigForm
