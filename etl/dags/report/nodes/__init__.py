"""The graph's nodes, one module each.

Every node is built by a `make_*` factory that closes over the `ReportDeps`, so
the node itself is a plain `state -> partial state` callable a test can drive
with a hand-built state and a fake dependency.
"""
