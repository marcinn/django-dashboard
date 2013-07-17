from djangofingers.template import Library
from dashboard.forms import AddGadgetForm

register = Library()

@register.filter
def filter_placeholder(gadgets, placeholder):
    return gadgets.filter(placeholder=placeholder)


@register.assignment_tag(takes_context=True)
def add_gadget_form(context, placeholder):
    return AddGadgetForm(context['user'], initial={'placeholder': placeholder})


@register.simple_tag
def render_edit_form(gadget, model):
    return gadget.render_edit_form(model)


@register.simple_tag
def render_gadget(request, gadget):
    return gadget.render_gadget(request)
