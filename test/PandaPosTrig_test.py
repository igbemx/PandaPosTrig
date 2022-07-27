#########################################################################################
# -*- coding: utf-8 -*-
#
# This file is part of the PandaPosTrig project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.
#########################################################################################
"""Contain the tests for the Panda position based triggering for STXM FPGA.."""

# Path
import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

# Imports
import pytest
from mock import MagicMock

from PyTango import DevState

# PROTECTED REGION ID(PandaPosTrig.test_additional_imports) ENABLED START #
# PROTECTED REGION END #    //  PandaPosTrig.test_additional_imports


# Device test case
@pytest.mark.usefixtures("tango_context", "initialize_device")
# PROTECTED REGION ID(PandaPosTrig.test_PandaPosTrig_decorators) ENABLED START #
# PROTECTED REGION END #    //  PandaPosTrig.test_PandaPosTrig_decorators
class TestPandaPosTrig(object):
    """Test case for packet generation."""

    properties = {
        }

    @classmethod
    def mocking(cls):
        """Mock external libraries."""
        # Example : Mock numpy
        # cls.numpy = PandaPosTrig.numpy = MagicMock()
        # PROTECTED REGION ID(PandaPosTrig.test_mocking) ENABLED START #
        # PROTECTED REGION END #    //  PandaPosTrig.test_mocking

    def test_properties(self, tango_context):
        # Test the properties
        # PROTECTED REGION ID(PandaPosTrig.test_properties) ENABLED START #
        # PROTECTED REGION END #    //  PandaPosTrig.test_properties
        pass

    # PROTECTED REGION ID(PandaPosTrig.test_State_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_State_decorators
    def test_State(self, tango_context):
        """Test for State"""
        # PROTECTED REGION ID(PandaPosTrig.test_State) ENABLED START #
        assert tango_context.device.State() == DevState.UNKNOWN
        # PROTECTED REGION END #    //  PandaPosTrig.test_State

    # PROTECTED REGION ID(PandaPosTrig.test_Status_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_Status_decorators
    def test_Status(self, tango_context):
        """Test for Status"""
        # PROTECTED REGION ID(PandaPosTrig.test_Status) ENABLED START #
        assert tango_context.device.Status() == "The device is in UNKNOWN state."
        # PROTECTED REGION END #    //  PandaPosTrig.test_Status

    # PROTECTED REGION ID(PandaPosTrig.test_Arm_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_Arm_decorators
    def test_Arm(self, tango_context):
        """Test for Arm"""
        # PROTECTED REGION ID(PandaPosTrig.test_Arm) ENABLED START #
        assert tango_context.device.Arm() == None
        # PROTECTED REGION END #    //  PandaPosTrig.test_Arm

    # PROTECTED REGION ID(PandaPosTrig.test_Disarm_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_Disarm_decorators
    def test_Disarm(self, tango_context):
        """Test for Disarm"""
        # PROTECTED REGION ID(PandaPosTrig.test_Disarm) ENABLED START #
        assert tango_context.device.Disarm() == None
        # PROTECTED REGION END #    //  PandaPosTrig.test_Disarm


    # PROTECTED REGION ID(PandaPosTrig.test_AbsX_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_AbsX_decorators
    def test_AbsX(self, tango_context):
        """Test for AbsX"""
        # PROTECTED REGION ID(PandaPosTrig.test_AbsX) ENABLED START #
        assert tango_context.device.AbsX == 0
        # PROTECTED REGION END #    //  PandaPosTrig.test_AbsX

    # PROTECTED REGION ID(PandaPosTrig.test_AbsY_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_AbsY_decorators
    def test_AbsY(self, tango_context):
        """Test for AbsY"""
        # PROTECTED REGION ID(PandaPosTrig.test_AbsY) ENABLED START #
        assert tango_context.device.AbsY == 0
        # PROTECTED REGION END #    //  PandaPosTrig.test_AbsY

    # PROTECTED REGION ID(PandaPosTrig.test_TrigXPos_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_TrigXPos_decorators
    def test_TrigXPos(self, tango_context):
        """Test for TrigXPos"""
        # PROTECTED REGION ID(PandaPosTrig.test_TrigXPos) ENABLED START #
        assert tango_context.device.TrigXPos == 0
        # PROTECTED REGION END #    //  PandaPosTrig.test_TrigXPos

    # PROTECTED REGION ID(PandaPosTrig.test_TrigYPos_decorators) ENABLED START #
    # PROTECTED REGION END #    //  PandaPosTrig.test_TrigYPos_decorators
    def test_TrigYPos(self, tango_context):
        """Test for TrigYPos"""
        # PROTECTED REGION ID(PandaPosTrig.test_TrigYPos) ENABLED START #
        assert tango_context.device.TrigYPos == 0.0
        # PROTECTED REGION END #    //  PandaPosTrig.test_TrigYPos


