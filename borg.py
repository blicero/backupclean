#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-05 15:11:29 krylon>
#
# /data/code/python/backupclean/borg.py
# created on 05. 03. 2025
# (c) 2025 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
backupclean.borg

(c) 2025 Benjamin Walkenhorst
"""

import re
import subprocess
from datetime import datetime, timedelta
from typing import Final

from backupclean import common

datePat: Final[str] = "%Y_%m_%d"
borgCmd: Final[str] = "/usr/bin/borg"
newline: Final[re.Pattern] = re.compile("\n")
namePat: Final[re.Pattern] = re.compile("^(\\d{4}_\\d{2}_\\d{2})", re.M)


class Backup:  # pylint: disable-msg=R0903
    """Backup represents a backup archive"""

    __slots__ = [
        "name",
        "date",
    ]

    name: Final[str]
    date: Final[datetime]

    def __init__(self, name) -> None:
        self.name = name
        self.date = datetime.strptime(name, datePat)

    def age(self) -> timedelta:
        """Return the age of the Backup as a timedelta object."""
        return datetime.now() - self.date


class Borg:  # pylint: disable-msg=R0903
    """Borg handles the invocation and parsing of output of the borg command"""

    __slots__ = [
        "log",
        "repo",
        "password",
    ]

    def __init__(self, repo, password) -> None:
        self.log = common.get_logger("borg")
        self.repo = repo
        self.password = password

    def list_backup(self) -> list[Backup]:
        """Get a list of archives for the configured borg repo"""
        cmd: subprocess.CompletedProcess = subprocess.run(
            [borgCmd, "list"],
            capture_output=True,
            check=False,
            text=True,
            env={"BORG_REPO": self.repo, "BORG_PASSPHRASE": self.password},
            encoding="utf-8")

        if cmd.returncode != 0:
            self.log.error("Error invoking %s:\n%s\n\n",
                           borgCmd,
                           cmd.stdout)

        archives: list[Backup] = []
        names: list[str] = namePat.findall(cmd.stdout)

        for n in names:
            b = Backup(n)
            archives.append(b)

        return archives

# Local Variables: #
# python-indent: 4 #
# End: #
