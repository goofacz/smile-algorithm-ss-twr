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

import unittest
import ss_twr.algorithm


class TestAlgorithm(unittest.TestCase):
    def test__lookup_sequence_number_triples(self):
        a = (0, 1, 2, 3, 4, 5)
        b = (0, 1, 2, 3, 4, 5)
        result = ss_twr.algorithm._lookup_sequence_number_triples(a, b)
        self.assertSequenceEqual(result, [[0, 1, 2], [3, 4, 5]])

        a = (0, 1, 2, 3, 4, 5)
        b = (0, 1, 2, 3, 4)
        result = ss_twr.algorithm._lookup_sequence_number_triples(a, b)
        self.assertSequenceEqual(result, [[0, 1, 2]])

        a = (0, 1, 2, 3, 4, 6, 7, 8)
        b = (0, 1, 2, 3, 6, 7, 8)
        result = ss_twr.algorithm._lookup_sequence_number_triples(a, b)
        self.assertSequenceEqual(result, [[0, 1, 2], [6, 7, 8]])


if __name__ == '__main__':
    unittest.main()
