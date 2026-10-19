# Retained library contracts

Retain `pyowletapi==2025.4.1`. It requires Python `>=3.10` and unbounded
`aiohttp`; inspected newer versions remove exception imports used here.
Package hashes and the comparison are recorded in the
[audit](AUDIT.md#dependency-versions-and-release-mismatch). Any upgrade needs
separate compatibility and privacy review.

[Contract tests](../tests/test_library_contracts.py) exercise real `OwletAPI`
and `Sock` methods through a strict fake HTTP session. Requests must match the
queue exactly; unexpected calls, unused responses and unapproved session closes
fail. Endpoints, credentials and payloads are synthetic, and sockets stay blocked.
[Dependency tests](../tests/test_dependency.py) check metadata, imports and exceptions.

The important observed limitations are:

- A property poll makes four HTTP calls, including validation and activation.
  Discovery makes `2 + 4N` calls for N candidates; refresh adds three on tested
  paths. These counts are examples, not upper bounds.
- Only HTTP 200/201 succeed. Validation failures, including 429/5xx, trigger
  refresh; ordinary operation failures raise `OwletConnectionError`.
  `Retry-After` is ignored. Handling remains [#12](https://github.com/Wiggi26/owlet/issues/12).
- Refresh can update client tokens without returning them in property/discovery
  envelopes. Partial exchanges can mutate token state. Persistence and concurrency
  remain [#8](https://github.com/Wiggi26/owlet/issues/8).
- V2/V3 normalization is covered. V3 timestamps lose their UTC marker, and sleep
  codes are converted to integers without validation or interpretation. Freshness
  remains [#11](https://github.com/Wiggi26/owlet/issues/11).
- Commands return response truthiness, including true for a nonempty error mapping;
  this does not confirm device action. Command handling remains
  [#15](https://github.com/Wiggi26/owlet/issues/15).
- Explicit library `close()` closes even a supplied session. Integration unload
  must preserve Home Assistant's shared session.

Use the locked profiles in [TESTING.md](TESTING.md); exact results are linked from
[PR #30](https://github.com/Wiggi26/owlet/pull/30). Existing strict expected failures
remain separate from passes, and coverage measures integration source. These
offline contracts do not establish live cloud, firmware or hardware compatibility.
