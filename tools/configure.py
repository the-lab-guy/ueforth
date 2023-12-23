#! /usr/bin/env python3
# Copyright 2023 Bradley D. Nelson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import subprocess

VERSION = '7.0.7.16'
STABLE_VERSION = '7.0.6.19'
OLD_STABLE_VERSION = '7.0.5.4'

REVISION = 'TODO'
#REVISION=$(shell git rev-parse HEAD | head -c 20)
#REVSHORT=$(shell echo $(REVISION) | head -c 7)

CFLAGS_COMMON = [
  '-O2',
  '-I', './',
  '-I', '../',
]

CFLAGS_MINIMIZE = [
  '-s',
  '-DUEFORTH_MINIMAL',
  '-fno-exceptions',
  '-ffreestanding',
  '-fno-stack-protector',
  '-fomit-frame-pointer',
  '-fno-ident',
  '-ffunction-sections', '-fdata-sections',
  '-fmerge-all-constants',
]

if sys.platform == 'linux':
  CFLAGS_MINIMIZE.append('-Wl,--build-id=none')

CFLAGS = CFLAGS_COMMON + CFLAGS_MINIMIZE + [
  '-std=c++11',
  '-Wall',
  '-Werror',
  '-no-pie',
  '-Wl,--gc-sections',
]

if sys.platform == 'darwin':
  CFLAGS += [
    '-Wl,-dead_strip',
    '-D_GNU_SOURCE',
  ]
elif sys.platform == 'linux':
  CFLAGS += [
    '-s',
    '-Wl,--gc-sections',
    '-no-pie',
    '-Wl,--build-id=none',
  ]

STRIP_ARGS = ['-S']
if sys.platform == 'darwin':
  STRIP_ARGS += ['-x']
elif sys.platform == 'linux':
  STRIP_ARGS += [
    '--strip-unneeded',
    '--remove-section=.note.gnu.gold-version',
    '--remove-section=.comment',
    '--remove-section=.note',
    '--remove-section=.note.gnu.build-id',
    '--remove-section=.note.ABI-tag',
  ]

LIBS = ['-ldl']

output = """

version = %(version)s
revision = %(revision)s
cflags = %(cflags)s
strip_args = %(strip_args)s
libs = %(libs)s

rule mkdir
  description = mkdir
  command = mkdir -p $out

rule importation
  description = importation
  depfile = $out.dd
  command = ../tools/importation.py -i $in -o $out -I . -I .. $options --depsout $out.dd -DVERSION=$version -DREVSION=$revision

build gen: mkdir

""" % {
  'version': VERSION,
  'revision': REVISION,
  'cflags': ' '.join(CFLAGS),
  'strip_args': ' '.join(STRIP_ARGS),
  'libs': ' '.join(LIBS),
}

def Importation(target, source, header_mode='cpp', name=None, keep=False):
  source = '../' + source
  options = ''
  if keep:
    options += '--keep-first-comment'
  if name:
    options += ' --name ' + name + ' --header ' + header_mode
  global output
  output += f"""
build {target}: importation {source} | gen
  options = {options}
"""

def Esp32Optional(target, c_source, header, name, forth_source):
  Importation(target, name, forth_source)
  Importation('gen/' + header, name, forth_source)

Importation('gen/esp32_assembler.h', 'common/assembler.fs', name='assembler_source')
Importation('gen/esp32_xtensa-assembler.h',
            'esp32/optional/assemblers/xtensa-assembler.fs', name='xtensa_assembler_source')
Importation('gen/esp32_riscv-assembler.h',
            'esp32/optional/assemblers/riscv-assembler.fs', name='riscv_assembler_source')

Importation('gen/esp32_camera.h', 'esp32/optional/camera/camera_server.fs', name='camera_source')
Importation('gen/esp32_interrupts.h', 'esp32/optional/interrupts/timers.fs', name='interrupts_source')
Importation('gen/esp32_oled.h', 'esp32/optional/oled/oled.fs', name='oled_source')
Importation('gen/esp32_spi-flash.h', 'esp32/optional/spi-flash/spi-flash.fs', name='spi_flash_source')
Importation('gen/esp32_serial-bluetooth.h',
            'esp32/optional/serial-bluetooth/serial-bluetooth.fs', name='serial_bluetooth_source')

Importation('gen/posix_boot.h', 'posix/posix_boot.fs', name='boot')
Importation('gen/window_boot.h', 'windows/windows_boot.fs', header_mode='win', name='boot')
Importation('gen/window_boot_extra.h', 'windows/windows_boot_extra.fs', header_mode='win', name='boot')
Importation('gen/pico_ice_boot.h', 'pico-ice/pico_ice_boot.fs', name='boot')
Importation('gen/esp32_boot.h', 'esp32/esp32_boot.fs', name='boot')
Importation('gen/web_boot.js', 'web/web_boot.fs', header_mode='web', name='boot')

print(output)