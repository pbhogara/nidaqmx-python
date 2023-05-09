<%
    from codegen.utilities.interpreter_helpers import get_interpreter_functions, get_grpc_interpreter_call_params, get_params_for_function_signature, get_interpreter_parameter_signature, get_output_params, get_response_parameters, get_compound_parameter, create_compound_parameter_request, get_input_arguments_for_compound_params, check_if_parameters_contain_read_array, get_read_array_parameters
    from codegen.utilities.function_helpers import order_function_parameters_by_optional
    from codegen.utilities.text_wrappers import wrap, docstring_wrap
    from codegen.utilities.helpers import snake_to_pascal
    functions = get_interpreter_functions(data)
%>\
# Do not edit this file; it was automatically generated.

import grpc
import typing
import warnings

from . import errors as errors
from nidaqmx._base_interpreter import BaseInterpreter
from nidaqmx._stubs import nidaqmx_pb2 as grpc_types
from nidaqmx._stubs import nidaqmx_pb2_grpc as nidaqmx_grpc
from nidaqmx._stubs import session_pb2 as session_grpc_types



class GrpcStubInterpreter(BaseInterpreter):
    '''Interpreter for interacting with a gRPC Stub class'''
    __slots__ = ['_grpc_options', '_client']


    def __init__(self, grpc_options):
        self._grpc_options = grpc_options
        self._client = nidaqmx_grpc.NiDAQmxStub(grpc_options.grpc_channel)

    def _invoke(self, func, request, metadata=None):
        try:
            response = func(request, metadata=metadata)
        except grpc.RpcError as rpc_error:
            error_message = rpc_error.details()
            error_code = None
            samps_per_chan_read = None
            samps_per_chan_written = None
            for entry in rpc_error.trailing_metadata() or []:
                if entry.key == 'ni-error':
                    try:
                        error_code = int(typing.cast(str, entry.value))
                    except ValueError:
                        error_message += f'\nError status: {entry.value}'
                elif entry.key == "ni-samps-per-chan-read":
                    try:
                        samps_per_chan_read = int(typing.cast(str, entry.value))
                    except ValueError:
                        error_message += f'\nSamples per channel read: {entry.value}'
                elif entry.key == "ni-samps-per-chan-written":
                    try:
                        samps_per_chan_written = int(typing.cast(str, entry.value))
                    except ValueError:
                        error_message += f'\nSamples per channel written: {entry.value}'
            grpc_error = rpc_error.code()
            if grpc_error == grpc.StatusCode.UNAVAILABLE:
                error_message = 'Failed to connect to server'
            elif grpc_error == grpc.StatusCode.UNIMPLEMENTED:
                error_message = (
                    'This operation is not supported by the NI gRPC Device Server being used. Upgrade NI gRPC Device Server.'
                )
            if error_code is None:
                raise errors.RpcError(grpc_error, error_message) from None
            else:
                self._raise_error(error_code, error_message, samps_per_chan_written, samps_per_chan_read)
        return response

    def _raise_error(self, error_code, error_message, samps_per_chan_written=None, samps_per_chan_read=None):
        if error_code < 0:
            if samps_per_chan_read is not None:
                raise errors.DaqReadError(error_message, error_code, samps_per_chan_read) from None
            elif samps_per_chan_written is not None:
                raise errors.DaqWriteError(error_message, error_code, samps_per_chan_written) from None
            else:
                raise errors.DaqError(error_message, error_code) from None
        elif error_code > 0:
            if not error_message:
                try:
                    error_message = self.get_error_string(error_code)
                except errors.Error:
                    error_message = 'Failed to retrieve error description.'
            warnings.warn(errors.DaqWarning(error_message, error_code))

    def _get_integer_value_from_grpc_string(self, entry_value):
        value = entry_value if isinstance(entry_value, str) else entry_value.decode('utf-8')
        error_code = None
        error_message = None
        try:
            error_code = int(value)
        except ValueError:
            error_message = f'\nError status: {value}'
        return error_code, error_message

% for func in functions:
<%
    params = get_params_for_function_signature(func, True)
    sorted_params = order_function_parameters_by_optional(params)
    parameter_signature = get_interpreter_parameter_signature(is_python_factory, sorted_params)
    output_parameters = get_output_params(func)
    compound_parameter = get_compound_parameter(func.base_parameters)
    grpc_interpreter_params = get_grpc_interpreter_call_params(func, sorted_params)
    is_read_method = check_if_parameters_contain_read_array(func.base_parameters)
    %>
    %if (len(func.function_name) + len(parameter_signature)) > 68:
    def ${func.function_name}(
            ${parameter_signature + '):' | wrap(12, 12)}
    %else:
    def ${func.function_name}(${parameter_signature}):
    %endif
    %if (compound_parameter is not None):
        ${compound_parameter.parameter_name} = []
        for index in range(len(${get_input_arguments_for_compound_params(func)[0]})):
            ${compound_parameter.parameter_name}.append(${create_compound_parameter_request(func)})
    %endif
    %if (func.is_init_method):
        metadata = (
            ('ni-api-key', self._grpc_options.api_key),
        )
    %endif
        response = self._invoke(
            self._client.${snake_to_pascal(func.function_name)},
        %if (len(func.function_name) + len(grpc_interpreter_params)) > 68:
            grpc_types.${snake_to_pascal(func.function_name)}Request(
            %if func.is_init_method:
                ${grpc_interpreter_params | wrap(16, 16)}),
            metadata=metadata)
            %else:
                ${grpc_interpreter_params + ')' | wrap(16, 16)})
            %endif
        %else:
        %if func.is_init_method:
            grpc_types.${snake_to_pascal(func.function_name)}Request(${grpc_interpreter_params + ')'},
            metadata=metadata)
        %else:
            grpc_types.${snake_to_pascal(func.function_name)}Request(${grpc_interpreter_params + ')'})
        %endif
        %endif
        %if is_read_method:
        % for param in get_read_array_parameters(func):
        ${param}[:] = response.${param}
        % endfor
        %endif
        %if len(output_parameters)  > 0:
        return ${get_response_parameters(func)}
        %endif
% endfor