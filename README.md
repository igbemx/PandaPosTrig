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

The functionality of the present tango device is based on SoftiMAX specific PandABox layout that is available in the current repo.

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

##### Attributes

The PandaPosTrig device expose the following attributes:

|   Attribute  |    Type   |  R/W | Unit | Purpose                                      |
|:------------ |:----------|:---- |:---- |:-------------------------------------------- |
| AbsX         | DevDouble | R/W  | µm   | Absolute sample X position                   |
| AbsY         | DevDouble | R/W  | µm   | Absolute sample Y position                   |
| AbsXOffset   | DevDouble | R/W  | µm   | Sample X position offset                     |
| AbsXOffset   | DevDouble | R/W  | µm   | Sample X position offset                     |
| TrigAxis     | TrigAxis  | R/W  |      | Selection of the axis for triggering         |
| TrigXPos     | DevDouble | R/W  | µm   | Position for the X axis triggering           |
| TrigYPos     | DevDouble | R/W  | µm   | Position for the Y axis triggering           |
| TrigState    | DevString | R/W  | µm   | Status of the PandABox concerning triggering |
