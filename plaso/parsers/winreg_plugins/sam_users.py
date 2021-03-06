#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.#
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
"""This file contains the SAM Users & Names key plugin."""

import construct
import logging
from plaso.events import windows_events
from plaso.lib import binary
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class UsersPlugin(interface.KeyPlugin):
  """SAM Windows Registry plugin for Users Account information."""

  NAME = 'winreg_sam_users'
  DESCRIPTION = u'Parser for SAM Users and Names Registry keys.'

  REG_KEYS = [u'\\SAM\\Domains\\Account\\Users']
  REG_TYPE = 'SAM'
  F_VALUE_STRUCT = construct.Struct(
      'f_struct', construct.Padding(8), construct.ULInt64('last_login'),
      construct.Padding(8), construct.ULInt64('password_reset'),
      construct.Padding(16), construct.ULInt16('rid'), construct.Padding(16),
      construct.ULInt8('login_count'))
  V_VALUE_HEADER = construct.Struct(
      'v_header', construct.Array(11, construct.ULInt32('values')))
  V_VALUE_HEADER_SIZE = 0xCC

  def GetEntries(
      self, parser_context, key=None, registry_type=None, file_entry=None,
      parser_chain=None, **unused_kwargs):
    """Collect data from Users and Names and produce event objects.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """

    name_dict = {}

    name_key = key.GetSubkey('Names')
    if not name_key:
      logging.error(u'Unable to locate Names key.')
      return
    values = [(v.name, v.last_written_timestamp) for v in name_key.GetSubkeys()]
    name_dict = dict(values)

    for subkey in key.GetSubkeys():
      text_dict = {}
      if subkey.name == 'Names':
        continue
      text_dict['user_guid'] = subkey.name
      parsed_v_value = self._ParseVValue(subkey)
      if not parsed_v_value:
        logging.error(u'V Value was not succesfully parsed by ParseVValue.')
        return
      username = parsed_v_value[0]
      full_name = parsed_v_value[1]
      comments = parsed_v_value[2]
      if username:
        text_dict['username'] = username
      if full_name:
        text_dict['full_name'] = full_name
      if comments:
        text_dict['comments'] = comments
      if name_dict:
        account_create_time = name_dict.get(text_dict.get('username'), 0)
      else:
        account_create_time = 0

      f_data = self._ParseFValue(subkey)
      last_login_time = timelib.Timestamp.FromFiletime(f_data.last_login)
      password_reset_time = timelib.Timestamp.FromFiletime(
          f_data.password_reset)
      text_dict['account_rid'] = f_data.rid
      text_dict['login_count'] = f_data.login_count

      if account_create_time > 0:
        event_object = windows_events.WindowsRegistryEvent(
            account_create_time, key.path, text_dict,
            usage=eventdata.EventTimestamp.ACCOUNT_CREATED,
            offset=key.offset, registry_type=registry_type,
            source_append=u'User Account Information')
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      if last_login_time > 0:
        event_object = windows_events.WindowsRegistryEvent(
            last_login_time, key.path, text_dict,
            usage=eventdata.EventTimestamp.LAST_LOGIN_TIME,
            offset=key.offset,
            registry_type=registry_type,
            source_append=u'User Account Information')
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      if password_reset_time > 0:
        event_object = windows_events.WindowsRegistryEvent(
            password_reset_time, key.path, text_dict,
            usage=eventdata.EventTimestamp.LAST_PASSWORD_RESET,
            offset=key.offset, registry_type=registry_type,
            source_append=u'User Account Information')
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

  def _ParseVValue(self, key):
    """Parses V value and returns name, fullname, and comments data.

    Args:
      key: Registry key (instance of winreg.WinRegKey).

    Returns:
      name: Name data parsed with name start and length values.
      fullname: Fullname data parsed with fullname start and length values.
      comments: Comments data parsed with comments start and length values.
    """

    v_value = key.GetValue('V')
    if not v_value:
      logging.error(u'Unable to locate V Value in key.')
      return
    try:
      structure = self.V_VALUE_HEADER.parse(v_value.data)
    except construct.FieldError as exception:
      logging.error(
          u'Unable to extract V value header data: {:s}'.format(exception))
      return
    name_offset = structure.values()[0][3] + self.V_VALUE_HEADER_SIZE
    full_name_offset = structure.values()[0][6] + self.V_VALUE_HEADER_SIZE
    comments_offset = structure.values()[0][9] + self.V_VALUE_HEADER_SIZE
    name_raw = v_value.data[
        name_offset:name_offset + structure.values()[0][4]]
    full_name_raw = v_value.data[
        full_name_offset:full_name_offset + structure.values()[0][7]]
    comments_raw = v_value.data[
        comments_offset:comments_offset + structure.values()[0][10]]
    name = binary.ReadUtf16(name_raw)
    full_name = binary.ReadUtf16(full_name_raw)
    comments = binary.ReadUtf16(comments_raw)
    return name, full_name, comments

  def _ParseFValue(self, key):
    """Parses F value and returns parsed F data construct object.

    Args:
      key: Registry key (instance of winreg.WinRegKey).

    Returns:
      f_data: Construct parsed F value containing rid, login count,
              and timestamp information.
    """
    f_value = key.GetValue('F')
    if not f_value:
      logging.error(u'Unable to locate F Value in key.')
      return
    try:
      f_data = self.F_VALUE_STRUCT.parse(f_value.data)
    except construct.FieldError as exception:
      logging.error(
          u'Unable to extract F value data: {:s}'.format(exception))
      return
    return f_data


winreg.WinRegistryParser.RegisterPlugin(UsersPlugin)
