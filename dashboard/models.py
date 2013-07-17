from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import F
from django.template.loader import render_to_string
import pickle
import base64
import dashboard
import settings


COLOR_CHOICES = settings.COLOR_CHOICES


class Layout(models.Model):
    name = models.CharField(max_length=64)
    template_name = models.CharField(max_length=255)


class DefaultGadget(models.Model):
    layout = models.ForeignKey(Layout)
    import_path = models.CharField(max_length=255)
    position = models.PositiveIntegerField(db_index=True)
    placeholder = models.CharField(max_length=128, db_index=True)
    config_data = models.TextField(null=True, blank=True)

    def set_config(self, config):
        self.config_data = base64.b64encode(pickle.dumps(config))

    def get_config(self):
        return pickle.loads(base64.b64decode(self.config_data)) if self.config_data else {}


class DashboardManager(models.Manager):
    def create_default(self, user):
        from forms import AdminAddGadgetForm
        from django.forms import ValidationError
        from django.core.exceptions import ImproperlyConfigured

        try:
            default_layout = Layout.objects.get(pk=settings.DEFAULT_LAYOUT_ID)
        except Layout.DoesNotExist:
            raise ImproperlyConfigured(
                'Default dashboard layout (ID=%s) does not exist' %\
                        settings.DEFAULT_LAYOUT_ID)

        instance,created = Dashboard.objects.get_or_create(owner=user,
                defaults={'layout': default_layout})

        if created:
            for gadget in instance.defaultgadget_set.all():
                data = {
                        'placeholder': gadget.placeholder,
                        'import_path': gadget.import_path,
                        'position': gadget.position,
                        }
                form = AdminAddGadgetForm(user, data)
                if form.is_valid():
                    g = form.save()
                    gconf = g.get_config()
                    gconf.update(gadget.get_config())
                    g.set_config(gconf)
                    g.save()
                else:
                    raise forms.ValidationError('Invalid gadget data (%s)' % form.errors)
        return instance


class Dashboard(models.Model):
    owner = models.OneToOneField('auth.User')
    layout = models.ForeignKey(Layout)

    objects = DashboardManager()


class GadgetInstanceCache(object):
    def __init__(self):
        self.cache = {}

    def get(self, import_path):
        if import_path in self.cache:
            return self.cache[import_path]

        if not import_path:
            raise TypeError('Gadget class path not specified')
        try:
            cls = dashboard.load_gadget(import_path)
        except ImportError, e:
            raise dashboard.GadgetDoesNotExist('Gadget class path %s is invalid (%s)' %
                             (import_path, e))

        instance = dashboard.all_gadgets.get_by_class(cls).gadget
        self.cache[import_path] = instance
        return instance

    def clear(self):
        self.cache = {}



class GadgetManager(models.Manager):
    def move_to(self, gadget, position):
        gadget.position = position
        self.get_query_set().filter(dashboard=gadget.dashboard,
                position__gte=position).update(
                    position=F('position')+1)
        gadget.save()

    def insert_at(self, gadget, position):
        return self.move_to(gadget, position)

    def placeholder(self, placeholder):
        return self.get_query_set().filter(placeholder=placeholder)



class Gadget(models.Model):
    dashboard = models.ForeignKey(Dashboard)
    import_path = models.CharField(max_length=255)
    position = models.PositiveIntegerField(db_index=True)
    placeholder = models.CharField(max_length=128, db_index=True)
    config_data = models.TextField(null=True, blank=True)

    objects = GadgetManager()
    gadgets_instance_cache = GadgetInstanceCache()

    class Meta:
        ordering = ('position',)

    def auto_id(self):
        return 'gadget%d' % self.pk

    def set_config(self, config):
        self.config_data = base64.b64encode(pickle.dumps(config))

    def get_config(self):
        return pickle.loads(base64.b64decode(self.config_data)) if self.config_data else {}

    def gadget_instance(self):
        return Gadget.gadgets_instance_cache.get(self.import_path)

    def render_gadget(self, request,
            error_template_name='dashboard/gadget_missing.html'):
        try:
            return self.gadget_instance().render(self, request)
        except dashboard.GadgetDoesNotExist:
            ctx = {'object': self}
            return render_to_string(error_template_name, ctx)


