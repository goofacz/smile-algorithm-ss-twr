#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http:#www.gnu.org/licenses/.
#

import numpy as np
import scipy.constants as scc

from smile.filter import Filter


def localize_mobile(mobile_node, anchors, mobile_frames):
    # Construct POLL frames filter, i.e. transmitted frames ('TX' directions) sent by mobile node
    data_filter = Filter()
    data_filter.equal("direction", hash('TX'))
    data_filter.equal("source_mac_address", mobile_node["mac_address"])
    poll_frames = data_filter.execute(mobile_frames)

    # Construct REPONSE frames filter, i.e. transmitted frames ('RX' directions) sent to mobile node
    data_filter = Filter()
    data_filter.equal("direction", hash('RX'))
    data_filter.equal("destination_mac_address", mobile_node["mac_address"])
    response_frames = data_filter.execute(mobile_frames)

    # Here we will store distance between mobile node and three anchors, each row will contain value in meters and
    # anchor's MAC address
    distances = np.zeros((3, 2))

    assert (np.unique(anchors["message_processing_time"]).shape == (1,))
    processing_delay = anchors[0, "message_processing_time"]

    c = scc.value('speed of light in vacuum')
    c = c * 1e-12  # m/s -> m/ps

    for sequence_numbers in _lookup_sequence_number_triples(poll_frames["sequence_number"], response_frames["sequence_number"]):
        # Iterate over POLL and RESPONSE frames
        for i in range(len(sequence_numbers)):
            # Lookup POLL
            sequence_number = sequence_numbers[i]
            poll_frame = poll_frames[poll_frames["sequence_number"] == sequence_number]
            response_frame = response_frames[response_frames["sequence_number"] == sequence_number]

            # Compute ToF and fill time_of_flights array
            tof = (response_frame[0, "begin_clock_timestamp"] - poll_frame[
                0, "begin_clock_timestamp"] - processing_delay) / 2
            distances[i, 0] = tof * c
            distances[i, 1] = response_frame[0, "destination_mac_address"]

        A = np.zeros((3, 3))
        A[:, (0, 1)] = -2 * anchors[0:3, "position_2d"]
        A[:, 2] = 1

        B = np.zeros((3, 3))
        B[:, 0] = distances[:, 0]
        B[:, (1, 2)] = anchors[0:3, "position_2d"]
        B = np.power(B, 2)
        B = B[:, 0] - B[:, 1] - B[:, 2]

        position, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
        position = position[0:2]
        pass  # TODO


def _lookup_sequence_number_triples(poll_sequence_numbers, response_sequence_numbers):
    sequence_numbers = np.intersect1d(poll_sequence_numbers, response_sequence_numbers)
    triples = []

    current_triple = []
    for sequence_number in sequence_numbers:
        if len(current_triple) == 0:
            current_triple.append(sequence_number)
        elif current_triple[-1] == sequence_number - 1:
            current_triple.append(sequence_number)
        else:
            current_triple = [sequence_number]

        if len(current_triple) == 3:
            triples.append(current_triple)
            current_triple = []

    return triples
