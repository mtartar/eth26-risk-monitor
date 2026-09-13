#!/usr/bin/env bash
# Regenerate the compiled protobuf/gRPC stubs in monitor/substreams_pb/ from
# the source .proto files in protos/. Run from the repo root after changing
# any .proto file. Requires `pip install -r requirements-dev.txt` (grpcio-tools).
set -euo pipefail

cd "$(dirname "$0")/.."

python -m grpc_tools.protoc \
  -I protos \
  --python_out=monitor/substreams_pb \
  --pyi_out=monitor/substreams_pb \
  --grpc_python_out=monitor/substreams_pb \
  protos/sf/substreams/v1/package.proto \
  protos/sf/substreams/v1/modules.proto \
  protos/sf/substreams/v1/clock.proto \
  protos/sf/substreams/rpc/v2/service.proto \
  protos/contract/v1/contract.proto

echo "Generated stubs in monitor/substreams_pb/"
