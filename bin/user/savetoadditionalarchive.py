#!/usr/bin/python3
# Service to save certain observation types to separate databases
# Copyright (C) 2026 Johanna Karen Rödenbeck

"""

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

"""
    To use this extension add data binding(s) and database(s) to `weewx.conf`
    and write the appropriate database schema according to the rules of
    WeeWX database schema files. Then add the key `savetoadditionalarchive`
    to the respective binding(s) and set it to `true`.
"""

import weeutil.weeutil
import weewx
from weewx.engine import StdService

VERSION = "0.1"

import weeutil.logger
import logging
log = logging.getLogger('user.savetoadditionalarchive')

def logdbg(msg):
    log.debug(msg)

def loginf(msg):
    log.info(msg)

def logerr(msg):
    log.error(msg)


class AdditionalArchive(StdService):
    """ This services saves records to additional databases, including only
        those observation types that are in the schema of the database
    """

    def __init__(self, engine, config_dict):
        super(AdditionalArchive,self).__init__(engine, config_dict)
        # Set up logging
        self.log_success = weeutil.weeutil.to_bool(config_dict.get('log_success',True))
        self.log_failure = weeutil.weeutil.to_bool(config_dict.get('log_failure',True))
        # Get databases to save to
        self.data_bindings = []
        ct = 0
        for binding in config_dict.get('DataBindings',dict()):
            binding_config_dict = config_dict['DataBindings'][binding]
            if weeutil.weeutil.to_bool(binding_config_dict.get('savetoadditionalarchive',False)):
                self.data_bindings.append(binding)
                ct += 1
        # Bind methods to events
        if ct:
            self.bind(weewx.STARTUP, self.startup)
            self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        else:
            loginf('no additional databases configured')
    
    def startup(self, _unused):
        """Called when the engine is starting up. Main task is to set up the databases.
        """
        for binding in self.data_bindings:
            self._startup_one_binding(binding)
    
    def _startup_one_binding(self, binding):
        """Called when the engine is starting up. Main task is to set up the database.
        
           Copyright (C) Tom Keffer
        """

        # This will create the database if it doesn't exist:
        dbmanager = self.engine.db_binder.get_manager(binding, initialize=True)
        loginf("Using binding '%s' to database '%s'" % (binding, dbmanager.database_name))

        # Make sure the daily summaries have not been partially updated
        if dbmanager._read_metadata('lastWeightPatch'):
            raise weewx.ViolatedPrecondition("Update of daily summary for database '%s' not"
                                             " complete. Finish the update first."
                                             % dbmanager.database_name)

        # Backfill the daily summaries.
        _nrecs, _ndays = dbmanager.backfill_day_summary()
    
    def new_archive_record(self, event):
        """Called when a new archive record has arrived.
        Put it in the archive database."""
        for binding in self.data_bindings:
            self._save_one_binding(event, binding)
    
    def _save_one_binding(self, event, binding):
        """Called when a new archive record has arrived.
        Put it in the archive database."""
        dbmanager = self.engine.db_binder.get_manager(binding)
        dbmanager.addRecord(event.record,
                            event.accumulator,
                            log_success=self.log_success,
                            log_failure=self.log_failure)


loginf("version %s" % VERSION)
