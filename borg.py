#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-06 21:26:15 krylon>
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

import functools
import logging
import math
import re
import subprocess
from datetime import datetime, timedelta
from typing import Final

from backupclean import common

datePat: Final[str] = "%Y_%m_%d"
borgCmd: Final[str] = "/usr/bin/borg"
newline: Final[re.Pattern] = re.compile("\n")
namePat: Final[re.Pattern] = re.compile("^(\\d{4}_\\d{2}_\\d{2})", re.M)


@functools.total_ordering
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

    def __str__(self) -> str:
        """Stringify the thang"""
        return f"::{self.name}"

    def __repr__(self) -> str:
        """Stringify the thang"""
        return f"::{self.name}"

    def __lt__(self, other):
        """Compare the Backup to another"""
        if not type(other) is type(self):
            return NotImplemented
        return self.date < other.date

    def __eq__(self, other):
        """See if the Backup is equal to another"""
        if not type(self) is type(other):
            return NotImplemented
        return self.date == other.date

    def __hash__(self):
        """Return a hash value"""
        return hash(self.name)

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


class CleanupSchedule:  # pylint: disable-msg=R0903
    """CleanupSchedule describes which archives should be kept or deleted."""

    __slots__ = [
        "log",
        "archives",
        "daily",
        "weekly",
        "monthly",
    ]

    log: logging.Logger
    archives: list[Backup]
    daily: Final[int]
    weekly: Final[int]
    monthly: Final[int]

    def __init__(self, d: int, w: int, m: int, archives: list[Backup]) -> None:
        self.log = common.get_logger("cleanup")
        self.archives = archives
        self.daily = d
        self.weekly = w
        self.monthly = m

    def prune(self) -> list[Backup]:
        """Return the archives to NOT delete."""
        archives = sorted(self.archives, key=lambda x: x.date)
        keepers = set()
        today: Final[datetime] = datetime.today()
        limit: Final[datetime] = today - timedelta(days=self.daily)

        # First we keep the daily archives for the past <self.daily> days.
        for a in archives:
            if a.date > limit:
                archives.remove(a)
                keepers.add(a)

        by_week: dict = {}

        for a in archives:
            dt = a.date.isocalendar()
            week = (dt.year, dt.week)
            if week not in by_week:
                by_week[week] = []

            by_week[week].append(a)

        for w in sorted(by_week.keys(), reverse=True):
            arc = by_week[w][-1]
            if weeks_since(arc.date) < self.weekly:
                keepers.add(arc)

        return sorted(keepers, reverse=True)


def weeks_since(d1: datetime, d2: datetime | None = None) -> int:
    """Return the number of weeks between two dates."""
    if d2 is None:
        d2 = datetime.now()

    assert d1 < d2

    if d1.year == d2.year:
        return d2.isocalendar().week - d1.isocalendar().week

    return math.floor((d2 - d1).days / 7)

# Local Variables: #
# python-indent: 4 #
# End: #
