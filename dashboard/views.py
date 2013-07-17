from django.shortcuts import get_object_or_404, render_to_response
from django.utils import simplejson as json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db import transaction

from models import Gadget, Dashboard
from forms import AddGadgetForm


def json_response(message, code=200, data=None, success=True):
    msg = {
        'success': success,
        'message': message,
        'data': data or {},
        }
    return HttpResponse(content=json.dumps(msg), status=code)


def gadget_to_dict(gadget):
    return = {
        'config': gadget.get_config(),
        'id': gadget.pk,
        'auto_id': gadget.auto_id(),
        'placeholder': gadget.placeholder,
    }


def form_errors_data(form):
    return {
        'errors': map(unicode, form.errors),
        }


@login_required
@transaction.commit_on_success
def add_gadget(request):
    if request.method=='POST':
        form = AddGadgetForm(request.user, data=request.POST)
        if form.is_valid():
            gadget = form.save()
            return json_response('OK', data=gadget_to_dict(gadget))
        else:
            return json_response('Validation error', success=False,
                    data=form_errors_data(form))
    return json_response('invalid request', success=False, code=400)


@login_required
@transaction.commit_on_success
def save_gadget_config(request, object_id):
    """
    ajax gadget save

    data config in json must be posted
    """

    if request.method == 'POST':
        gadget = get_object_or_404(Gadget, pk=object_id,
                       dashboard=request.user.dashboard)
        gadget_obj = gadget.gadget_instance()
        form = gadget_obj.config_form(gadget, data=request.POST)
        if form.is_valid():
            form.save()
            return json_response(
                    message='OK',
                    data=gadget.get_config(),
                    )
        else:
            return json_response(message=u'Validation error', success=False,
                    data=form_errors_data(form))

    return json_response(message='Invalid call', success=False, code=500)


@login_required
@transaction.commit_on_success
def update_placeholder(request, placeholder):
    if request.method=='POST':
        gadgets = request.POST.getlist('items[]')
        for pos, gadget_id in enumerate(gadgets):
            try:
                gadget = Gadget.objects.get(pk=gadget_id,
                    dashboard=request.user.dashboard)
                gadget.position = pos
                gadget.placeholder = placeholder
                gadget.save()
            except Gadget.DoesNotExist, e:
                pass
        return json_response('ok')
    else:
        return json_response('invalid method call', 400)


@login_required
@transaction.commit_on_success
def remove_gadget(request, object_id):
    if not request.method=='POST':
        return json_response('invalid method call', 400)

    gadget = get_object_or_404(Gadget, pk=object_id,
                   dashboard=request.user.dashboard)

    gadget_obj = gadget.gadget_instance()
    if hasattr(gadget_obj, 'cleanup'):
        gadget_obj.cleanup(request.user, gadget.get_config())

    if not gadget.gadget_instance().removable:
        return json_response('widget is not removable', 400)

    gadget.delete()

    gadgets = Gadget.objects.filter(
        placeholder=gadget.placeholder,
        dashboard=gadget.dashboard)

    for pos, gadget in enumerate(gadgets):
        gadget.position = pos
        gadget.save()

    return json_response('ok')


@login_required
@transaction.commit_on_success
def move_gadget(request, object_id):
    """
    ajax gadget move

    POST args:
        position    - new position
        placeholder - name of placeholder
    """

    if request.method == 'POST':
        gadget = get_object_or_404(Gadget, pk=object_id,
                       dashboard=request.user.dashboard)
        placeholder = request.POST.get('placeholder')
        position = request.POST.get('position')
        gadget.placeholder = placeholder
        gadget.position = position
        Gadget.objects.move_to(gadget, position)
        return json_response(message='OK')
    return json_response(message='Invalid call', code=500)


@login_required
def show_placeholder(request, placeholder,
        template_name='dashboard/placeholder.html'):
    gadgets = request.user.dashboard.gadget_set.placeholder(placeholder)
    ctx = {
        'dashboard': request.user.dashboard,
        'gadgets': gadgets,
    }

    return render_to_response(template_name, RequestContext(request, ctx))


@login_required
def show_widget(request, object_id):
    gadget = get_object_or_404(Gadget, dashboard=request.user.dashboard,
                               pk=object_id)
    return HttpResponse(content=gadget.render_gadget(request))


@login_required
def dashboard(request):
    try:
        dashboard = request.user.dashboard
    except Dashboard.DoesNotExist:
        dashboard = Dashboard.objects.create_default(request.user)
    ctx = {
        'dashboard': request.user.dashboard,
    }
    return render_to_response(dashboard.layout,
                              RequestContext(request, ctx))


