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
import pandas as pd

from smile.nodes import Nodes


class Anchors(Nodes):
    @classmethod
    def load_csv(cls, file_path):
        columns = cls.__get_columns()
        return pd.read_csv(file_path, names=columns.keys(), dtype=columns)

    @classmethod
    def __get_columns(cls):
        columns = super(cls).__get_columns()
        columns['message_processing_time'] = np.int64
        return columns
