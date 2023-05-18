# Do not edit this file; it was automatically generated.

from nidaqmx.utils import unflatten_channel_string
from nidaqmx.constants import (
    RegenerationMode, ResolutionType, WaitMode, WriteRelativeTo)


class OutStream:
    """
    Exposes an output data stream on a DAQmx task.

    The output data stream be used to control writing behavior and can be
    used in conjunction with writer classes to write samples to an
    NI-DAQmx task.
    """
    def __init__(self, task, interpreter):
        self._task = task
        self._handle = task._handle
        self._interpreter = interpreter
        self._auto_start = False
        self._timeout = 10.0

        super().__init__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self._handle == other._handle and
                    self._auto_start == other._auto_start and
                    self._timeout == other._timeout)
        return False

    def __hash__(self):
        return self._interpreter.hash_task_handle(self._handle) ^ hash(self._auto_start, self._timeout)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f'OutStream(task={self._task.name})'

    @property
    def auto_start(self):
        """
        bool: Specifies if the "write" method automatically starts the
            stream's owning task if you did not explicitly start it
            with the DAQmx Start Task method.
        """
        return self._auto_start

    @auto_start.setter
    def auto_start(self, val):
        self._auto_start = val

    @auto_start.deleter
    def auto_start(self):
        self._auto_start = False

    @property
    def timeout(self):
        """
        float: Specifies the amount of time in seconds to wait for
            the write method to write all samples. NI-DAQmx performs a
            timeout check only if the write method must wait before it
            writes data. The write method returns an error if the time
            elapses. The default timeout is 10 seconds. If you set
            "timeout" to nidaqmx.WAIT_INFINITELY, the write method
            waits indefinitely. If you set timeout to 0, the write
            method tries once to write the submitted samples. If the
            write method could not write all the submitted samples, it
            returns an error and the number of samples successfully
            written in the number of samples written per channel
            output.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, val):
        self._timeout = val

    @timeout.deleter
    def timeout(self):
        self._timeout = 10.0

    @property
    def accessory_insertion_or_removal_detected(self):
        """
        bool: Indicates if any devices in the task detected the
            insertion or removal of an accessory since the task started.
            Reading this property clears the accessory change status for
            all channels in the task. You must read this property before
            you read **devs_with_inserted_or_removed_accessories**.
            Otherwise, you will receive an error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x3053)
        return val

    @property
    def curr_write_pos(self):
        """
        int: Indicates the position in the buffer of the next sample to
            generate. This value is identical for all channels in the
            task.
        """

        val = self._interpreter.get_write_attribute_uint64(self._handle, 0x1458)
        return val

    @property
    def devs_with_inserted_or_removed_accessories(self):
        """
        List[str]: Indicates the names of any devices that detected the
            insertion or removal of an accessory since the task started.
            You must read **accessory_insertion_or_removal_detected**
            before you read this property. Otherwise, you will receive
            an error.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x3054)
        return unflatten_channel_string(val)

    @property
    def do_num_booleans_per_chan(self):
        """
        int: Indicates the number of Boolean values expected per channel
            in a sample for line-based writes. This property is
            determined by the channel in the task with the most digital
            lines. If a channel has fewer lines than this number, NI-
            DAQmx ignores the extra Boolean values.
        """

        val = self._interpreter.get_write_attribute_uint32(self._handle, 0x217f)
        return val

    @property
    def external_overvoltage_chans(self):
        """
        List[str]: Indicates a list of names of any virtual channels in
            the task for which an External Overvoltage condition has
            been detected. You must read External OvervoltageChansExist
            before you read this property. Otherwise, you will receive
            an error.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x30bc)
        return unflatten_channel_string(val)

    @property
    def external_overvoltage_chans_exist(self):
        """
        bool: Indicates if the device(s) detected an External
            Overvoltage condition for any channel in the task. Reading
            this property clears the External Overvoltage status for all
            channels in the task. You must read this property before you
            read External OvervoltageChans. Otherwise, you will receive
            an error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x30bb)
        return val

    @property
    def num_chans(self):
        """
        int: Indicates the number of channels that DAQmx Write writes to
            the task. This value is the number of channels in the task.
        """

        val = self._interpreter.get_write_attribute_uint32(self._handle, 0x217e)
        return val

    @property
    def offset(self):
        """
        int: Specifies in samples per channel an offset at which a write
            operation begins. This offset is relative to the location
            you specify with **relative_to**.
        """

        val = self._interpreter.get_write_attribute_int32(self._handle, 0x190d)
        return val

    @offset.setter
    def offset(self, val):
        self._interpreter.set_write_attribute_int32(self._handle, 0x190d, val)

    @offset.deleter
    def offset(self):
        self._interpreter.reset_write_attribute(self._handle, 0x190d)

    @property
    def open_current_loop_chans(self):
        """
        List[str]: Indicates a list of names of any virtual channels in
            the task for which the device(s) detected an open current
            loop. You must read **open_current_loop_chans_exist** before
            you read this property. Otherwise, you will receive an
            error.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x29eb)
        return unflatten_channel_string(val)

    @property
    def open_current_loop_chans_exist(self):
        """
        bool: Indicates if the device(s) detected an open current loop
            for any channel in the task. Reading this property clears
            the open current loop status for all channels in the task.
            You must read this property before you read
            **open_current_loop_chans**. Otherwise, you will receive an
            error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x29ea)
        return val

    @property
    def output_buf_size(self):
        """
        int: Specifies the number of samples the output buffer can hold
            for each channel in the task. Zero indicates to allocate no
            buffer. Use a buffer size of 0 to perform a hardware-timed
            operation without using a buffer. Setting this property
            overrides the automatic output buffer allocation that NI-
            DAQmx performs.
        """

        val = self._interpreter.get_buffer_attribute_uint32(self._handle, 0x186d)
        return val

    @output_buf_size.setter
    def output_buf_size(self, val):
        self._interpreter.set_buffer_attribute_uint32(self._handle, 0x186d, val)

    @output_buf_size.deleter
    def output_buf_size(self):
        self._interpreter.reset_buffer_attribute(self._handle, 0x186d)

    @property
    def output_onbrd_buf_size(self):
        """
        int: Specifies in samples per channel the size of the onboard
            output buffer of the device.
        """

        val = self._interpreter.get_buffer_attribute_uint32(self._handle, 0x230b)
        return val

    @output_onbrd_buf_size.setter
    def output_onbrd_buf_size(self, val):
        self._interpreter.set_buffer_attribute_uint32(self._handle, 0x230b, val)

    @output_onbrd_buf_size.deleter
    def output_onbrd_buf_size(self):
        self._interpreter.reset_buffer_attribute(self._handle, 0x230b)

    @property
    def overcurrent_chans(self):
        """
        List[str]: Indicates a list of names of any virtual channels in
            the task for which an overcurrent condition has been
            detected. You must read **overcurrent_chans_exist** before
            you read this property. Otherwise, you will receive an
            error.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x29e9)
        return unflatten_channel_string(val)

    @property
    def overcurrent_chans_exist(self):
        """
        bool: Indicates if the device(s) detected an overcurrent
            condition for any channel in the task. Reading this property
            clears the overcurrent status for all channels in the task.
            You must read this property before you read
            **overcurrent_chans**. Otherwise, you will receive an error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x29e8)
        return val

    @property
    def overloaded_chans(self):
        """
        List[str]: Indicates a list of names of any overloaded virtual
            channels in the task. You must read
            **overloaded_chans_exist** before you read this property.
            Otherwise, you will receive an error.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x3085)
        return unflatten_channel_string(val)

    @property
    def overloaded_chans_exist(self):
        """
        bool: Indicates if the device(s) detected an overload in any
            virtual channel in the task. Reading this property clears
            the overload status for all channels in the task. You must
            read this property before you read **overloaded_chans**.
            Otherwise, you will receive an error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x3084)
        return val

    @property
    def overtemperature_chans(self):
        """
        List[str]: Indicates a list of names of any overtemperature
            virtual channels. You must read
            **overtemperature_chans_exist** before you read this
            property. Otherwise, you will receive an error. The list of
            names may be empty if the device cannot determine the source
            of the overtemperature.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x3083)
        return unflatten_channel_string(val)

    @property
    def overtemperature_chans_exist(self):
        """
        bool: Indicates if the device(s) detected an overtemperature
            condition in any virtual channel in the task. Reading this
            property clears the overtemperature status for all channels
            in the task. You must read this property before you read
            **overtemperature_chans**. Otherwise, you will receive an
            error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x2a84)
        return val

    @property
    def power_supply_fault_chans(self):
        """
        List[str]: Indicates a list of names of any virtual channels in
            the task that have a power supply fault. You must read
            **power_supply_fault_chans_exist** before you read this
            property. Otherwise, you will receive an error.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x29ed)
        return unflatten_channel_string(val)

    @property
    def power_supply_fault_chans_exist(self):
        """
        bool: Indicates if the device(s) detected a power supply fault
            for any channel in the task. Reading this property clears
            the power supply fault status for all channels in the task.
            You must read this property before you read
            **power_supply_fault_chans**. Otherwise, you will receive an
            error.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x29ec)
        return val

    @property
    def raw_data_width(self):
        """
        int: Indicates in bytes the required size of a raw sample to
            write to the task.
        """

        val = self._interpreter.get_write_attribute_uint32(self._handle, 0x217d)
        return val

    @property
    def regen_mode(self):
        """
        :class:`nidaqmx.constants.RegenerationMode`: Specifies whether
            to allow NI-DAQmx to generate the same data multiple times.
        """

        val = self._interpreter.get_write_attribute_int32(self._handle, 0x1453)
        return RegenerationMode(val)

    @regen_mode.setter
    def regen_mode(self, val):
        val = val.value
        self._interpreter.set_write_attribute_int32(self._handle, 0x1453, val)

    @regen_mode.deleter
    def regen_mode(self):
        self._interpreter.reset_write_attribute(self._handle, 0x1453)

    @property
    def relative_to(self):
        """
        :class:`nidaqmx.constants.WriteRelativeTo`: Specifies the point
            in the buffer at which to write data. If you also specify an
            offset with **offset**, the write operation begins at that
            offset relative to this point you select with this property.
        """

        val = self._interpreter.get_write_attribute_int32(self._handle, 0x190c)
        return WriteRelativeTo(val)

    @relative_to.setter
    def relative_to(self, val):
        val = val.value
        self._interpreter.set_write_attribute_int32(self._handle, 0x190c, val)

    @relative_to.deleter
    def relative_to(self):
        self._interpreter.reset_write_attribute(self._handle, 0x190c)

    @property
    def sleep_time(self):
        """
        float: Specifies in seconds the amount of time to sleep after
            checking for available buffer space if **wait_mode** is
            **WaitMode2.SLEEP**.
        """

        val = self._interpreter.get_write_attribute_double(self._handle, 0x22b2)
        return val

    @sleep_time.setter
    def sleep_time(self, val):
        self._interpreter.set_write_attribute_double(self._handle, 0x22b2, val)

    @sleep_time.deleter
    def sleep_time(self):
        self._interpreter.reset_write_attribute(self._handle, 0x22b2)

    @property
    def space_avail(self):
        """
        int: Indicates in samples per channel the amount of available
            space in the buffer.
        """

        val = self._interpreter.get_write_attribute_uint32(self._handle, 0x1460)
        return val

    @property
    def sync_unlocked_chans(self):
        """
        List[str]: Indicates the channels from devices in an unlocked
            target.
        """

        val = self._interpreter.get_write_attribute_string(self._handle, 0x3140)
        return unflatten_channel_string(val)

    @property
    def sync_unlocked_chans_exist(self):
        """
        bool: Indicates whether the target is currently locked to the
            grand master. Devices may report PLL Unlock either during
            acquisition or after acquisition.
        """

        val = self._interpreter.get_write_attribute_bool(self._handle, 0x313f)
        return val

    @property
    def total_samp_per_chan_generated(self):
        """
        int: Indicates the total number of samples generated by each
            channel in the task. This value is identical for all
            channels in the task.
        """

        val = self._interpreter.get_write_attribute_uint64(self._handle, 0x192b)
        return val

    @property
    def wait_mode(self):
        """
        :class:`nidaqmx.constants.WaitMode`: Specifies how DAQmx Write
            waits for space to become available in the buffer.
        """

        val = self._interpreter.get_write_attribute_int32(self._handle, 0x22b1)
        return WaitMode(val)

    @wait_mode.setter
    def wait_mode(self, val):
        val = val.value
        self._interpreter.set_write_attribute_int32(self._handle, 0x22b1, val)

    @wait_mode.deleter
    def wait_mode(self):
        self._interpreter.reset_write_attribute(self._handle, 0x22b1)

    def write(self, numpy_array):
        """
        Writes raw samples to the task or virtual channels you specify.

        The number of samples per channel to write is determined using the
        following equation:

        number_of_samples_per_channel = math.floor(
            numpy_array_size_in_bytes / (
                number_of_channels_to_write * raw_sample_size_in_bytes))

        Raw samples constitute the internal representation of samples in a
        device, read directly from the device or buffer without scaling or
        reordering. The native format of a device can be an 8-, 16-, or 32-bit
        integer, signed or unsigned.

        If you use a different integer size than the native format of the
        device, one integer can contain multiple samples or one sample can
        stretch across multiple integers. For example, if you use 32-bit
        integers, but the device uses 8-bit samples, one integer contains up to
        four samples. If you use 8-bit integers, but the device uses 16-bit
        samples, a sample might require two integers. This behavior varies from
        device to device. Refer to your device documentation for more
        information.

        NI-DAQmx does not separate raw data into channels. It accepts data in
        an interleaved or non-interleaved 1D array, depending on the raw
        ordering of the device. Refer to your device documentation for more
        information.

        If the task uses on-demand timing, this method returns only after the
        device generates all samples. On-demand is the default timing type if
        you do not use the timing property on the task to configure a sample
        timing type. If the task uses any timing type other than on-demand,
        this method returns immediately and does not wait for the device to
        generate all samples. Your application must determine if the task is
        done to ensure that the device generated all samples.

        Use the "auto_start" property on the stream to specify if this method
        automatically starts the stream's owning task if you did not explicitly
        start it with the DAQmx Start Task method.

        Use the "timeout" property on the stream to specify the amount of
        time in seconds to wait for the method to write all samples. NI-DAQmx
        performs a timeout check only if the method must wait before it writes
        data. This method returns an error if the time elapses. The default
        timeout is 10 seconds. If you set timeout to nidaqmx.WAIT_INFINITELY,
        the method waits indefinitely. If you set timeout to 0, the method
        tries once to write the submitted samples. If the method could not
        write all the submitted samples, it returns an error and the number of
        samples successfully written.

        Args:
            numpy_array (numpy.ndarray): Specifies a 1D NumPy array that
                contains the raw samples to write to the task.
        Returns:
            int:

            Specifies the actual number of samples per channel successfully
            written to the buffer.
        """
        channels_to_write = self._task.channels
        number_of_channels = len(channels_to_write.channel_names)

        channels_to_write.ao_resolution_units = ResolutionType.BITS

        number_of_samples_per_channel, _ = divmod(
            numpy_array.nbytes, (
                number_of_channels * int(channels_to_write.ao_resolution) // 8))

        return self._interpreter.write_raw(
            self._handle, number_of_samples_per_channel,
            self.auto_start, self.timeout, numpy_array)
