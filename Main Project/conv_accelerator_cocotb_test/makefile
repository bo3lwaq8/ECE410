# Makefile for Cocotb

#--------------------------------------------------------------------------
# Configuration - User can modify these
#--------------------------------------------------------------------------
SIM = icarus
TOPLEVEL_LANG = verilog

VERILOG_SOURCES = accelerator_system.sv \
                  spi_slave.sv \
                  conv5x5_wrapper.sv \
                  conv5x5_core.sv

TOPLEVEL = accelerator_system
MODULE = test_spi_accelerator

ifeq ($(SIM),icarus)
    COMPILE_ARGS += -g2012
    COMPILE_ARGS += -DSIMULATOR_$(SIM)
endif

#--------------------------------------------------------------------------
# Standard Cocotb setup - Usually no need to modify below this line
#--------------------------------------------------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim
