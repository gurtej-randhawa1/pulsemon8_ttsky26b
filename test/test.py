import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ReadOnly, Timer


def make_uio(signal=0, enable=0, clear=0, freeze_on_match=0):
    return (
        (signal << 4)
        | (enable << 5)
        | (clear << 6)
        | (freeze_on_match << 7)
    )


def read_status(dut):
    status = int(dut.uio_out.value)
    return {
        "edge_detect": (status >> 0) & 1,
        "overflow": (status >> 1) & 1,
        "match_status": (status >> 2) & 1,
        "freeze_status": (status >> 3) & 1,
    }


async def send_pulse(dut, enable=1, freeze_on_match=0):
    dut.uio_in.value = make_uio(
        signal=0,
        enable=enable,
        freeze_on_match=freeze_on_match,
    )
    await ClockCycles(dut.clk, 1)

    dut.uio_in.value = make_uio(
        signal=1,
        enable=enable,
        freeze_on_match=freeze_on_match,
    )
    await ClockCycles (dut.clk, 1)
    # Allow gate-level outputs to settle after the clock edge.
    await Timer(7, unit="ns")
    await ReadOnly()
    await Timer(1, unit="ns")


@cocotb.test()
async def test_project(dut):
    # Start clock
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # -------------------------------------------------------------------------
    # TEST 1: Reset behavior
    # -------------------------------------------------------------------------

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    await ReadOnly()

    count = int(dut.uo_out.value)
    dut._log.info("TEST 1: Reset behavior")
    dut._log.info(f"After reset: count={count}")
    assert count == 0

    await Timer(3, unit="ns")

    # -------------------------------------------------------------------------
    # TEST 2: Counting and overflow behavior
    # -------------------------------------------------------------------------
    dut._log.info("\nTEST 2: Counting and overflow behavior")

    overflow_pulses = 301
    expected_count = overflow_pulses % 256

    for _ in range(overflow_pulses):
        await send_pulse(dut)

    count = int(dut.uo_out.value)
    status = read_status(dut)

    dut._log.info(
        "After overflow test: "
        f"pulses={overflow_pulses}, "
        f"count={count}, "
        f"expected_count={expected_count}, "
        f"overflow={status['overflow']}"
    )

    assert count == expected_count
    assert status["overflow"] == 1

    # -------------------------------------------------------------------------
    # TEST 3: Rising-edge detection
    # -------------------------------------------------------------------------
    dut._log.info("\nTEST 3: Rising-edge detection")

    # Bring signal low first.
    dut.uio_in.value = make_uio(signal=0, enable=1)
    await ClockCycles(dut.clk, 1)

    # Drive signal high and check edge_detect before prev_signal updates.
    dut.uio_in.value = make_uio(signal=1, enable=1)
    await Timer(7, unit="ns")
    await ReadOnly()

    status = read_status(dut)
    dut._log.info(f"During rising edge: edge_detect={status['edge_detect']}")
    assert status["edge_detect"] == 1

    await ClockCycles(dut.clk, 1)
    await Timer(7, unit = "ns")
    await ReadOnly()
    await Timer(1, unit="ns")

    # -------------------------------------------------------------------------
    # TEST 4: Runtime clear behavior
    # -------------------------------------------------------------------------
    dut._log.info("\nTEST 4: Runtime clear behavior")

    dut.uio_in.value = make_uio(clear=1)
    await ClockCycles(dut.clk, 1)
    await Timer (7, unit="ns")
    await ReadOnly()

    count = int(dut.uo_out.value)
    status = read_status(dut)

    dut._log.info(
        "After clear: "
        f"count={count}, "
        f"overflow={status['overflow']}, "
        f"freeze_status={status['freeze_status']}"
    )

    assert count == 0
    assert status["overflow"] == 0
    assert status["freeze_status"] == 0

    await Timer(1, unit="ns")

    # -------------------------------------------------------------------------
    # TEST 5: Compare-match and freeze-on-match behavior
    # -------------------------------------------------------------------------
    dut._log.info("\nTEST 5: Compare-match and freeze-on-match behavior")

    compare_value = 89
    dut.ui_in.value = compare_value

    for _ in range(compare_value):
        await send_pulse(dut, freeze_on_match=1)

    await Timer (7, unit="ns")
    await ReadOnly()

    count = int(dut.uo_out.value)
    status = read_status(dut)

    await Timer (1, unit="ns")

    dut._log.info(
        "After freeze test: "
        f"count={count}, "
        f"compare_value={compare_value}, "
        f"match_status={status['match_status']}, "
        f"freeze_status={status['freeze_status']}\n"
    )

    assert count == compare_value
    assert status["match_status"] == 1
    assert status["freeze_status"] == 1
    

    
