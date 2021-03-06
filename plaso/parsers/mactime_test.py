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
"""Tests the for mactime parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mactime as mactime_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import mactime
from plaso.parsers import test_lib
from plaso.serializer import protobuf_serializer


class MactimeUnitTest(test_lib.ParserTestCase):
  """Tests the for mactime parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = mactime.MactimeParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['mactime.body'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The file contains 13 lines x 4 timestamps per line, which should be
    # 52 events in total. However several of these events have an empty
    # timestamp value and are omitted.
    # Total entries: 11 * 3 + 2 * 4 = 41
    self.assertEquals(len(event_objects), 41)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0
    event_object = event_objects[6]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        u'2012-05-25 15:59:43+00:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEquals(event_object.inode, 16)

    event_object = event_objects[6]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        u'2012-05-25 15:59:43+00:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    expected_string = u'/a_directory/another_file'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[8]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        u'2012-05-25 15:59:44+00:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    event_object = event_objects[7]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        u'2012-05-25 15:59:45+00:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CHANGE_TIME)
    self.assertEquals(event_object.filename, u'/a_directory/another_file')
    self.assertEquals(event_object.mode_as_string, u'r/rrw-------')

    event_object = event_objects[37]

    self.assertEquals(event_object.inode, 4)

    # Serialize the event objects.
    serialized_events = []
    serializer = protobuf_serializer.ProtobufEventObjectSerializer
    for event_object in event_objects:
      serialized_events.append(serializer.WriteSerialized(event_object))

    self.assertEquals(len(serialized_events), len(event_objects))


if __name__ == '__main__':
  unittest.main()
