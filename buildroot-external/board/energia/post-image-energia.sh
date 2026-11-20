#!/bin/sh
BOARD_DIR=$(dirname $0)
mkdir -p ${BINARIES_DIR}/rpi-firmware/overlays
cp ${BOARD_DIR}/ina219.dtbo ${BINARIES_DIR}/rpi-firmware/overlays/ina219.dtbo
