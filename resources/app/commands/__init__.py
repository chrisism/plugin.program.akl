# -*- coding: utf-8 -*-

# Advanced Emulator Launcher package inisialisation file.

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Import each command file for automatically registration by
# the mediator implementation.
import resources.app.commands.mediator
import resources.app.commands.view_rendering_commands
import resources.app.commands.addon_commands
import resources.app.commands.category_commands
import resources.app.commands.romcollection_commands
import resources.app.commands.romcollection_roms_commands
import resources.app.commands.rom_commands
import resources.app.commands.rom_launcher_commands
import resources.app.commands.rom_scanner_commands
import resources.app.commands.rom_scraper_commands
import resources.app.commands.stats_commands
import resources.app.commands.misc_commands
