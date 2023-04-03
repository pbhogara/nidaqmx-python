<%
    from codegen.utilities.attribute_helpers import get_attributes, get_enums_used, transform_attributes
    from codegen.utilities.text_wrappers import wrap
    attributes = get_attributes(data, "AIChannel")
    attributes =  transform_attributes(attributes, "AIChannel")
    enums_used = get_enums_used(attributes)
%>\
# Do not edit this file; it was automatically generated.

import ctypes
import numpy
import deprecation

from nidaqmx._lib import (
    lib_importer, wrapped_ndpointer, ctypes_byte_str, c_bool32)
from nidaqmx.scale import Scale
from nidaqmx.errors import (
    check_for_error, is_string_buffer_too_small, is_array_buffer_too_small)
from nidaqmx._task_modules.channels.channel import Channel
from nidaqmx.utils import unflatten_channel_string
from nidaqmx.constants import (
    ${', '.join([c for c in enums_used]) | wrap(4, 4)})


class AIChannel(Channel):
    """
    Represents one or more analog input virtual channels and their properties.
    """
    __slots__ = []

    def __repr__(self):
        return 'AIChannel(name={0})'.format(self._name)

<%namespace name="property_template" file="/property_template.py.mako"/>\
%for attribute in attributes:
${property_template.script_property(attribute)}\
%endfor
<%namespace name="deprecated_template" file="/property_deprecated_template.py.mako"/>\
${deprecated_template.script_deprecated_property(attributes)}\