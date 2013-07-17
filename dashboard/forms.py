from django import forms
from models import Gadget, COLOR_CHOICES
from django.db.models import Max
from collections import defaultdict
import dashboard


class GadgetsLibrary(object):
    def __init__(self, force_all=False):
        self.force_all = force_all

    def __iter__(self):
        if self.force_all:
            gadgets =[(v.group, k, v.name) for k,v in \
                dashboard.all_gadgets.gadgets.items()]
        else:
            gadgets =[(v.group, k, v.name) for k,v in \
                dashboard.all_gadgets.gadgets.items() if v.gadget.selectable]
        groups = defaultdict(list)
        for group, key, name in gadgets:
            groups[group].append((key,name))
        [g.sort(key=lambda x: x[1]) for g in groups.values()]
        groups = sorted(groups.items(), key=lambda x: x[0])
        return iter(groups)


class ColorSelect(forms.Select):
    pass


class AddGadgetForm(forms.ModelForm):
    placeholder = forms.CharField(widget=forms.HiddenInput)
    import_path = forms.ChoiceField(choices=[],
            label=u'Gadżet')
    position = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Gadget
        fields = ('placeholder', 'import_path', 'position')

    def __init__(self, user, *args, **kw):
        super(AddGadgetForm, self).__init__(*args, **kw)
        self.user = user
        self.fields['import_path'].choices = GadgetsLibrary()

    def save(self, commit=True):
        instance = super(AddGadgetForm, self).save(commit=False)
        instance.dashboard = self.user.dashboard

        gadget = instance.gadget_instance()
        config = dict(gadget.defaults)
        if hasattr(gadget, 'initialize'):
            config.update(gadget.initialize(self.user, instance.get_config()))
        instance.set_config(config)

        if commit:
            if not self.cleaned_data['position'] is None:
                if instance.position:
                    Gadget.objects.move_to(instance, self.cleaned_data['position'])
                else:
                    instance.position = self.cleaned_data['position']
            elif not instance.position:
                new_pos = Gadget.objects.filter(dashboard=instance.dashboard,
                       placeholder=instance.placeholder).aggregate(
                    Max('position'))['position__max'] or 0
                instance.position = new_pos+1
            else:
                new_pos = instance.position or 0
            instance.save()
        return instance


class AdminAddGadgetForm(AddGadgetForm):
    class Meta:
        model = Gadget
        fields = ('placeholder', 'import_path', 'position')
    def __init__(self, *args, **kw):
        super(AdminAddGadgetForm, self).__init__(*args, **kw)
        self.fields['import_path'].choices = GadgetsLibrary(force_all=True)


class ConfigForm(forms.Form):
    title = forms.CharField()
    color = forms.ChoiceField(choices=COLOR_CHOICES, widget=ColorSelect)

    def __init__(self, gadget=None, *args, **kw):
        self.gadget = gadget
        if gadget:
            kw['initial'] = kw.get('initial', {})
            kw['initial'].update(gadget.get_config() or {})
        super(ConfigForm, self).__init__(*args, **kw)

    def save(self, commit=True):
        config = self.gadget.get_config()
        config.update(self.cleaned_data)
        self.gadget.set_config(config)
        if commit:
            self.gadget.save()

