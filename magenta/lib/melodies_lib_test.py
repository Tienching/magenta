# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for melodies_lib."""

# internal imports
import tensorflow as tf

from magenta.lib import melodies_lib
from magenta.lib import sequence_example_lib
from magenta.lib import sequences_lib
from magenta.lib import testing_lib


NUM_SPECIAL_EVENTS = melodies_lib.NUM_SPECIAL_EVENTS
NOTE_OFF = melodies_lib.NOTE_OFF
NO_EVENT = melodies_lib.NO_EVENT


class MelodiesLibTest(tf.test.TestCase):

  def setUp(self):
    self.quantized_sequence = sequences_lib.QuantizedSequence()
    self.quantized_sequence.bpm = 60.0
    self.quantized_sequence.steps_per_beat = 4

  def testGetNoteHistogram(self):
    events = [NO_EVENT, NOTE_OFF, 12 * 2 + 1, 12 * 3, 12 * 5 + 11, 12 * 6 + 3,
              12 * 4 + 11]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    expected = [1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2]
    self.assertEqual(expected, list(melody.get_note_histogram()))

    events = [0, 1, NO_EVENT, NOTE_OFF, 12 * 2 + 1, 12 * 3, 12 * 6 + 3,
              12 * 5 + 11, NO_EVENT, 12 * 4 + 11, 12 * 7 + 1]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    expected = [2, 3, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2]
    self.assertEqual(expected, list(melody.get_note_histogram()))

    melody = melodies_lib.MonophonicMelody()
    expected = [0] * 12
    self.assertEqual(expected, list(melody.get_note_histogram()))

  def testGetKeyHistogram(self):
    # One C.
    events = [NO_EVENT, 12 * 5, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    expected = [1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0]
    self.assertListEqual(expected, list(melody.get_major_key_histogram()))

    # One C and one C#.
    events = [NO_EVENT, 12 * 5, NOTE_OFF, 12 * 7 + 1, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    expected = [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1]
    self.assertListEqual(expected, list(melody.get_major_key_histogram()))

    # One C, one C#, and one D.
    events = [NO_EVENT, 12 * 5, NOTE_OFF, 12 * 7 + 1, NO_EVENT, 12 * 9 + 2]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    expected = [2, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2, 1]
    self.assertListEqual(expected, list(melody.get_major_key_histogram()))

  def testGetMajorKey(self):
    # D Major.
    events = [NO_EVENT, 12 * 2 + 2, 12 * 3 + 4, 12 * 5 + 1, 12 * 6 + 6,
              12 * 4 + 11, 12 * 3 + 9, 12 * 5 + 7, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    self.assertEqual(2, melody.get_major_key())

    # C# Major with accidentals.
    events = [NO_EVENT, 12 * 2 + 1, 12 * 4 + 8, 12 * 5 + 5, 12 * 6 + 6,
              12 * 3 + 3, 12 * 2 + 11, 12 * 3 + 10, 12 * 5, 12 * 2 + 8,
              12 * 4 + 1, 12 * 3 + 5, 12 * 5 + 9, 12 * 4 + 3, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    self.assertEqual(1, melody.get_major_key())

    # One note in C Major.
    events = [NO_EVENT, 12 * 2 + 11, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    self.assertEqual(0, melody.get_major_key())

  def testTranspose(self):
    # MonophonicMelody transposed down 5 half steps. 2 octave range.
    events = [12 * 5 + 4, NO_EVENT, 12 * 5 + 5, NOTE_OFF, 12 * 6, NO_EVENT]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.transpose(transpose_amount=-5, min_note=12 * 5, max_note=12 * 7)
    expected = [12 * 5 + 11, NO_EVENT, 12 * 5, NOTE_OFF, 12 * 5 + 7, NO_EVENT]
    self.assertEqual(expected, list(melody))

    # MonophonicMelody transposed up 19 half steps. 2 octave range.
    events = [12 * 5 + 4, NO_EVENT, 12 * 5 + 5, NOTE_OFF, 12 * 6, NO_EVENT]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.transpose(transpose_amount=19, min_note=12 * 5, max_note=12 * 7)
    expected = [12 * 6 + 11, NO_EVENT, 12 * 6, NOTE_OFF, 12 * 6 + 7, NO_EVENT]
    self.assertEqual(expected, list(melody))

    # MonophonicMelody transposed zero half steps. 1 octave range.
    events = [12 * 4 + 11, 12 * 5, 12 * 5 + 11, NOTE_OFF, 12 * 6, NO_EVENT]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.transpose(transpose_amount=0, min_note=12 * 5, max_note=12 * 6)
    expected = [12 * 5 + 11, 12 * 5, 12 * 5 + 11, NOTE_OFF, 12 * 5, NO_EVENT]
    self.assertEqual(expected, list(melody))

  def testSquash(self):
    # MonophonicMelody in C, transposed to C, and squashed to 1 octave.
    events = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 6 + 4, NO_EVENT]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=0)
    expected = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 5 + 4, NO_EVENT]
    self.assertEqual(expected, list(melody))

    # MonophonicMelody in D, transposed to C, and squashed to 1 octave.
    events = [12 * 5 + 2, 12 * 5 + 4, 12 * 6 + 7, 12 * 6 + 6, 12 * 5 + 1]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=0)
    expected = [12 * 5, 12 * 5 + 2, 12 * 5 + 5, 12 * 5 + 4, 12 * 5 + 11]
    self.assertEqual(expected, list(melody))

    # MonophonicMelody in D, transposed to E, and squashed to 1 octave.
    events = [12 * 5 + 2, 12 * 5 + 4, 12 * 6 + 7, 12 * 6 + 6, 12 * 4 + 11]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=4)
    expected = [12 * 5 + 4, 12 * 5 + 6, 12 * 5 + 9, 12 * 5 + 8, 12 * 5 + 1]
    self.assertEqual(expected, list(melody))

  def testSquashCenterOctaves(self):
    # Move up an octave.
    events = [12 * 4, NO_EVENT, 12 * 4 + 2, NOTE_OFF, 12 * 4 + 4, NO_EVENT,
              12 * 4 + 5, 12 * 5 + 2, 12 * 4 - 1, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 4, max_note=12 * 7, transpose_to_key=0)
    expected = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 5 + 4, NO_EVENT,
                12 * 5 + 5, 12 * 6 + 2, 12 * 5 - 1, NOTE_OFF]
    self.assertEqual(expected, list(melody))

    # Move down an octave.
    events = [12 * 6, NO_EVENT, 12 * 6 + 2, NOTE_OFF, 12 * 6 + 4, NO_EVENT,
              12 * 6 + 5, 12 * 7 + 2, 12 * 6 - 1, NOTE_OFF]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 4, max_note=12 * 7, transpose_to_key=0)
    expected = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 5 + 4, NO_EVENT,
                12 * 5 + 5, 12 * 6 + 2, 12 * 5 - 1, NOTE_OFF]
    self.assertEqual(expected, list(melody))

  def testSquashMaxNote(self):
    events = [12 * 5, 12 * 5 + 2, 12 * 5 + 4, 12 * 5 + 5, 12 * 5 + 11, 12 * 6,
              12 * 6 + 1]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=0)
    expected = [12 * 5, 12 * 5 + 2, 12 * 5 + 4, 12 * 5 + 5, 12 * 5 + 11, 12 * 5,
                12 * 5 + 1]
    self.assertEqual(expected, list(melody))

  def testSquashAllNotesOff(self):
    events = [NO_EVENT, NOTE_OFF, NO_EVENT, NO_EVENT]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    melody.squash(min_note=12 * 4, max_note=12 * 7, transpose_to_key=0)
    self.assertEqual(events, list(melody))

  def testFromQuantizedSequence(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 0, 40), (11, 55, 1, 2), (40, 45, 10, 14),
         (55, 120, 16, 17), (52, 99, 19, 20)])
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=0, track=0)
    expected = [12, 11, NOTE_OFF, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT,
                NO_EVENT, NO_EVENT, NO_EVENT, 40, NO_EVENT, NO_EVENT, NO_EVENT,
                NOTE_OFF, NO_EVENT, 55, NOTE_OFF, NO_EVENT, 52, NOTE_OFF]
    self.assertEqual(expected, list(melody))
    self.assertEqual(16, melody.steps_per_bar)

  def testFromQuantizedSequenceNotCommonTimeSig(self):
    self.quantized_sequence.time_signature = sequences_lib.TimeSignature(7, 8)
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 0, 40), (11, 55, 1, 2), (40, 45, 10, 14),
         (55, 120, 16, 17), (52, 99, 19, 20)])
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=0, track=0)
    expected = [12, 11, NOTE_OFF, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT,
                NO_EVENT, NO_EVENT, NO_EVENT, 40, NO_EVENT, NO_EVENT, NO_EVENT,
                NOTE_OFF, NO_EVENT, 55, NOTE_OFF, NO_EVENT, 52, NOTE_OFF]
    self.assertEqual(expected, list(melody))
    self.assertEqual(14, melody.steps_per_bar)

  def testFromNotesPolyphonic(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 4, 16), (19, 100, 4, 12)])
    melody = melodies_lib.MonophonicMelody()
    with self.assertRaises(melodies_lib.PolyphonicMelodyException):
      melody.from_quantized_sequence(self.quantized_sequence,
                                     start_step=0, track=0,
                                     ignore_polyphonic_notes=False)
    self.assertFalse(list(melody))

  def testFromNotesPolyphonicWithIgnorePolyphonicNotes(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 0, 8), (19, 100, 0, 12),
         (12, 100, 4, 12), (19, 100, 4, 16)])
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=0, track=0,
                                   ignore_polyphonic_notes=True)
    expected = [19] + [NO_EVENT] * 3 + [19] + [NO_EVENT] * 11 + [NOTE_OFF]
    self.assertEqual(expected, list(melody))

  def testFromNotesChord(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 4, 5), (19, 100, 4, 5),
         (20, 100, 4, 5), (25, 100, 4, 5)])
    melody = melodies_lib.MonophonicMelody()
    with self.assertRaises(melodies_lib.PolyphonicMelodyException):
      melody.from_quantized_sequence(self.quantized_sequence,
                                     start_step=0, track=0,
                                     ignore_polyphonic_notes=False)
    self.assertFalse(list(melody))

  def testFromNotesTrimEmptyMeasures(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 6, 7), (11, 100, 8, 9)])
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=0, track=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 12,
                NOTE_OFF, 11, NOTE_OFF]
    self.assertEqual(expected, list(melody))

  def testFromNotesTimeOverlap(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 4, 8), (11, 100, 13, 15),
         (13, 100, 8, 16)])
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=0, track=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 12, NO_EVENT, NO_EVENT,
                NO_EVENT, 13, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 11,
                NO_EVENT, NOTE_OFF]
    self.assertEqual(expected, list(melody))

  def testFromNotesStepsPerBar(self):
    self.quantized_sequence.time_signature = sequences_lib.TimeSignature(7, 8)
    self.quantized_sequence.steps_per_beat = 12
    self.quantized_sequence.tracks[0] = []
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=0, track=0,
                                   ignore_polyphonic_notes=False)
    self.assertEqual(42, melody.steps_per_bar)

  def testFromNotesStartAndEndStep(self):
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 4, 8), (11, 100, 9, 10), (13, 100, 13, 15),
         (14, 100, 19, 20), (15, 100, 21, 27)])
    melody = melodies_lib.MonophonicMelody()
    melody.from_quantized_sequence(self.quantized_sequence,
                                   start_step=18, track=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, NO_EVENT, NO_EVENT, 14, NOTE_OFF, 15, NO_EVENT,
                NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, NOTE_OFF]
    self.assertEqual(expected, list(melody))
    self.assertEqual(32, melody.end_step)

  def testExtractMelodiesSimple(self):
    self.quantized_sequence.steps_per_beat = 1
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 2, 4), (11, 1, 6, 7)])
    testing_lib.add_quantized_track(
        self.quantized_sequence, 1,
        [(12, 127, 2, 4), (14, 50, 6, 8)])
    expected = [[NO_EVENT, NO_EVENT, 12, NO_EVENT, NOTE_OFF, NO_EVENT, 11,
                 NOTE_OFF],
                [NO_EVENT, NO_EVENT, 12, NO_EVENT, NOTE_OFF, NO_EVENT, 14,
                 NO_EVENT, NOTE_OFF]]
    melodies = melodies_lib.extract_melodies(
        self.quantized_sequence, min_bars=1, gap_bars=1, min_unique_pitches=2,
        ignore_polyphonic_notes=True)

    self.assertEqual(2, len(melodies))
    self.assertTrue(isinstance(melodies[0], melodies_lib.MonophonicMelody))
    self.assertTrue(isinstance(melodies[1], melodies_lib.MonophonicMelody))

    melodies = sorted([list(melody) for melody in melodies])
    self.assertEqual(expected, melodies)

  def testExtractMultipleMelodiesFromSameTrack(self):
    self.quantized_sequence.steps_per_beat = 1
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 2, 4), (11, 1, 6, 7)])
    testing_lib.add_quantized_track(
        self.quantized_sequence, 1,
        [(12, 127, 2, 4), (14, 50, 6, 8),
         (50, 100, 33, 37), (52, 100, 34, 36)])
    expected = [[NO_EVENT, NO_EVENT, 12, NO_EVENT, NOTE_OFF, NO_EVENT, 11,
                 NOTE_OFF],
                [NO_EVENT, NO_EVENT, 12, NO_EVENT, NOTE_OFF, NO_EVENT, 14,
                 NO_EVENT, NOTE_OFF],
                [NO_EVENT, 50, 52, NO_EVENT, NOTE_OFF]]
    melodies = melodies_lib.extract_melodies(
        self.quantized_sequence, min_bars=1, gap_bars=2, min_unique_pitches=2,
        ignore_polyphonic_notes=True)
    melodies = sorted([list(melody) for melody in melodies])
    self.assertEqual(expected, melodies)

  def testExtractMelodiesMelodyTooShort(self):
    self.quantized_sequence.steps_per_beat = 1
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 127, 2, 4), (14, 50, 6, 7)])
    testing_lib.add_quantized_track(
        self.quantized_sequence, 1,
        [(12, 127, 2, 4), (14, 50, 6, 8)])
    expected = [[NO_EVENT, NO_EVENT, 12, NO_EVENT, NOTE_OFF, NO_EVENT, 14,
                 NO_EVENT, NOTE_OFF]]
    melodies = melodies_lib.extract_melodies(
        self.quantized_sequence, min_bars=2, gap_bars=1, min_unique_pitches=2,
        ignore_polyphonic_notes=True)
    melodies = [list(melody) for melody in melodies]
    self.assertEqual(expected, melodies)

  def testExtractMelodiesTooFewPitches(self):
    # Test that extract_melodies discards melodies with too few pitches where
    # pitches are equivalent by octave.
    self.quantized_sequence.steps_per_beat = 1
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 0, 1), (13, 100, 1, 2), (18, 100, 2, 3),
         (24, 100, 3, 4), (25, 100, 4, 5)])
    testing_lib.add_quantized_track(
        self.quantized_sequence, 1,
        [(12, 100, 0, 1), (13, 100, 1, 2), (18, 100, 2, 3),
         (25, 100, 3, 4), (26, 100, 4, 5)])
    expected = [[12, 13, 18, 25, 26, NOTE_OFF]]
    melodies = melodies_lib.extract_melodies(
        self.quantized_sequence, min_bars=1, gap_bars=1, min_unique_pitches=4,
        ignore_polyphonic_notes=True)
    melodies = [list(melody) for melody in melodies]
    self.assertEqual(expected, melodies)

  def testExtractMelodiesLateStart(self):
    self.quantized_sequence.steps_per_beat = 1
    testing_lib.add_quantized_track(
        self.quantized_sequence, 0,
        [(12, 100, 102, 103), (13, 100, 104, 106)])
    testing_lib.add_quantized_track(
        self.quantized_sequence, 1,
        [(12, 100, 100, 101), (13, 100, 102, 104)])
    expected = [[NO_EVENT, NO_EVENT, 12, NOTE_OFF, 13, NO_EVENT, NOTE_OFF],
                [12, NOTE_OFF, 13, NO_EVENT, NOTE_OFF]]
    melodies = melodies_lib.extract_melodies(
        self.quantized_sequence, min_bars=1, gap_bars=1, min_unique_pitches=2,
        ignore_polyphonic_notes=True)
    melodies = sorted([list(melody) for melody in melodies])
    self.assertEqual(expected, melodies)


class OneHotEncoderDecoder(melodies_lib.MelodyEncoderDecoder):

  def __init__(self, min_note, max_note, transpose_to_key):
    super(OneHotEncoderDecoder, self).__init__(min_note, max_note,
                                               transpose_to_key)
    self._input_size = self.max_note - self.min_note + NUM_SPECIAL_EVENTS
    self._num_classes = self.max_note - self.min_note + NUM_SPECIAL_EVENTS

  @property
  def input_size(self):
    return self._input_size

  @property
  def num_classes(self):
    return self._num_classes

  def melody_to_input(self, melody):
    input_ = [0.0] * self._input_size
    index = (melody.events[-1] + NUM_SPECIAL_EVENTS if melody.events[-1] < 0
             else melody.events[-1] - self.min_note + NUM_SPECIAL_EVENTS)
    input_[index] = 1.0
    return input_

  def melody_to_label(self, melody):
    return (melody.events[-1] + NUM_SPECIAL_EVENTS if melody.events[-1] < 0
            else melody.events[-1] - self.min_note + NUM_SPECIAL_EVENTS)

  def class_index_to_melody_event(self, class_index, melody):
    return (class_index - NUM_SPECIAL_EVENTS if class_index < NUM_SPECIAL_EVENTS
            else class_index + self.min_note - NUM_SPECIAL_EVENTS)


class MelodyEncoderDecoderTest(tf.test.TestCase):

  def setUp(self):
    self.melody_encoder_decoder = OneHotEncoderDecoder(60, 72, 0)

  def testMinNoteMaxNoteAndTransposeToKeyValidValues(self):
    # Valid parameters
    OneHotEncoderDecoder(0, 128, 0)
    OneHotEncoderDecoder(60, 72, 11)

    # Invalid parameters
    self.assertRaises(ValueError, OneHotEncoderDecoder, -1, 72, 0)
    self.assertRaises(ValueError, OneHotEncoderDecoder, 60, 129, 0)
    self.assertRaises(ValueError, OneHotEncoderDecoder, 60, 71, 0)
    self.assertRaises(ValueError, OneHotEncoderDecoder, 60, 72, -1)
    self.assertRaises(ValueError, OneHotEncoderDecoder, 60, 72, 12)

  def testInitValues(self):
    self.assertEqual(self.melody_encoder_decoder.min_note, 60)
    self.assertEqual(self.melody_encoder_decoder.max_note, 72)
    self.assertEqual(self.melody_encoder_decoder.transpose_to_key, 0)
    self.assertEqual(self.melody_encoder_decoder.input_size, 14)
    self.assertEqual(self.melody_encoder_decoder.num_classes, 14)

  def testEncode(self):
    events = [100, 100, 107, 111, NO_EVENT, 99, 112, NOTE_OFF, NO_EVENT]
    melody = melodies_lib.MonophonicMelody()
    melody.from_event_list(events)
    sequence_example = self.melody_encoder_decoder.encode(melody)
    expected_inputs = [
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    expected_labels = [2, 9, 13, 0, 13, 2, 1, 0]
    expected_sequence_example = sequence_example_lib.make_sequence_example(
        expected_inputs, expected_labels)
    self.assertEqual(sequence_example, expected_sequence_example)

  def testGetInputsBatch(self):
    events1 = [100, 100, 107, 111, NO_EVENT, 99, 112, NOTE_OFF, NO_EVENT]
    melody1 = melodies_lib.MonophonicMelody()
    melody1.from_event_list(events1)
    events2 = [9, 10, 12, 14, 15, 17, 19, 21, 22]
    melody2 = melodies_lib.MonophonicMelody()
    melody2.from_event_list(events2)
    transpose_amount1 = melody1.squash(
        self.melody_encoder_decoder.min_note,
        self.melody_encoder_decoder.max_note,
        self.melody_encoder_decoder.transpose_to_key)
    transpose_amount2 = melody2.squash(
        self.melody_encoder_decoder.min_note,
        self.melody_encoder_decoder.max_note,
        self.melody_encoder_decoder.transpose_to_key)
    self.assertEqual(transpose_amount1, -40)
    self.assertEqual(transpose_amount2, 50)
    melodies = [melody1, melody2]
    expected_inputs1 = [
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    expected_inputs2 = [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    expected_full_length_inputs_batch = [expected_inputs1, expected_inputs2]
    expected_last_event_inputs_batch = [expected_inputs1[-1:],
                                        expected_inputs2[-1:]]
    self.assertListEqual(
        expected_full_length_inputs_batch,
        self.melody_encoder_decoder.get_inputs_batch(melodies, True))
    self.assertListEqual(
        expected_last_event_inputs_batch,
        self.melody_encoder_decoder.get_inputs_batch(melodies))

  def testExtendMelodies(self):
    melody1 = melodies_lib.MonophonicMelody()
    melody1.from_event_list([60])
    melody2 = melodies_lib.MonophonicMelody()
    melody2.from_event_list([60])
    melody3 = melodies_lib.MonophonicMelody()
    melody3.from_event_list([60])
    melody4 = melodies_lib.MonophonicMelody()
    melody4.from_event_list([60])
    melodies = [melody1, melody2, melody3, melody4]
    softmax = [[
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ], [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    ], [
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ], [
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ]]
    self.melody_encoder_decoder.extend_melodies(melodies, softmax)
    self.assertListEqual(melody1.events, [60, 60])
    self.assertListEqual(melody2.events, [60, 71])
    self.assertListEqual(melody3.events, [60, NO_EVENT])
    self.assertListEqual(melody4.events, [60, NOTE_OFF])


if __name__ == '__main__':
  tf.test.main()
