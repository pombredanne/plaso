#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Plugin for the Mac OS X launch services quarantine events."""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class LsQuarantineEvent(time_events.CocoaTimeEvent):
  """Convenience class for a Mac OS X launch services quarantine event."""
  DATA_TYPE = 'macosx:lsquarantine'

  # TODO: describe more clearly what the data value contains.
  def __init__(self, cocoa_time, url, user_agent, data):
    """Initializes the event object.

    Args:
      cocoa_time: The Cocoa time value.
      url: The original URL of the file.
      user_agent: The user agent that was used to download the file.
      data: The data.
    """
    super(LsQuarantineEvent, self).__init__(
        cocoa_time, eventdata.EventTimestamp.FILE_DOWNLOADED)

    self.url = url
    self.agent = user_agent
    self.data = data


class LsQuarantinePlugin(interface.SQLitePlugin):
  """Parses the launch services quarantine events database.

     The LS quarantine events are stored in SQLite database files named
     /Users/<username>/Library/Preferences/\
         QuarantineEvents.com.apple.LaunchServices
  """

  NAME = 'ls_quarantine'
  DESCRIPTION = u'Parser for LS quarantine events SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (('SELECT LSQuarantineTimestamp AS Time, LSQuarantine'
        'AgentName AS Agent, LSQuarantineOriginURLString AS URL, '
        'LSQuarantineDataURLString AS Data FROM LSQuarantineEvent '
        'ORDER BY Time'), 'ParseLSQuarantineRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset(['LSQuarantineEvent'])

  def ParseLSQuarantineRow(
      self, parser_context, row, file_entry=None, parser_chain=None, query=None,
      **unused_kwargs):
    """Parses a launch services quarantine event row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      query: Optional query string. The default is None.
    """
    event_object = LsQuarantineEvent(
        row['Time'], row['URL'], row['Agent'], row['Data'])
    parser_context.ProduceEvent(
        event_object, query=query, parser_chain=parser_chain,
        file_entry=file_entry)


sqlite.SQLiteParser.RegisterPlugin(LsQuarantinePlugin)
