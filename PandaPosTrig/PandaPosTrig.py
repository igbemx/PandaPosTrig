# -*- coding: utf-8 -*-
#
# This file is part of the PandaPosTrig project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

""" Panda position based triggering for STXM FPGA.

"""

# PyTango imports
import tango
from tango import DebugIt
from tango.server import run
from tango.server import Device
from tango.server import attribute, command
from tango.server import device_property
from tango import AttrQuality, DispLevel, DevState
from tango import AttrWriteType, PipeWriteType
import enum
# Additional import
# PROTECTED REGION ID(PandaPosTrig.additionnal_import) ENABLED START #
import socket
import time
import threading
from pyparsing import Word, Literal, nums, ParseException
import logging as log
log.basicConfig(level=log.DEBUG)


class SoftwareTrigger(object):
    def __init__(self, state):
        self.lock = threading.Lock()
        self.state = state

    @property
    def state(self):
        with self.lock:
            return self._state

    @state.setter
    def state(self, state):
        with self.lock:
            self._state = state

# PROTECTED REGION END #    //  PandaPosTrig.additionnal_import

__all__ = ["PandaPosTrig", "main"]


class DetTrigSrc(enum.IntEnum):
    """Python enumerated type for DetTrigSrc attribute."""
    INTERNAL = 0
    EXT_SOFT = 1


class TrigAxis(enum.IntEnum):
    """Python enumerated type for TrigAxis attribute."""
    X = 0
    Y = 1


class PandaPosTrig(Device):
    """

    **Properties:**

    - Device Property
        PandaHost
            - Type:'DevString'
        PandaPort
            - Type:'DevShort'
        AbsXSign
            - Type:'DevShort'
        AbsYSign
            - Type:'DevShort'
        PandaDataPort
            - Type:'DevShort'
    """
    # PROTECTED REGION ID(PandaPosTrig.class_variable) ENABLED START #
    def _get_panda_ctrl_socket(self):
        """
        Returns PandABox control socket.
        """
        try:
            panda_ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            panda_ctrl_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            panda_ctrl_sock.settimeout(1)
            panda_ctrl_sock.connect((self.PandaHost, self.PandaPort))
            return panda_ctrl_sock
        except Exception as e:
            print('Problem connecting to the PandABox control port: ', e)
    
    def _get_panda_data_socket(self):
        """
        Returns PandABox data socket.
        """
        try:
            panda_data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            panda_data_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            panda_data_sock.settimeout(None)
            panda_data_sock.connect((self.PandaHost, self.PandaDataPort))
            return panda_data_sock
        except Exception as e:
            print('Problem connecting to the PandaBox data port: ', e)

    def _panda_block_write(self, argin, ctrl_socket=None):
        """
        Sends 'argin' value to the panda control soket and receives the output.
        """
        try:
            if not ctrl_socket:
                panda_ctrl_sock = self._get_panda_ctrl_socket()
            else:
                panda_ctrl_sock = ctrl_socket
            panda_ctrl_sock.sendall(bytes(argin + '\n', 'ascii'))
            argout = panda_ctrl_sock.recv(4096).decode()
            #log.debug(f'argout in _panda_block_write is: {argout}')
            return argout
        except Exception as e:
            log.debug('A problem when sending a query to the PandaBox occured: {e}')
        finally:
            if not ctrl_socket:
                log.debug(f'Closing panda_ctrl_sock, {panda_ctrl_sock}')

    def _read_data_port(self, argin='', data_socket=None):
        """
        Receives the data socket output.
        """
        try:
            if not data_socket:
                panda_data_sock = self._get_panda_data_socket()
            else:
                panda_data_sock = data_socket
            if argin == '':
                pass
            else:
                log.debug(f'argin in _read_data_port is: {argin}')
                panda_data_sock.sendall(bytes(argin+'\n', 'ascii'))
            argout = panda_data_sock.recv(4096).decode()
            log.debug(f'argout in _read_data_port is: {argout}')
            return argout
        except Exception as e:
            log.debug(f'A problem when reading the PandaBox data port occured: {e}')
        finally:
            if not data_socket:
                log.debug(f'Closing panda_data_sock, {panda_data_sock}')

    def _enable_panda_block(self, name, ctrl_socket):
        """
        Enables the selected panda block.
        """
        resp = self._panda_block_write(f'{name}.ENABLE=ONE', ctrl_socket=ctrl_socket)
        log.debug(f'{name}.ENABLE=ONE, resp: {resp}')

    def _disable_panda_block(self, name, ctrl_socket):
        """
        Disables the selected panda block.
        """
        resp = self._panda_block_write(f'{name}.ENABLE=ZERO', ctrl_socket=ctrl_socket)
        log.debug(f'{name}.ENABLE=ZERO, resp: {resp}')

    def _arm_pos_capt(self, ctrl_socket):
        """
        Armes the PCAP panda block.
        """
        resp = self._panda_block_write(f'*PCAP.ARM=', ctrl_socket=ctrl_socket)
        log.debug(f'*PCAP.ARM=, resp: {resp}')

    def _disarm_pos_capt(self, ctrl_socket):
        """
        Disarms the PCAP panda block.
        """
        resp = self._panda_block_write(f'*PCAP.DISARM=', ctrl_socket=ctrl_socket)
        log.debug(f'*PCAP.DISARM=, resp: {resp}')

    def _read_abs_pos(self, ctrl_socket):
        """ Reads incremental encoder FPGA blocks directly via the control socket """
        try:
            abs_x = self._panda_block_write('INENC1.VAL?',
                                                    ctrl_socket=ctrl_socket)
            abs_y = self._panda_block_write('INENC2.VAL?',
                                                    ctrl_socket=ctrl_socket)

            _, abs_x = abs_x.split('=')
            _, abs_y = abs_y.split('=')

            return (int(abs_x), int(abs_y))
        except Exception as e:
            log.debug(f'A problem in _read_abs_pos occured: {e}')

    def _sel_trig_axis(self, axis=TrigAxis.Y, ctrl_socket=None):
        """
        Connects the right encoder input module to the PCOMP module for triggering according to
        the selected axis.
        """
        try:
            if axis == TrigAxis.X:
                resp = self._panda_block_write(
                                                'PCOMP1.INP=INENC1.VAL',
                                                ctrl_socket=ctrl_socket
                                                )
                log.debug(f'PCOMP1.INP=INENC1.VAL, resp: {resp}')
            elif axis == TrigAxis.Y:
                resp = self._panda_block_write(
                                                'PCOMP1.INP=INENC2.VAL',
                                                ctrl_socket=ctrl_socket
                                                )
                log.debug(f'PCOMP1.INP=INENC2.VAL, resp: {resp}')
        except Exception as e:
            log.debug(f'A problem in _sel_trig_axis occured: {e}')

    def _arm_axis(self, ctrl_socket=None):
        """
        Sequentially disables and enables the choosen axis, which arms the selected axis for triggering.
        """
        try:
            self._disable_panda_block('PCOMP1', ctrl_socket=ctrl_socket)
            self._enable_panda_block('PCOMP1', ctrl_socket=ctrl_socket)
        except Exception as e:
            log.debug(f'A problem in _arm_axis occured: {e}')

    def _det_time_pulse_switch(self, enable, ctrl_socket):
        """
        Switches the ENABLE/DISABLE state of the PULSE1 block.
        """
        if enable:
            self._enable_panda_block('PULSE1', ctrl_socket=ctrl_socket)
        else:
            self._disable_panda_block('PULSE1', ctrl_socket=ctrl_socket)

    def _prepare_pcomp(self,
                        pre_start,
                        start,
                        width=20,
                        step=21,
                        pulses=1,
                        direction=1,
                        pcomp_name='PCOMP1',
                        ctrl_socket=None):
        ''' Function prepares the panda PCOMP block.
            PRE_START: how far from START position should be before waiting for START
            WIDTH: defines the width of the pulse in position counts at the input
            STEP: defines the difference between the subsequent triggeres (if needed), should be at least width+1
        '''
        if direction == 1:
            pcmp_dir = 'Positive'  # 'Positive'
        elif direction == -1:
            pcmp_dir = 'Negative'  # 'Negative'
        else:
            pcmp_dir = 'Either'  # 'Either'

        send_parameters = {"PRE_START": int(pre_start),
                            "START": int(start),
                            "WIDTH": int(width),
                            "STEP": int(step),
                            "PULSES": int(pulses),
                            "DIR": pcmp_dir}
        try:
            for parameter in send_parameters.items():
                field_name, value = parameter
                field = pcomp_name + '.' + field_name
                resp = self._panda_block_write(f'{field}={value}',
                                        ctrl_socket=ctrl_socket)
                log.debug(f'The {field}={value} has been sent, response: {resp}')
        except Exception as e:
            print(e)

    def _set_axis_trig(self, trig_pos, axis=TrigAxis.Y, axis_sign=1, ctrl_socket=None):
        """
        Sets the PCOMP blocks parameters according to the requested
        position and axis.
        """
        start = int(trig_pos * 1000) * axis_sign # convert to nm
        pcomp_name = 'PCOMP1'
        self._prepare_pcomp(
                        pre_start=100,
                        start=start,
                        width=20,
                        step=21,
                        pulses=1,
                        direction=axis_sign,
                        pcomp_name=pcomp_name,
                        ctrl_socket=ctrl_socket)

    def _set_time_pulse_block(self, ctrl_socket):
        # Setting the number of pulses
        resp = self._panda_block_write(f'PULSE1.PULSES={self.__det_time_pulse_n}', ctrl_socket=ctrl_socket)
        log.debug(f'PULSE1.PULSES={self.__det_time_pulse_n}, resp: {resp}')
        # Setting the pulse width in ms
        resp = self._panda_block_write(f'PULSE1.WIDTH={self.__det_time_pulse_width}', ctrl_socket=ctrl_socket)
        log.debug(f'PULSE1.WIDTH={self.__det_time_pulse_width}, resp: {resp}')
        # Setting the pulse step in ms
        resp = self._panda_block_write(f'PULSE1.STEP={self.__det_time_pulse_step}', ctrl_socket=ctrl_socket)
        log.debug(f'PULSE1.STEP={self.__det_time_pulse_step}, resp: {resp}')

    def _read_zerod_counters(self, ctrl_socket):
        try:
            resp_buff = None
            resp_buff = self._panda_block_write('PULSE2.TRIG=ONE',
                                                    ctrl_socket=ctrl_socket)
            time.sleep(self.__det_dwell/1000)
            resp_buff = self._panda_block_write('PULSE2.TRIG=ZERO',
                                                    ctrl_socket=ctrl_socket)

            counter5 = self._panda_block_write('COUNTER5.OUT?',
                                                    ctrl_socket=ctrl_socket)
            counter6 = self._panda_block_write('COUNTER6.OUT?',
                                                    ctrl_socket=ctrl_socket)

            _, ret_PD = counter5.split('=')
            _, ret_PMT = counter6.split('=')

            return (int(ret_PD), int(ret_PMT))
        except Exception as e:
            log.debug(f'A problem in _read_zerod_counters ocuured: {e}')

    def _zerod_det_read(self, ctrl_socket, trigger=None, ph_diode_var=None, pmt_var=None):
        log.debug(f'Started _zerod_det_read thread')
        try:
            while True:
                if self.__det_trig_src == DetTrigSrc.INTERNAL:
                    ret_PD, ret_PMT = self._read_zerod_counters(ctrl_socket)
                    self.__int_ph_diode = ret_PD
                    self.__int_pmt = ret_PMT
                    #log.debug(f'Detector readings: {self.__int_ph_diode}, {self.__int_pmt}')
                elif self.__det_trig_src == DetTrigSrc.EXT_SOFT:
                    if trigger.state:
                        self.set_state(DevState.RUNNING)
                        start_time = time.time()
                        ret_PD, ret_PMT = self._read_zerod_counters(ctrl_socket)
                        self.__int_ph_diode = ret_PD
                        self.__int_pmt = ret_PMT
                        if self.get_state() not in [
                                                    DevState.MOVING,
                                                    DevState.FAULT,
                                                    DevState.OFF]:
                            log.debug('Switching from RUNNING to ON state after EXT_SOFT trigger.')
                            self.set_state(DevState.ON)
                        self.push_change_event("DetOut", (
                                                        self.__det_trig_cntr,
                                                        self.__int_ph_diode,
                                                        self.__int_pmt))
                        self.__det_trig_cntr += 1
                        trigger.state = False
                        log.debug(f'The EXT_SOFT triggered measurement took: {time.time()-start_time}s')
                    else:
                        continue

        except Exception as e:
            log.debug(f'There is a problem in _zerod_det_read(): {e} ')
        finally:
            log.debug('Closing the _zerod_det_read thread..')

    def _set_det_dwell(self, value, ctrl_socket):
        # Sets detector dwell in ms
        resp = self._panda_block_write(f'PULSE2.WIDTH={value}', ctrl_socket=ctrl_socket)
        log.debug(f'PULSE2.WIDTH={value}, resp: {resp}')

    def _panda_dataline_read(self, data_socket):
        while True:    
            try:
                self._read_data_port('NO_HEADER', data_socket)
                panda_line_read_finished = False
                log.debug('Inside _panda_dataline_read')
                while not panda_line_read_finished:
                    repl = self._read_data_port(data_socket=data_socket)
                    repl = repl.strip()
                    print(repl)
                    resp = repl.strip().split('\n')
                    first_line, *second_line = resp
                    try:
                        res = self.panda_line_repl.parseString(repl)
                        print('Result is:', res)
                    except ValueError as val_err:
                        print('Value conversion error during panda reply parsing: ', val_err)
                    except ParseException as pe:
                        print('An error in async_panda_line_read(), cannot parse the input', pe)

                    if isinstance(res[0], int) and isinstance(res[5], int):
                        log.debug('Data line received: ', res)
                        # self._last_acq_x_array.append(res[0])
                        # self._last_acq_y_array.append(res[1])
                        # self._last_acq_delta_t_array.append(res[2])
                        # self._last_acq_diode_array.append(res[3])
                        # self._last_acq_pmt_array.append(res[4])
                        # self._last_acq_ret_cnt_array.append(res[5])
                    elif res[0] == 'END':
                            #self._number_of_acquired_points = int(first_line[1])
                            log.debug('END message on the data port.')
                            panda_line_read_finished = True
                    else:
                        print('Not an array element: ', res)
            except Exception as e:
                log.debug('A problem within _panda_dataline_read(): ', e)
            finally:
                log.debug('Exiting the _panda_dataline_read()')

    def read_attr_hardware(self, data):
        """Method always executed to read the hardware."""
        abs_x, abs_y = self._read_abs_pos(self.panda_ctrl_sock)
        self.__abs_x, self.__abs_y = abs_x*self.AbsXSign/1000, abs_y*self.AbsYSign/1000 # all values in microns

    # PROTECTED REGION END #    //  PandaPosTrig.class_variable

    # -----------------
    # Device Properties
    # -----------------

    PandaHost = device_property(
        dtype='DevString',
        default_value="b-softimax-panda-0"
    )

    PandaPort = device_property(
        dtype='DevShort',
        default_value=8888
    )

    AbsXSign = device_property(
        dtype='DevShort',
        default_value=1
    )

    AbsYSign = device_property(
        dtype='DevShort',
        default_value=1
    )

    PandaDataPort = device_property(
        dtype='DevShort',
        default_value=8889
    )

    # ----------
    # Attributes
    # ----------

    AbsX = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="microns",
        doc="Absolute sample X position",
    )

    AbsY = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="microns",
        doc="Absolute sample Y position",
    )

    AbsXOffset = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="microns",
        memorized=True,
    )

    AbsYOffset = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="microns",
        memorized=True,
    )

    TrigAxis = attribute(
        dtype=TrigAxis,
        access=AttrWriteType.READ_WRITE,
        doc="Selection of triggerring axis",
    )

    TrigXPos = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="microns",
        doc="Position for X axis triggerring",
    )

    TrigYPos = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="microns",
        doc="Position for Y axis triggerring",
    )

    TrigState = attribute(
        dtype='DevString',
    )

    DataPortBusy = attribute(
        dtype='DevBoolean',
    )

    DetDwell = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="ms",
    )

    DetPosCapt = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
    )

    DetTimePulseN = attribute(
        dtype='DevULong64',
        access=AttrWriteType.READ_WRITE,
    )

    DetTimePulseStep = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
    )

    DetTimePulseWidth = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
    )

    DetTimePulses = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
    )

    DetTrig = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
    )

    DetTrigCntr = attribute(
        dtype='DevLong64',
        access=AttrWriteType.READ_WRITE,
    )

    DetTrigSrc = attribute(
        dtype=DetTrigSrc,
        access=AttrWriteType.READ_WRITE,
    )

    IntPMT = attribute(
        dtype='DevULong64',
    )

    IntPhDiode = attribute(
        dtype='DevULong64',
    )

    DetOut = attribute(
        dtype=('DevULong64',),
        max_dim_x=3,
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialises the attributes and properties of the PandaPosTrig."""
        Device.init_device(self)
        self.set_change_event("DetOut", True, False)
        # PROTECTED REGION ID(PandaPosTrig.init_device) ENABLED START #
        self.__abs_x = 0
        self.__abs_y = 0
        self.__abs_x_offset = 0
        self.__abs_y_offset = 0
        self.__int_ph_diode = 0
        self.__int_pmt = 0
        self.__trig_x_pos = 0.0
        self.__trig_y_pos = 0.0
        self.__trig_state = 'NEVER ARMED'
        self.__trig_axis = TrigAxis.Y
        self.__det_trig_src = DetTrigSrc.INTERNAL
        self.__det_trig = SoftwareTrigger(False)
        self.__det_dwell = 10  # Detector dwell = 10 ms
        self.__det_trig_cntr = 0
        self.__det_time_pulse_n = 1
        self.__det_time_pulse_width = 1
        self.__det_time_pulse_step = 1
        self.__det_pos_capt = False

        # Parsing expressions

        num_value = Word(nums+'-').setParseAction(lambda val: int(val[0]))
        panda_OK_reply = Literal('OK')
        panda_END_reply = Literal('END')
        pcap_point_values = (num_value + num_value + num_value + num_value + num_value + num_value)
        self.panda_line_repl = panda_OK_reply | pcap_point_values | panda_END_reply

        try:
            self.panda_ctrl_sock = self._get_panda_ctrl_socket()
            self.panda_det_ctrl_sock = self._get_panda_ctrl_socket()
            self.panda_det_data_sock = self._get_panda_data_socket()
            self._sel_trig_axis(axis=self.__trig_axis,
                                ctrl_socket=self.panda_ctrl_sock)
        except Exception as e:
            log.debug(f'Problem obtaining panda_ctrl_sock: {e}')

        # Setting the detector dwell in the hardware
        try:
            self._set_det_dwell(self.__det_dwell, self.panda_ctrl_sock)
        except Exception as e:
            log.debug(f'Problem setting the initial detector dwell: {e}')

        try:
            self.__det_time_pulses = False
            self._det_time_pulse_switch(self.__det_time_pulses, self.panda_ctrl_sock)
        except Exception as e:
            log.debug(f'Problem with the initialization of time-based block: {e}')

        try:
            self.t_zerod_acq = threading.Thread(target=self._zerod_det_read,
                                                args=(self.panda_det_ctrl_sock,
                                                self.__det_trig))
            self.t_zerod_acq.setDaemon(True)
            self.t_zerod_acq.start()
        except Exception as e:
            print(e)

        try:
            self.t_data_acq = threading.Thread(
                                            target=self._panda_dataline_read,
                                            args=(self.panda_det_data_sock,)
            )
            self.t_data_acq.setDaemon(True)
            self.t_data_acq.start()
        except Exception as e:
            print(e)
        self.set_state(DevState.ON)
        # PROTECTED REGION END #    //  PandaPosTrig.init_device

    def always_executed_hook(self):
        """Method always executed before any TANGO command is executed."""
        # PROTECTED REGION ID(PandaPosTrig.always_executed_hook) ENABLED START #
        # PROTECTED REGION END #    //  PandaPosTrig.always_executed_hook

    def delete_device(self):
        """Hook to delete resources allocated in init_device.

        This method allows for any memory or other resources allocated in the
        init_device method to be released.  This method is called by the device
        destructor and by the device Init command.
        """
        # PROTECTED REGION ID(PandaPosTrig.delete_device) ENABLED START #
        # PROTECTED REGION END #    //  PandaPosTrig.delete_device
    # ------------------
    # Attributes methods
    # ------------------

    def read_AbsX(self):
        # PROTECTED REGION ID(PandaPosTrig.AbsX_read) ENABLED START #
        """Return the AbsX attribute."""
        return self.__abs_x - self.__abs_x_offset
        # PROTECTED REGION END #    //  PandaPosTrig.AbsX_read

    def write_AbsX(self, value):
        # PROTECTED REGION ID(PandaPosTrig.AbsX_write) ENABLED START #
        """Set the AbsX attribute."""
        self.__abs_x_offset = self.__abs_x - value
        # PROTECTED REGION END #    //  PandaPosTrig.AbsX_write

    def read_AbsXOffset(self):
        # PROTECTED REGION ID(PandaPosTrig.AbsXOffset_read) ENABLED START #
        """Return the AbsXOffset attribute."""
        return self.__abs_x_offset
        # PROTECTED REGION END #    //  PandaPosTrig.AbsXOffset_read

    def write_AbsXOffset(self, value):
        # PROTECTED REGION ID(PandaPosTrig.AbsXOffset_write) ENABLED START #
        """Set the AbsXOffset attribute."""
        self.__abs_x_offset = value
        # PROTECTED REGION END #    //  PandaPosTrig.AbsXOffset_write

    def read_AbsY(self):
        # PROTECTED REGION ID(PandaPosTrig.AbsY_read) ENABLED START #
        """Return the AbsY attribute."""
        return self.__abs_y - self.__abs_y_offset
        # PROTECTED REGION END #    //  PandaPosTrig.AbsY_read

    def write_AbsY(self, value):
        # PROTECTED REGION ID(PandaPosTrig.AbsY_write) ENABLED START #
        """Set the AbsY attribute."""
        self.__abs_y_offset = self.__abs_y - value
        # PROTECTED REGION END #    //  PandaPosTrig.AbsY_write

    def read_AbsYOffset(self):
        # PROTECTED REGION ID(PandaPosTrig.AbsYOffset_read) ENABLED START #
        """Return the AbsYOffset attribute."""
        return self.__abs_y_offset
        # PROTECTED REGION END #    //  PandaPosTrig.AbsYOffset_read

    def write_AbsYOffset(self, value):
        # PROTECTED REGION ID(PandaPosTrig.AbsYOffset_write) ENABLED START #
        """Set the AbsYOffset attribute."""
        self.__abs_y_offset = value
        # PROTECTED REGION END #    //  PandaPosTrig.AbsYOffset_write

    def read_DataPortBusy(self):
        # PROTECTED REGION ID(PandaPosTrig.DataPortBusy_read) ENABLED START #
        """Return the DataPortBusy attribute."""
        return self.__data_port_busy
        # PROTECTED REGION END #    //  PandaPosTrig.DataPortBusy_read

    def read_DetDwell(self):
        # PROTECTED REGION ID(PandaPosTrig.DetDwell_read) ENABLED START #
        """Return the DetDwell attribute."""
        return self.__det_dwell
        # PROTECTED REGION END #    //  PandaPosTrig.DetDwell_read

    def write_DetDwell(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetDwell_write) ENABLED START #
        """Set the DetDwell attribute."""
        self.__det_dwell = value
        self._set_det_dwell(self.__det_dwell, self.panda_ctrl_sock)
        # PROTECTED REGION END #    //  PandaPosTrig.DetDwell_write

    def read_DetPosCapt(self):
        # PROTECTED REGION ID(PandaPosTrig.DetPosCapt_read) ENABLED START #
        """Return the DetPosCapt attribute."""
        return self.__det_pos_capt
        # PROTECTED REGION END #    //  PandaPosTrig.DetPosCapt_read

    def write_DetPosCapt(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetPosCapt_write) ENABLED START #
        """Set the DetPosCapt attribute."""
        self.__det_pos_capt = value
        if self.__det_pos_capt:
            self._arm_pos_capt(ctrl_socket=self.panda_ctrl_sock)
        else:
            self._disarm_pos_capt(ctrl_socket=self.panda_ctrl_sock)
        # PROTECTED REGION END #    //  PandaPosTrig.DetPosCapt_write

    def read_DetTimePulseN(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulseN_read) ENABLED START #
        """Return the DetTimePulseN attribute."""
        return self.__det_time_pulse_n
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulseN_read

    def write_DetTimePulseN(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulseN_write) ENABLED START #
        """Set the DetTimePulseN attribute."""
        self.__det_time_pulse_n = value
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulseN_write

    def read_DetTimePulseStep(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulseStep_read) ENABLED START #
        """Return the DetTimePulseStep attribute."""
        return self.__det_time_pulse_step
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulseStep_read

    def write_DetTimePulseStep(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulseStep_write) ENABLED START #
        """Set the DetTimePulseStep attribute."""
        self.__det_time_pulse_step = value
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulseStep_write

    def read_DetTimePulseWidth(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulseWidth_read) ENABLED START #
        """Return the DetTimePulseWidth attribute."""
        return self.__det_time_pulse_width
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulseWidth_read

    def write_DetTimePulseWidth(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulseWidth_write) ENABLED START #
        """Set the DetTimePulseWidth attribute."""
        self.__det_time_pulse_width = value
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulseWidth_write

    def read_DetTimePulses(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulses_read) ENABLED START #
        """Return the DetTimePulses attribute."""
        return self.__det_time_pulses
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulses_read

    def write_DetTimePulses(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTimePulses_write) ENABLED START #
        """Set the DetTimePulses attribute."""
        self._det_time_pulse_switch(value, self.panda_ctrl_sock)
        self.__det_time_pulses = value
        # PROTECTED REGION END #    //  PandaPosTrig.DetTimePulses_write

    def read_DetTrig(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTrig_read) ENABLED START #
        """Return the DetTrig attribute."""
        return self.__det_trig.state
        # PROTECTED REGION END #    //  PandaPosTrig.DetTrig_read

    def write_DetTrig(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTrig_write) ENABLED START #
        """Set the DetTrig attribute."""
        self.__det_trig.state = value
        # PROTECTED REGION END #    //  PandaPosTrig.DetTrig_write

    def read_DetTrigCntr(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTrigCntr_read) ENABLED START #
        """Return the DetTrigCntr attribute."""
        return self.__det_trig_cntr
        # PROTECTED REGION END #    //  PandaPosTrig.DetTrigCntr_read

    def write_DetTrigCntr(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTrigCntr_write) ENABLED START #
        """Set the DetTrigCntr attribute."""
        self.__det_trig_cntr = value
        # PROTECTED REGION END #    //  PandaPosTrig.DetTrigCntr_write

    def read_DetTrigSrc(self):
        # PROTECTED REGION ID(PandaPosTrig.DetTrigSrc_read) ENABLED START #
        """Return the DetTrigSrc attribute."""
        return self.__det_trig_src
        # PROTECTED REGION END #    //  PandaPosTrig.DetTrigSrc_read

    def write_DetTrigSrc(self, value):
        # PROTECTED REGION ID(PandaPosTrig.DetTrigSrc_write) ENABLED START #
        """Set the DetTrigSrc attribute."""
        self.__det_trig_src = DetTrigSrc(value)
        # PROTECTED REGION END #    //  PandaPosTrig.DetTrigSrc_write

    def read_IntPMT(self):
        # PROTECTED REGION ID(PandaPosTrig.IntPMT_read) ENABLED START #
        """Return the IntPMT attribute."""
        return self.__int_pmt
        # PROTECTED REGION END #    //  PandaPosTrig.IntPMT_read

    def read_IntPhDiode(self):
        # PROTECTED REGION ID(PandaPosTrig.IntPhDiode_read) ENABLED START #
        """Return the IntPhDiode attribute."""
        return self.__int_ph_diode
        # PROTECTED REGION END #    //  PandaPosTrig.IntPhDiode_read

    def read_TrigAxis(self):
        # PROTECTED REGION ID(PandaPosTrig.TrigAxis_read) ENABLED START #
        """Return the TrigAxis attribute."""
        return self.__trig_axis
        # PROTECTED REGION END #    //  PandaPosTrig.TrigAxis_read

    def write_TrigAxis(self, value):
        # PROTECTED REGION ID(PandaPosTrig.TrigAxis_write) ENABLED START #
        """Set the TrigAxis attribute."""
        self.__trig_axis = TrigAxis(value)
        self._sel_trig_axis(axis=self.__trig_axis, ctrl_socket=self.panda_ctrl_sock)
        if self.__trig_axis == TrigAxis.X:
            trig_pos = self.__trig_x_pos + self.__abs_x_offset
            axis_sign = self.AbsXSign
        elif self.__trig_axis == TrigAxis.Y:
            trig_pos = self.__trig_y_pos + self.__abs_y_offset
            axis_sign = self.AbsYSign
        self._set_axis_trig(trig_pos,
                            axis=self.__trig_axis,
                            axis_sign=axis_sign,
                            ctrl_socket=self.panda_ctrl_sock)
        # PROTECTED REGION END #    //  PandaPosTrig.TrigAxis_write

    def read_TrigXPos(self):
        # PROTECTED REGION ID(PandaPosTrig.TrigXPos_read) ENABLED START #
        """Return the TrigXPos attribute."""
        return self.__trig_x_pos
        # PROTECTED REGION END #    //  PandaPosTrig.TrigXPos_read

    def write_TrigXPos(self, value):
        # PROTECTED REGION ID(PandaPosTrig.TrigXPos_write) ENABLED START #
        """Set the TrigXPos attribute."""
        self.__trig_x_pos = value
        # PROTECTED REGION END #    //  PandaPosTrig.TrigXPos_write

    def read_TrigYPos(self):
        # PROTECTED REGION ID(PandaPosTrig.TrigYPos_read) ENABLED START #
        """Return the TrigYPos attribute."""
        return self.__trig_y_pos
        # PROTECTED REGION END #    //  PandaPosTrig.TrigYPos_read

    def write_TrigYPos(self, value):
        # PROTECTED REGION ID(PandaPosTrig.TrigYPos_write) ENABLED START #
        """Set the TrigYPos attribute."""
        self.__trig_y_pos = value
        # PROTECTED REGION END #    //  PandaPosTrig.TrigYPos_write

    def read_TrigState(self):
        # PROTECTED REGION ID(PandaPosTrig.TrigState_read) ENABLED START #
        """Return the TrigState attribute."""
        resp = self._panda_block_write(
                                    'PCOMP1.STATE?',
                                    ctrl_socket=self.panda_ctrl_sock
                                    )
        self.__trig_state = resp
        return self.__trig_state
        # PROTECTED REGION END #    //  PandaPosTrig.TrigState_read

    def read_DetOut(self):
        # PROTECTED REGION ID(PandaPosTrig.DetOut_read) ENABLED START #
        """Return the DetOut attribute."""
        return self.__det_out
        # PROTECTED REGION END #    //  PandaPosTrig.DetOut_read

    # --------
    # Commands
    # --------

    @command(
    )
    @DebugIt()
    def ArmSingle(self):
        # PROTECTED REGION ID(PandaPosTrig.ArmSingle) ENABLED START #
        """
        Arming the controller for the next line acquisition.

        :return:None
        """
        if self.__trig_axis == TrigAxis.X:
            trig_pos = self.__trig_x_pos + self.__abs_x_offset
            axis_sign = self.AbsXSign
        elif self.__trig_axis == TrigAxis.Y:
            trig_pos = self.__trig_y_pos + self.__abs_y_offset
            axis_sign = self.AbsYSign
        self._set_axis_trig(trig_pos,
                            axis=self.__trig_axis,
                            axis_sign=axis_sign,
                            ctrl_socket=self.panda_ctrl_sock)
        self.set_state(DevState.RUNNING)
        self._arm_axis(ctrl_socket=self.panda_ctrl_sock)
        if self.get_state() not in [DevState.FAULT, ]:
            self.set_state(DevState.ON)
        # PROTECTED REGION END #    //  PandaPosTrig.ArmSingle

    def is_ArmSingle_allowed(self):
        # PROTECTED REGION ID(PandaPosTrig.is_ArmSingle_allowed) ENABLED START #
        return self.get_state() not in [DevState.FAULT,DevState.RUNNING]
        # PROTECTED REGION END #    //  PandaPosTrig.is_ArmSingle_allowed

    @command(
    )
    @DebugIt()
    def Disarm(self):
        # PROTECTED REGION ID(PandaPosTrig.Disarm) ENABLED START #
        """

        :return:None
        """
        pass
        # PROTECTED REGION END #    //  PandaPosTrig.Disarm

    @command(
    )
    @DebugIt()
    def SetXTrigToCurr(self):
        # PROTECTED REGION ID(PandaPosTrig.SetXTrigToCurr) ENABLED START #
        """
        Setting the X trigger position to the current X position.

        :return:None
        """
        self.__trig_axis = TrigAxis.X
        self.__trig_x_pos = self.__abs_x - self.__abs_x_offset
        self._sel_trig_axis(axis=self.__trig_axis,
                            ctrl_socket=self.panda_ctrl_sock)
        self._set_axis_trig(self.__trig_x_pos + self.__abs_x_offset,
                            axis=self.__trig_axis,
                            axis_sign=self.AbsXSign,
                            ctrl_socket=self.panda_ctrl_sock)
        # PROTECTED REGION END #    //  PandaPosTrig.SetXTrigToCurr

    @command(
    )
    @DebugIt()
    def SetYTrigToCurr(self):
        # PROTECTED REGION ID(PandaPosTrig.SetYTrigToCurr) ENABLED START #
        """
        Setting the Y trigger position to the current Y position.

        :return:None
        """
        self.__trig_y_pos = self.__abs_y - self.__abs_y_offset
        self.__trig_axis = TrigAxis.Y
        self._sel_trig_axis(axis=self.__trig_axis,
                            ctrl_socket=self.panda_ctrl_sock)
        self._set_axis_trig(self.__trig_y_pos + self.__abs_y_offset,
                            axis=self.__trig_axis,
                            axis_sign=self.AbsYSign,
                            ctrl_socket=self.panda_ctrl_sock)
        # PROTECTED REGION END #    //  PandaPosTrig.SetYTrigToCurr

    @command(
    )
    @DebugIt()
    def ZeroAbs(self):
        # PROTECTED REGION ID(PandaPosTrig.ZeroAbs) ENABLED START #
        """

        :return:None
        """
        resp = self._panda_block_write(f'INENC1.RST_ON_Z=1', ctrl_socket=self.panda_ctrl_sock)
        log.debug(f'INENC1.RST_ON_Z=1, resp: {resp}')
        resp = self._panda_block_write(f'INENC2.RST_ON_Z=1', ctrl_socket=self.panda_ctrl_sock)
        log.debug(f'INENC2.RST_ON_Z=1, resp: {resp}')
        resp = self._panda_block_write(f'INENC1.RST_ON_Z=0', ctrl_socket=self.panda_ctrl_sock)
        log.debug(f'INENC1.RST_ON_Z=0, resp: {resp}')
        resp = self._panda_block_write(f'INENC2.RST_ON_Z=0', ctrl_socket=self.panda_ctrl_sock)
        log.debug(f'INENC2.RST_ON_Z=0, resp: {resp}')
        # PROTECTED REGION END #    //  PandaPosTrig.ZeroAbs

    @command(
    )
    @DebugIt()
    def SetDetTimePulseBlock(self):
        # PROTECTED REGION ID(PandaPosTrig.SetDetTimePulseBlock) ENABLED START #
        """
        Setting the detector time pulse block according to the provided number of steps, step width, and step

        :return:None
        """
        self._set_time_pulse_block(ctrl_socket=self.panda_ctrl_sock)
        # PROTECTED REGION END #    //  PandaPosTrig.SetDetTimePulseBlock

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    """Main function of the PandaPosTrig module."""
    # PROTECTED REGION ID(PandaPosTrig.main) ENABLED START #
    return run((PandaPosTrig,), args=args, **kwargs)
    # PROTECTED REGION END #    //  PandaPosTrig.main


if __name__ == '__main__':
    main()
