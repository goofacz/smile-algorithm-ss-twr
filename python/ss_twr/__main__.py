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
import numpy
from smile.frames import Frames
from smile.nodes import Nodes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Single Sided Two-Way ranging data.')
    parser.add_argument('logs_directory_path', type=str, nargs=1, help='Path to directory holding CSV logs')
    arguments = parser.parse_args()

    logs_directory_path = arguments.logs_directory_path[0]

    # Load data from CSV files
    anchors = Nodes(os.path.join(logs_directory_path, 'ss_twr_mobile_nodes.csv'))
    mobiles = Nodes(os.path.join(logs_directory_path, 'ss_twr_mobile_nodes.csv'))
    frames = Frames(os.path.join(logs_directory_path, 'ss_twr_frames.csv'))

    # Construct POLL frames filter, i.e. transmitted frames ('TX' directions) sent by mobile node
    # (frames.mac_addresses[:, 0] equal to mobile nod'se MAC address)
    poll_frames_condition = numpy.logical_and(frames.directions == 'TX',
                                              frames.mac_addresses[:, 0] == mobiles.mac_addresses[0])

    # Construct REPONSE frames filter, i.e. transmitted frames ('RX' directions) sent to mobile node
    # (frames.mac_addresses[:, 1] equal to mobile nod'se MAC address)
    response_frames_condition = numpy.logical_and(frames.directions == 'RX',
                                                  frames.mac_addresses[:, 1] == mobiles.mac_addresses[0])

    # Apply filters constructed above
    response_frames = frames[response_frames_condition]
    poll_frames = frames[poll_frames_condition]

    # Here we will store ToF between mobile node and three anchors, each row will contain ToF in ps and anchor's
    # MAC address
    time_of_flights = numpy.zeros((3, 2))

    # Iterate over POLL and RESPONSE frames
    sequence_numbers = (1, 2, 3)
    for i in range(len(sequence_numbers)):
        # Lookup POLL
        sequence_number = sequence_numbers[i]
        poll_frame = poll_frames[poll_frames.sequence_numbers == sequence_number]
        response_frame = response_frames[response_frames.sequence_numbers == sequence_number]

        # Compute ToF and fill time_of_flights array
        time_of_flights[i, 0] = response_frame.begin_timestamps[0, 0] - poll_frame.begin_positions[0, 0]
        time_of_flights[i, 1] = response_frame.mac_addresses[0, 0]

    pass  # TODO
