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

import os.path
import argparse
import numpy as np
import scipy.constants as scc
from smile.frames import Frames
from smile.nodes import Nodes
from smile.filter import Filter
from anchors import Anchors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Single Sided Two-Way ranging data.')
    parser.add_argument('logs_directory_path', type=str, nargs=1, help='Path to directory holding CSV logs')
    arguments = parser.parse_args()

    logs_directory_path = arguments.logs_directory_path[0]

    # Load data from CSV files
    anchors = Anchors.load_csv(os.path.join(logs_directory_path, 'ss_twr_anchors.csv'))
    mobiles = Nodes.load_csv(os.path.join(logs_directory_path, 'ss_twr_mobiles.csv'))
    mobile_frames = Frames.load_csv(os.path.join(logs_directory_path, 'ss_twr_mobile_frames.csv'))
    anchor_frames = Frames.load_csv(os.path.join(logs_directory_path, 'ss_twr_anchor_frames.csv'))

    # Construct POLL frames filter, i.e. transmitted frames ('TX' directions) sent by mobile node
    # (frames.mac_addresses[:, 0] equal to mobile nod'se MAC address)
    data_filter = Filter()
    data_filter.equal("direction", hash('TX'))
    data_filter.equal("source_mac_address", mobiles[0, "mac_address"])
    poll_frames = data_filter.execute(mobile_frames)

    # Construct REPONSE frames filter, i.e. transmitted frames ('RX' directions) sent to mobile node
    # (frames.mac_addresses[:, 1] equal to mobile nod'se MAC address)
    data_filter = Filter()
    data_filter.equal("direction", hash('RX'))
    data_filter.equal("destination_mac_address", mobiles[0, "mac_address"])
    response_frames = data_filter.execute(mobile_frames)

    # Here we will store distance between mobile node and three anchors, each row will contain value in meters and
    # anchor's MAC address
    distances = np.zeros((3, 2))

    assert(np.unique(anchors["message_processing_time"]).shape == (1,))
    processing_delay = anchors[0, "message_processing_time"]

    c = scc.value('speed of light in vacuum')
    c = c * 1e-12  # m/s -> m/ps

    # Iterate over POLL and RESPONSE frames
    sequence_numbers = (1, 2, 3)
    for i in range(len(sequence_numbers)):
        # Lookup POLL
        sequence_number = sequence_numbers[i]
        poll_frame = poll_frames[poll_frames["sequence_number"] == sequence_number]
        response_frame = response_frames[response_frames["sequence_number"] == sequence_number]

        # Compute ToF and fill time_of_flights array
        tof = (response_frame[0, "begin_clock_timestamp"] - poll_frame[0, "begin_clock_timestamp"] - processing_delay) / 2
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
