"""
This is a module docstring
"""

__author__ = "Marcin Nowak"
__copyright__ = "Copyright 2013"
__license__ = "Propertiary"
__maintainer__ = "Marcin Nowak"
__email__ = "marcin.j.nowak@gmail.com"

from django.conf import settings

DEFAULT_LAYOUT_ID = getattr(settings, 'DASHBOARD_DEFAULT_LAYOUT_ID', 1)
COLOR_CHOICES = getattr(settings, 'DASHBOARD_COLOR_CHOICES', (
    ('#ff0000', 'red'),
    ('#00ff00', 'green'),
    ('#0000ff', 'blue'),
    ('#eeeeee', 'gray'),
))

