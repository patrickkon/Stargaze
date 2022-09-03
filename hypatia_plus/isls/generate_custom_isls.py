# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def generate_custom_isls(output_filename_isls, topo_filename, NUM_MASTERS, NUM_WORKERS, NUM_GS):
    """
    Generate custom ISL file, given (not a whole constellation) as input a satellite topology file.
    For now this basically returns the topo.txt itself, but with all node IDs converted to unique integers (e.g. m -> 0).
    Note: this follows the same implementation as that in provision_routes.py in k8s-emulator/
    WARNING: ensure that the positions of satellites have distances that are actually reachable from each other. This function does not perform such checking. 

    Note: currently this function is not well tested
    Note: we do not include gs-sat link here. 

    :param output_filename_isls     Output filename
    :param topo_filename            topo.txt input filename
    :param NUM_MASTERS              Number of master nodes in topo.txt
    """

    list_isls = []
    with open(topo_filename, 'r') as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 2
            left = row[0]
            right = row[1]
            if "g" in left or "g" in right:
                continue
            if "m" in left: # this is a master node:
                left = int(left.split('m')[1])
            elif "d" in left: # this is a dummy node:
                left = int(left.split('d')[1]) + NUM_MASTERS + NUM_WORKERS + NUM_GS
            else: # this is a worker node
                left = int(left) + NUM_MASTERS
            if "m" in right: # this is a master node:
                right = int(right.split('m')[1])
            elif "d" in right: # this is a dummy node:
                right = int(right.split('d')[1]) + NUM_MASTERS + NUM_WORKERS + NUM_GS
            else: # this is a worker node
                right = int(right) + NUM_MASTERS

            list_isls.append((left, right))
    
    with open(output_filename_isls, 'w+') as f:
        for (a, b) in list_isls:
            f.write(str(a) + " " + str(b) + "\n")

    return list_isls
