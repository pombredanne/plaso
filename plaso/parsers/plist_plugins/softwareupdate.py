#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains a default plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SoftwareUpdatePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Mac OS X update status."""

  NAME = 'plist_softwareupdate'
  DESCRIPTION = u'Parser for Mac OS X software update plist files.'

  PLIST_PATH = 'com.apple.SoftwareUpdate.plist'
  PLIST_KEYS = frozenset([
      'LastFullSuccessfulDate', 'LastSuccessfulDate',
      'LastAttemptSystemVersion', 'LastUpdatesAvailable',
      'LastRecommendedUpdatesAvailable', 'RecommendedUpdates'])

  # Generated events:
  # LastFullSuccessfulDate: timestamp when Mac OS X was full update.
  # LastSuccessfulDate: timestamp when Mac OS X was partially update.

  def GetEntries(
      self, parser_context, file_entry=None, parser_chain=None, match=None,
      **unused_kwargs):
    """Extracts relevant Mac OS X update entries.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    root = '/'
    key = ''
    version = match.get('LastAttemptSystemVersion', u'N/A')
    pending = match['LastUpdatesAvailable']

    description = u'Last Mac OS X {0:s} full update.'.format(version)
    event_object = plist_event.PlistEvent(
        root, key, match['LastFullSuccessfulDate'], description)
    parser_context.ProduceEvent(
        event_object, parser_chain=parser_chain, file_entry=file_entry)

    if pending:
      software = []
      for update in match['RecommendedUpdates']:
        software.append(u'{0:s}({1:s})'.format(
            update['Identifier'], update['Product Key']))
      description = (
          u'Last Mac OS {0!s} partially update, pending {1!s}: {2:s}.').format(
              version, pending, u','.join(software))
      event_object = plist_event.PlistEvent(
          root, key, match['LastSuccessfulDate'], description)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)


plist.PlistParser.RegisterPlugin(SoftwareUpdatePlugin)
