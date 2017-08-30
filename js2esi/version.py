__author__ = "Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"

IVERSION = (0, 9, 0)
VERSION = ".".join(str(i) for i in IVERSION)
JS2ESI = "js2esi " + VERSION

# Serialization format version. This is displayed nowhere, it just needs to be incremented by one
# for each change in the file format.
FLOW_FORMAT_VERSION = 5

if __name__ == "__main__":
    print(VERSION)