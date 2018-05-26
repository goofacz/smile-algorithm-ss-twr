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

import importlib
import os.path

import numpy as np

import smile.area as sarea
import smile.simulation as ssimulation
from smile.filter import Filter
from smile.array import Array
from smile.nodes import Nodes
from smile.results import Results
import scipy.constants as scc


class Simulation(ssimulation.Simulation):
    def __init__(self, configuration):
        self._configuration = configuration
        self.solver_configuration = self._configuration['algorithms']['tof']['solver']

        solver_module = importlib.import_module(self.solver_configuration['module'])
        self.Solver = getattr(solver_module, self.solver_configuration['class'])

        area_configuration = self._configuration['area']
        area_file_path = area_configuration['file']
        self.area = sarea.Area(area_file_path)

        self.c = scc.value('speed of light in vacuum')
        self.c *= 1e-12  # m/s -> m/ps

    def run_offline(self, directory_path):
        mobiles = Array.load_csv(Array.prepare_nodes_type(), os.path.join(directory_path, 'ss_twr_mobiles.csv'))

        mobile_frames = Array.load_csv(Array.prepare_frames_type(),
                                       os.path.join(directory_path, 'ss_twr_mobile_frames.csv'))

        anchors = Array.load_csv(Array.prepare_nodes_type([('message_processing_time', np.int64)]),
                                 os.path.join(directory_path, 'ss_twr_anchors.csv'))

        results = Array.create(Array.prepare_results_type())
        for _, mobile_node in mobiles.iterrows():
            mobile_results = self._localize_mobile(mobile_node, anchors, mobile_frames)
            if results is None:
                results = mobile_results
            else:
                results = Results(np.concatenate((results, mobile_results), axis=0))

        return results, anchors

    def _localize_mobile(self, mobile_node, all_anchors, all_mobile_frames):
        # Construct POLL frames filter, i.e. transmitted frames ('TX' directions) sent by mobile node
        #data_filter = Filter()
        #data_filter.equal("direction", hash('TX'))
        #data_filter.equal("source_mac_address", mobile_node["mac_address"])
        #poll_frames = data_filter.execute(mobile_frames)
        poll_frames = all_mobile_frames.query(f'source_mac_address == {mobile_node["mac_address"]} and direction == \'TX\'')

        # Construct REPONSE frames filter, i.e. transmitted frames ('RX' directions) sent to mobile node
        #data_filter = Filter()
        #data_filter.equal("direction", hash('RX'))
        #data_filter.equal("destination_mac_address", mobile_node["mac_address"])
        response_frames = all_mobile_frames.query(f'destination_mac_address == {mobile_node["mac_address"]} and direction == \'RX\'')

        #assert (np.unique(anchors["message_processing_time"]).shape == (1,))
        #processing_delays = all_anchors["message_processing_time"]

        sequence_numbers_triples = self._lookup_sequence_number_triples(poll_frames["sequence_number"],
                                                                        response_frames["sequence_number"])
        results = [] #Results.create_array(1, mac_address=mobile_node["mac_address"])

        for round_i in range(len(sequence_numbers_triples)):
            sequence_numbers = sequence_numbers_triples[round_i]

            #frames_filter = Filter()
            #frames_filter.is_in("sequence_number", sequence_numbers)
            #round_poll_frames = frames_filter.execute(poll_frames)
            #round_response_frames = frames_filter.execute(response_frames)
            round_poll_frames = poll_frames.query(f'sequence_number in {sequence_numbers}')
            round_response_frames = response_frames.query(f'sequence_number in {sequence_numbers}')
            anchors = all_anchors.query(f'mac_address in {list(round_response_frames["source_mac_address"])}')

            tof = round_response_frames["begin_clock_timestamp"].values
            tof -= round_poll_frames["begin_clock_timestamp"].values
            tof -= anchors["message_processing_time"].values
            tof = tof / 2

            distances = tof * self.c

            anchors_coordinates = anchors[['position_x', 'position_y']].values
            solver = self.Solver(anchors_coordinates, distances, self.solver_configuration)
            positions = solver.localize()
            position = positions[0]

            result = Results()
            result.mac_address = mobile_node["mac_address"]
            result.position_dimensions = 2
            result.position_x = position[0]
            result.position_y = position[1]
            result.position_z = 0

            results[round_i, "position_2d"] = position[0]
            results[round_i, "begin_true_position_2d"] = round_poll_frames[0, "begin_true_position_2d"]
            results[round_i, "end_true_position_2d"] = round_response_frames[2, "end_true_position_2d"]

        return results

    def _lookup_sequence_number_triples(self, poll_sequence_numbers, response_sequence_numbers):
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
