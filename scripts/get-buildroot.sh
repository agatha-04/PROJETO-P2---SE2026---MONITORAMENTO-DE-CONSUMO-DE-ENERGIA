#!/bin/sh

set -e
cd $(dirname $0)/..
[ -d buildroot ] && { echo 'buildroot ja existe'; exit 0; }
wget https://buildroot.org/downloads/buildroot-2026.08.1.tar.xz
tar -xf buildroot-2026.08.1.tar.xz
mv buildroot-2026.08.1 buildroot
rm buildroot-2026.08.1.tar.xz
