#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""The default plugin for parsing OLE Compound Files (OLECF)."""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OleCfItemEvent(time_events.FiletimeEvent):
  """Convenience class for an OLECF item event."""

  DATA_TYPE = 'olecf:item'

  def __init__(self, timestamp, usage, olecf_item):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: A string describing the timestamp value.
      olecf_item: The OLECF item (pyolecf.item).
    """
    super(OleCfItemEvent, self).__init__(timestamp, usage)

    # TODO: need a better way to express the original location of the
    # original data.
    self.offset = 0

    self.name = olecf_item.name
    # TODO: have pyolecf return the item type here.
    # self.type = olecf_item.type
    self.size = olecf_item.size


class DefaultOleCFPlugin(interface.OlecfPlugin):
  """Class to define the default OLECF file plugin."""

  NAME = 'olecf_default'
  DESCRIPTION = u'Parser for a generic OLECF item.'

  def _ParseItem(
      self, parser_context, file_entry=None, parser_chain=None,
      olecf_item=None):
    """Parses an OLECF item.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      olecf_item: An optional OLECF item (instance of pyolecf.item).

    Returns:
      A boolean value indicating if an event object was produced.
    """
    event_object = None
    result = False

    creation_time, modification_time = self.GetTimestamps(olecf_item)

    if creation_time:
      event_object = OleCfItemEvent(
          creation_time, eventdata.EventTimestamp.CREATION_TIME,
          olecf_item)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

    if modification_time:
      event_object = OleCfItemEvent(
          modification_time, eventdata.EventTimestamp.MODIFICATION_TIME,
          olecf_item)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

    if event_object:
      result = True

    for sub_item in olecf_item.sub_items:
      if self._ParseItem(
          parser_context, file_entry=file_entry, parser_chain=parser_chain,
          olecf_item=sub_item):
        result = True

    return result

  def ParseItems(
      self, parser_context, file_entry=None, parser_chain=None, root_item=None,
      **unused_kwargs):
    """Parses OLECF items.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      root_item: Optional root item of the OLECF file. The default is None.
    """
    if not self._ParseItem(
        parser_context, file_entry=file_entry, parser_chain=parser_chain,
        olecf_item=root_item):
      # If no event object was produced, produce at least one for
      # the root item.
      event_object = OleCfItemEvent(
          0, eventdata.EventTimestamp.CREATION_TIME, root_item)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

  def Process(
      self, parser_context, file_entry=None, parser_chain=None, root_item=None,
      item_names=None, **kwargs):
    """Determine if this is the right plugin for this OLECF file.

    This function takes a list of sub items found in the root of a
    OLECF file and compares that to a list of required items defined
    in this plugin.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      root_item: Optional root item of the OLECF file. The default is None.
      item_names: Optional list of all items discovered in the root.
                  The default is None.

    Raises:
      errors.WrongPlugin: If the set of required items is not a subset
                          of the available items.
      ValueError: If the root_item or items are not set.
    """
    if root_item is None or item_names is None:
      raise ValueError(u'Root item or items are not set.')

    # Add ourselves to the parser chain, which will be used in all subsequent
    # event creation in this parser.
    parser_chain = self._BuildParserChain(parser_chain)

    self.ParseItems(
        parser_context, file_entry=file_entry, parser_chain=parser_chain,
        root_item=root_item)


olecf.OleCfParser.RegisterPlugin(DefaultOleCFPlugin)
