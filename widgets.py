#-*- coding: utf-8 -*-
from itertools import chain
from babel import Locale
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import to_locale
from phonenumber_field.phonenumber import to_python

from phonenumbers.data import _COUNTRY_CODE_TO_REGION_CODE

from django.utils import translation
from django.forms import Select, TextInput
from django.forms.util import flatatt
from django.forms.widgets import MultiWidget
from phonenumber_field.phonenumber import PhoneNumber


class PhonePrefixSelect(Select):
    initial = None

    def __init__(self, initial):
        choices = [('', '---------')]
        locale = Locale(to_locale(translation.get_language()))
        for prefix, values in _COUNTRY_CODE_TO_REGION_CODE.iteritems():
            prefix = '+%d' % prefix
            if initial and initial in values:
                self.initial = prefix
            for country_code in values:
                country_name = locale.territories.get(country_code)
                if country_name:
                    # noinspection PyTypeChecker
                    choices.append(
                        (prefix, (
                            u'%s' % prefix,
                            {
                                u'data-image': u'/static/country-dropdown/images/msdropdown/icons/blank.gif',
                                u'data-imagecss': u'flag {0}'.format(country_code.lower()),
                                u'data-title': force_unicode(country_name),
                            }
                        )))
        super(PhonePrefixSelect, self).__init__(choices=sorted(choices, key=lambda item: item[1]))

    # def render(self, name, value, *args, **kwargs):
    #     return super(PhonePrefixSelect, self).render(name, value or self.initial, *args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = self.initial
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select%s class="countries">' % flatatt(final_attrs)]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append(u'</select>')
        return mark_safe(u'\n'.join(output))

    def render_option(self, selected_choices, option_value, option_label, attrs=None):
        option_value = force_unicode(option_value)
        attrs = u''.join([u' {0}="{1}"'.format(x, y) for x, y in attrs.iteritems()]) if attrs else u''
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<option value="%s"%s%s>%s</option>' % (
            escape(option_value), attrs, selected_html,
            conditional_escape(force_unicode(option_label)))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(self.render_option(selected_choices, option_value, option_label[0], option_label[1]))
            else:
                output.append(self.render_option(selected_choices, option_value, option_label))
        return u'\n'.join(output)

    class Media:
        css = {
            'all': ('country-dropdown/css/msdropdown/dd.css', 'country-dropdown/css/msdropdown/flags.css')
        }
        js = ('country-dropdown/js/jquery/jquery-1.8.2.min.js',
              'country-dropdown/js/msdropdown/jquery.dd.min.js',
              'country-dropdown/js/msdropdown/ready.js')


class PhoneNumberPrefixWidget(MultiWidget):
    """
    A Widget that splits phone number input into:
    - a country select box for phone prefix
    - an input for local phone number
    """

    def __init__(self, attrs=None, initial=None):
        widgets = (PhonePrefixSelect(initial), TextInput(),)
        super(PhoneNumberPrefixWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            if isinstance(value, unicode):
                value = to_python(value)
            if isinstance(value, PhoneNumber):
                return u'+%d' % value.country_code, value.national_number
        return [None, None]

    def value_from_datadict(self, data, files, name):
        values = super(PhoneNumberPrefixWidget, self).value_from_datadict(data, files, name)
        if values[1]:
            return u'%s%s' % tuple(values)
        else:
            return None, None