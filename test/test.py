import tango
import time


trigger_state = False
pmt_i = 0
ph_diode_i = 0
indx = 0


def det_out_cb(evnt):
    if evnt.attr_value.value is None:
        return
    global trigger_state
    global indx
    global pmt_i
    global ph_diode_i
    indx, pmt_i, ph_diode_i = evnt.attr_value.value.tolist()
    print('DetOut Callback.', evnt.attr_value.value.tolist())
    trigger_state = False


dev = tango.DeviceProxy('B318A-EA01/CTL/PandaPosTrig')
dev.subscribe_event("DetOut", tango.EventType.CHANGE_EVENT, det_out_cb)
dev.DetTrigCntr = 0


scan_start_time = time.time()
for l in range(100):
    print(l)
    time.sleep(0.1)
    for i in range(100):
        trigger_state = True
        dev.DetTrig = True
        start_time = time.time()
        while trigger_state:
            time.sleep(0.0001)
        stop_time = time.time() - start_time
        print('The EXT_SOFT trigger took: ', stop_time, i)
        print('Imported index is: ', indx)
        # print('The EXT_SOFT trigger took: ', stop_time, i, dev.IntPMT, dev.IntPhDiode)

scan_stop_time = time.time() - scan_start_time
print(f'scan_stop_time: {scan_stop_time}')
