# Panda position based triggering for STXM FPGA.

## tangods-softimax-pandapostrig


Tango device for the PandABox position-based triggering at SoftiMAX.


____________________________________________________________________________

##### Repository


- Provides: `tangods-softimax-pandapostrig`

- Requeriments: `PyTango >= 8.1.6`


____________________________________________________________________________

##### Device

This tango device interacts with the PandABox at SoftiMAX and provides position-based triggering capability.

Currently, it is used in combination with the BlackFreq acquisition FPGA controller. It sends a position-based trigger signal to the BlackFreq controller at the beginning of each new scanning line. In turn, the BlackFreq controller is responsible for the time-based acquisition of the signal from the 0D detectors, such as PMT and photo-diode.

The functionality of the present tango device is based on a SoftiMAX specific PandABox [layout](../config/panda_layout.png) that is called _pos_trig_stxm_ctrl_, which is also saved as a json file [here](../config/pos_trig_stxm_ctrl.json) and can be copied without any modification to the PandABox _/opt/share/designs/PANDA_ folder.

____________________________________________________________________________

##### Properties

The PandaPosTrig device requires the following property:

| Property  | Purpose                 | Default value        |
| --------- | ----------------------- | -------------------- |
| PandaHost | PandABox hostname or IP | "b-softimax-panda-0" |
| PandaPort | PandABox control port   | 8888                 |
| AbsXSign  | Sign of the X-axis      | -1                   |
| AbsYSign  | Sign of the Y-axis      | 1                    |

____________________________________________________________________________

##### Attributes used for time-based triggering

The PandaPosTrig device exposes the following attributes:

|   Attribute  |    Type   |  R/W | Unit | Purpose                                      |
|:------------ |:----------|:---- |:---- |:-------------------------------------------- |
| AbsX         | DevDouble | R/W  | µm   | Absolute sample X position                   |
| AbsY         | DevDouble | R/W  | µm   | Absolute sample Y position                   |
| AbsXOffset   | DevDouble | R/W  | µm   | Sample X position offset                     |
| AbsXOffset   | DevDouble | R/W  | µm   | Sample X position offset                     |
| TrigAxis     | TrigAxis  | R/W  |      | Selection of the axis for triggering         |
| TrigXPos     | DevDouble | R/W  | µm   | Position for the X axis triggering           |
| TrigYPos     | DevDouble | R/W  | µm   | Position for the Y axis triggering           |
| TrigState    | DevString |  R   | µm   | Status of the PandABox concerning triggering |

____________________________________________________________________________

##### Attributes used for time-based triggering

The PandaPosTrig device exposes the following attributes:

|   Attribute  |    Type   |  R/W | Unit | Purpose                                      |
|:------------ |:----------|:---- |:---- |:-------------------------------------------- |
| DetDwell     | DevDouble | R/W  | ms   | 0D detectors dwell time                      |

____________________________________________________________________________

##### Commands

The PandaPosTrig device exposes the following commands:

| Command        | Action                                                               |
| ---------------| -------------------------------------------------------------------- |
| Init           | Re-initialize the device                                             |
| ArmSingle      | Prepare PCAP block according to the given TrigXPos or TrigYPos value |
| Disarm         | Disarm the PCAP block                                                |
| SetXTrigToCurr | Set TrigXPos to the current absolute position value                  |
| SetYTrigToCurr | Set TrigYPos to the current absolute position value                  |
| ZeroAbs        | Sets absolute positions to zero by reseting increm. enc. block       |


____________________________________________________________________________

##### State Machine

The PandaPosTrig device has the following states:
| State          | Event                                                                      |
| ---------------| -------------------------------------------------------------------------- |
| ON             | The device is On and can be prepared for triggering                        |
| FAULT          | The device has failed to execute the last command or communication is lost |

____________________________________________________________________________

##### Description of the FPGA blocks used in the layout

| Block name      | Description                                                                       |
| ----------------| ----------------------------------------------------------------------------------|
| INENC1          | Y Position input from the Attocube interferometer A&B output                      |
| INENC2          | X Position input from the Attocube interferometer A&B output                      |
| OUTENC1, OUTENC2| Respective X and Y A&B outputs that go to the ACS position oscilloscope           |
| PCOMP1          | Block that produces a position-based pulse to mark the beginning of a new line    |
| PULSE1          | Triggers and gates position and 0D detecetors signals acquisition                 |
| TTLIN5          | PMT signal input                                                                  |
| TTLIN6          | Photodiode signal input                                                           |
| TTLOUT9         | Output of the position-based trigger that goes to BlackFreq                       |
| PULSE2          | Produces time-based pulses to trigger 0D det. acquisition for monitoring purposes |
| CLOCK1          | Produces pulse with 1 µs period for precise internal time stamping                |
| COUNTER1        | Measures the duration of the pulse produced by PULSE2 in µs                       |

