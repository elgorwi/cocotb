# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause
"""
Tests for handles
"""
import logging
import random

import cocotb
from cocotb.result import TestFailure
from cocotb.triggers import Timer

from common import assert_raises


@cocotb.test()
def test_lessthan_raises_error(dut):
    """
    Test that trying to use <= as if it were a comparison produces an error
    """
    ret = dut.stream_in_data <= 0x12
    try:
        bool(ret)
    except TypeError:
        pass
    else:
        raise TestFailure(
            "No exception was raised when confusing comparison with assignment"
        )

    # to make this a generator
    if False: yield


@cocotb.test()
def test_bad_attr(dut):
    yield cocotb.triggers.NullTrigger()
    try:
        _ = dut.stream_in_data.whoops
    except AttributeError as e:
        assert 'whoops' in str(e)
    else:
        assert False, "Expected AttributeError"


# strings are not supported on Icarus
@cocotb.test(skip=cocotb.SIM_NAME.lower().startswith("icarus"))
async def test_string_handle_takes_bytes(dut):
    dut.stream_in_string.value = b"bytes"
    await cocotb.triggers.Timer(10, 'ns')
    val = dut.stream_in_string.value
    assert isinstance(val, bytes)
    assert val == b"bytes"


async def test_delayed_assignment_still_errors(dut):
    """ Writing a bad value should fail even if the write is scheduled to happen later """

    # note: all these fail because BinaryValue.assign rejects them

    with assert_raises(ValueError):
        dut.stream_in_int.setimmediatevalue("1010 not a real binary string")
    with assert_raises(TypeError):
        dut.stream_in_int.setimmediatevalue([])

    with assert_raises(ValueError):
        dut.stream_in_int <= "1010 not a real binary string"
    with assert_raises(TypeError):
        dut.stream_in_int <= []


@cocotb.test(expect_error=cocotb.SIM_NAME in ["Icarus Verilog"])
def test_integer(dut):
    """
    Test access to integers
    """
    log = logging.getLogger("cocotb.test")
    yield Timer(10)

    for value in [0, 1, -1, 4, 2**31-1, -2**31]:
        dut.stream_in_int = value
        yield Timer(10)
        got_in = int(dut.stream_out_int)
        got_out = int(dut.stream_in_int)
        log.info("dut.stream_out_int = %d" % got_out)
        log.info("dut.stream_in_int = %d" % got_in)
        if got_in != got_out:
            raise TestFailure("stream_in_int and stream_out_int did not match")


@cocotb.test(expect_error=True)
def test_integer_out_of_range(dut):
    """
    Test out of range access to integers
    """
    log = logging.getLogger("cocotb.test")
    yield Timer(10)
    dut.stream_in_int = 2**31
    yield Timer(10)
    got_in = int(dut.stream_out_int)
    got_out = int(dut.stream_in_int)
    log.info("dut.stream_out_int = %d" % got_out)
    log.info("dut.stream_in_int = %d" % got_in)
    if got_in != got_out:
        raise TestFailure("stream_in_int and stream_out_int did not match")


@cocotb.test(expect_error=cocotb.SIM_NAME in ["Icarus Verilog"])
def test_double(dut):
    """
    Assign a random floating point value, read it back from the DUT and check
    it matches what we assigned
    """
    val = random.uniform(-1e307, 1e307)
    log = logging.getLogger("cocotb.test")
    yield Timer(1)
    log.info("Setting the value %g" % val)
    dut.stream_in_real = val
    yield Timer(1)
    yield Timer(1) # Workaround for VHPI scheduling - needs investigation
    got = float(dut.stream_out_real)
    log.info("Read back value %g" % got)
    if got != val:
        raise TestFailure("Values didn't match!")


@cocotb.test(expect_error=cocotb.SIM_NAME in ["Icarus Verilog"])
def test_double_int(dut):
    """Assign a random integer value to ensure we can write types convertible to
    int, read it back from the DUT and check it matches what we assigned.
    """
    val = random.randint(-2**31, 2**31 - 1)
    log = logging.getLogger("cocotb.test")
    yield Timer(1)
    log.info("Setting the value %i" % val)
    dut.stream_in_real <= val
    yield Timer(1)
    yield Timer(1) # Workaround for VHPI scheduling - needs investigation
    got = dut.stream_out_real
    log.info("Read back value %d" % got)
    if got != float(val):
        raise TestFailure("Values didn't match!")
