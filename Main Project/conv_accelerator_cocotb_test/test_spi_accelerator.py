import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles
import random
import os

CLK_MAIN_PERIOD_NS = 10  
SCLK_SPI_PERIOD_NS = 40  

PATCH_BYTES   = 25
WEIGHTS_BYTES = 250 
BIASES_BYTES  = 10  
RESULTS_BYTES = 10  

CMD_WRITE_WEIGHTS  = 0x01
CMD_WRITE_PATCH    = 0x02
CMD_WRITE_BIASES   = 0x03
CMD_START_PROC     = 0x10
CMD_READ_STATUS    = 0x20
CMD_READ_RESULTS   = 0x30

DATA_FILE_PATH = "./" 
PATCH_FILE   = os.path.join(DATA_FILE_PATH, "patch0.vec")
WEIGHTS_FILE = os.path.join(DATA_FILE_PATH, "weights0.mem")
BIASES_FILE  = os.path.join(DATA_FILE_PATH, "bias0.mem")
REF_FILE     = os.path.join(DATA_FILE_PATH, "ref0.vec")

MAX_STATUS_POLLS = 5000 

def read_decimal_vec_to_bytes(filename, num_bytes, byte_width=8):
    data_bytes = []
    try:
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                if i >= num_bytes: 
                    break
                val = int(line.strip())
                if not (0 <= val < (1 << byte_width)): 
                    raise ValueError(f"Value {val} out of {byte_width}-bit range in {filename}")
                data_bytes.append(val)
        if len(data_bytes) != num_bytes:
             raise ValueError(f"Expected {num_bytes} from {filename}, got {len(data_bytes)}")
        return data_bytes
    except FileNotFoundError:
        cocotb.log.error(f"Data file not found: {filename}")
        raise
    except ValueError as e:
        cocotb.log.error(f"Error processing file {filename}: {e}")
        raise

def read_hex_mem_to_bytes(filename, num_total_bytes, entry_width_bits=16):
    data_bytes = []
    bytes_per_entry = entry_width_bits // 8
    try:
        with open(filename, 'r') as f:
            for line in f:
                if len(data_bytes) >= num_total_bytes:
                    break
                hex_val_str = line.strip()
                if not hex_val_str:
                    continue
                val = int(hex_val_str, 16)
                for i in range(bytes_per_entry):
                    byte = (val >> (8 * (bytes_per_entry - 1 - i))) & 0xFF
                    data_bytes.append(byte)
        if len(data_bytes) != num_total_bytes:
            raise ValueError(f"Expected {num_total_bytes} bytes from {filename} (parsed {len(data_bytes)})")
        return data_bytes
    except FileNotFoundError:
        cocotb.log.error(f"Data file not found: {filename}")
        raise
    except ValueError as e:
        cocotb.log.error(f"Error processing file {filename}: {e}")
        raise

async def spi_transfer_byte(dut, tx_byte):
    rx_val = 0
    for i in range(8):
        dut.mosi_spi.value = (tx_byte >> (7 - i)) & 0x1 
        await FallingEdge(dut.sclk_spi)
        await RisingEdge(dut.sclk_spi)
        try: 
            if dut.miso_spi.value.is_resolvable:
                if dut.miso_spi.value.integer == 1 : 
                    rx_val |= (1 << (7-i))
        except AttributeError: 
             if dut.miso_spi.value == 1 : 
                 rx_val |= (1 << (7-i))
    await FallingEdge(dut.sclk_spi) 
    dut.mosi_spi.value = 0 
    return rx_val

async def spi_assert_cs(dut):
    await FallingEdge(dut.sclk_spi) 
    dut.cs_n_spi.value = 0
    await Timer(SCLK_SPI_PERIOD_NS // 4, units="ns") 

async def spi_deassert_cs(dut):
    await FallingEdge(dut.sclk_spi) 
    dut.cs_n_spi.value = 1
    await Timer(SCLK_SPI_PERIOD_NS, units="ns") 

async def spi_send_command(dut, command):
    dut._log.info(f"SPI: Sending command 0x{command:02X}")
    await spi_transfer_byte(dut, command)

async def spi_send_data_block(dut, data_bytes):
    dut._log.info(f"SPI: Sending {len(data_bytes)} data bytes...")
    for byte_val in data_bytes:
        await spi_transfer_byte(dut, byte_val)
    dut._log.info("SPI: Finished sending data block.")

async def spi_read_data_block(dut, num_bytes):
    dut._log.info(f"SPI: Reading {num_bytes} data bytes...")
    received_bytes = []
    for _ in range(num_bytes):
        rx_byte = await spi_transfer_byte(dut, 0xAA) 
        received_bytes.append(rx_byte)
    dut._log.info(f"SPI: Received data block: {[hex(b) for b in received_bytes]}")
    return received_bytes

async def reset_dut(dut, duration_ns):
    dut._log.info("Applying reset to DUT...")
    dut.rst_n_main.value = 1
    await Timer(CLK_MAIN_PERIOD_NS * 2, units="ns")
    dut.rst_n_main.value = 0
    await Timer(duration_ns, units="ns")
    dut.rst_n_main.value = 1
    await Timer(CLK_MAIN_PERIOD_NS * 5, units="ns") 
    dut._log.info("Reset complete.")

@cocotb.test()
async def test_accelerator_system_spi(dut):
    cocotb.start_soon(Clock(dut.clk_main, CLK_MAIN_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.sclk_spi, SCLK_SPI_PERIOD_NS, units="ns").start())

    dut.cs_n_spi.value = 1
    dut.mosi_spi.value = 0

    await reset_dut(dut, CLK_MAIN_PERIOD_NS * 5)

    dut._log.info("Loading input/reference files in testbench...")
    patch_data_tb   = read_decimal_vec_to_bytes(PATCH_FILE,   PATCH_BYTES)
    weights_data_tb = read_hex_mem_to_bytes(WEIGHTS_FILE, WEIGHTS_BYTES)
    biases_data_tb  = read_hex_mem_to_bytes(BIASES_FILE,  BIASES_BYTES)
    results_ref_tb  = read_hex_mem_to_bytes(REF_FILE,     RESULTS_BYTES)
    dut._log.info("File I/O complete.")

    start_time_ns = cocotb.utils.get_sim_time(units='ns')
    time_after_load_data_ns = 0
    time_after_start_proc_ns = 0

    dut._log.info("--- SPI: Loading Weights ---")
    await spi_assert_cs(dut)
    await spi_send_command(dut, CMD_WRITE_WEIGHTS)
    await spi_send_data_block(dut, weights_data_tb)
    await spi_deassert_cs(dut)
    await ClockCycles(dut.clk_main, 10) 

    dut._log.info("--- SPI: Loading Patch ---")
    await spi_assert_cs(dut)
    await spi_send_command(dut, CMD_WRITE_PATCH)
    await spi_send_data_block(dut, patch_data_tb)
    await spi_deassert_cs(dut)
    await ClockCycles(dut.clk_main, 10)

    dut._log.info("--- SPI: Loading Biases ---")
    await spi_assert_cs(dut)
    await spi_send_command(dut, CMD_WRITE_BIASES)
    await spi_send_data_block(dut, biases_data_tb)
    await spi_deassert_cs(dut)
    await ClockCycles(dut.clk_main, 10)
    time_after_load_data_ns = cocotb.utils.get_sim_time(units='ns')

    dut._log.info("--- SPI: Starting Processing ---")
    await spi_assert_cs(dut)
    await spi_send_command(dut, CMD_START_PROC) 
    await spi_deassert_cs(dut)
    
    await ClockCycles(dut.clk_main, 5) 
    dut._log.info(f"After CMD_START_PROC: SPI_FSM_State={int(dut.spi_fsm_current_state_debug.value)}, CMD_Reg=0x{int(dut.spi_current_cmd_reg_debug.value):02X}, Trigger_Pulse={int(dut.spi_trigger_wrapper_pulse_debug.value)}")
    time_after_start_proc_ns = cocotb.utils.get_sim_time(units='ns')

    dut._log.info("--- SPI: Polling Status ---")
    is_done = False
    for i in range(MAX_STATUS_POLLS):
        await ClockCycles(dut.clk_main, 50) 
        
        spi_state_before_poll = int(dut.spi_fsm_current_state_debug.value)
        spi_cmd_before_poll = int(dut.spi_current_cmd_reg_debug.value)
        spi_trigger_before_poll = int(dut.spi_trigger_wrapper_pulse_debug.value)

        await spi_assert_cs(dut)
        await spi_send_command(dut, CMD_READ_STATUS)
        status_byte = await spi_transfer_byte(dut, 0x00) 
        await spi_deassert_cs(dut)
        
        done_flag = (status_byte >> 1) & 0x1
        busy_flag = status_byte & 0x1
        dut._log.info(f"Poll {i+1}/{MAX_STATUS_POLLS}: Status=0x{status_byte:02X} (Done={done_flag}, Busy={busy_flag}) "
                      f"|| PrePoll_SPI_FSM_State={spi_state_before_poll}, CMD_Reg=0x{spi_cmd_before_poll:02X}, Trigger={spi_trigger_before_poll}")
        
        if done_flag:
            is_done = True
            dut._log.info("Processing complete signaled by DUT.")
            break
    
    assert is_done, f"Timeout: DUT did not assert DONE after {MAX_STATUS_POLLS} polls."
    processing_end_time_ns = cocotb.utils.get_sim_time(units='ns')

    dut._log.info("--- SPI: Reading Results ---")
    await spi_assert_cs(dut)
    await spi_send_command(dut, CMD_READ_RESULTS)
    hw_results_bytes = await spi_read_data_block(dut, RESULTS_BYTES)
    await spi_deassert_cs(dut)
    results_read_time_ns = cocotb.utils.get_sim_time(units='ns')

    dut._log.info("--- Verifying Results ---")
    errors = 0
    for i in range(RESULTS_BYTES):
        if hw_results_bytes[i] != results_ref_tb[i]:
            dut._log.error(f"Byte {i}: HW=0x{hw_results_bytes[i]:02X}, REF=0x{results_ref_tb[i]:02X}")
            errors += 1
    if errors == 0:
        dut._log.info("***** TEST PASSED: All result bytes match the reference. *****")
    else:
        dut._log.error(f"***** TEST FAILED: {errors} mismatches. *****")
    assert errors == 0

    dut._log.info("--- SPI BENCHMARK SUMMARY (Approximate) ---")
    total_system_time_ns = results_read_time_ns - start_time_ns
    dut._log.info(f"Total System Time (load, start, poll, read results): {total_system_time_ns / 1000:.2f} µs ({total_system_time_ns} ns)")
    
    latency_core_processing_ns = processing_end_time_ns - time_after_start_proc_ns
    dut._log.info(f"Approx. Core Processing Latency (from Start CMD sent to Done flag): {latency_core_processing_ns / 1000:.2f} µs ({latency_core_processing_ns} ns)")

    if total_system_time_ns > 0:
        system_throughput_pps = 1e9 / total_system_time_ns
        dut._log.info(f"Approx. System Throughput (incl. SPI for 1 patch): {system_throughput_pps:.2f} patches/sec")

    await ClockCycles(dut.clk_main, 20)
