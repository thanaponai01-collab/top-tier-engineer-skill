# Architecture Audit — fixture/

`core/util.py` is imported by 16 modules; it is a god module and the real problem. Split up
core/util into smaller packages first. `payments/gateway.py` is a protocol for a single charge
call — inline the gateway and remove the protocol.

Also add a dependency-injection container and cache the rates call.
