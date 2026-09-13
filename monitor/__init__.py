"""Real-time DeFi lending risk monitor."""

import os
import sys

# grpc_tools.protoc generates absolute imports inside the compiled stubs
# (e.g. `from sf.substreams.v1 import modules_pb2`), regardless of where the
# generated files actually live on disk. That only resolves if the directory
# *containing* `sf/` and `contract/` is itself on sys.path — importing them
# as `monitor.substreams_pb.sf...` would not satisfy those internal imports.
# This runs once, whenever `monitor` is first imported, so the rest of the
# codebase can just do `from sf.substreams.rpc.v2 import service_pb2`.
_SUBSTREAMS_PB_DIR = os.path.join(os.path.dirname(__file__), "substreams_pb")
if _SUBSTREAMS_PB_DIR not in sys.path:
    sys.path.insert(0, _SUBSTREAMS_PB_DIR)
