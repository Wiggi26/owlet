# Raw property parser boundary

The retained `pyowletapi==2025.4.1` still limits complete raw-field isolation
for [OWL-014 / #9](https://github.com/Wiggi26/owlet/issues/9). The original
investigation at fork base `2f1556652897ab1ec9d504017ef770ba84d363c5` established
the parser boundary below. A subsequent integration guard withholds invalid
raw flags after successful normalization; it cannot repair aborted polls.

The installed `pyowletapi.sock.Sock.update_properties()` calls the library API,
stores the response in `raw_properties`, and invokes its private normalization
method before replacing `properties` or returning tokens. The private method
casts fields with `bool`, `int` and `float`, catching only `KeyError`.

[Synthetic contract tests](../tests/test_raw_properties.py) demonstrate:

| Raw input | Retained behavior | Integration consequence |
| --- | --- | --- |
| V2/V3 optional movement `null`, signal strength `"bad"` | `TypeError` / `ValueError` aborts normalization; raw data is replaced but previous normalized properties remain stored. | The coordinator fails that whole sock poll, making unrelated entities unavailable. Its stored old readings are withheld from HA state. Another sock continues, and recovery retains registered IDs/bindings and entry data/options. |
| V2/V3 alert missing / `null` / `"false"` | Missing stays absent; other inputs become `False` / `True`. | The raw flag guard exposes unknown for these inputs, preserving unrelated measurements. |
| V2/V3 charging `0.5` / `true` | Both are cast to integers (`0` / `1`). | The guard rejects the fraction as unknown and withholds charging-sensitive entities. Boolean `true` remains valid and charging. |
| V2 base-station flag `null` / `"false"` | Values become `False` / `True`. V3 passes these raw values through. | Invalid raw values withhold switch state on both versions. Commands are unchanged; these tests send none. |

Existing [numeric contracts](../tests/test_numeric_validity.py) also demonstrate
raw null/malformed float failures and boolean-to-numeric coercion. These tests
record confirmed defects; passing them proves the remaining boundary, not full
isolation or current cloud/firmware behavior. No new expected failure is introduced.
When the parser is fixed, replace defective-behavior expectations with the
intended isolation/validity assertions.

## Post-success flag validation

After a successful library update, the coordinator records invalid flags from
the public raw snapshot without modifying either library-owned dictionary.
Existing getters withhold rejected flags. Exact booleans and exact integers
`0`/`1` remain valid, matching the existing getter policy. Other raw types or
values, including strings, fractions, nulls and containers, remain unknown
when normalization succeeds. Missing wrappers/values are also unknown.

The allowlist covers the ten exposed alert/status flags, charging and the
base-station read state. V2 uses the existing top-level property wrappers;
V3 uses the existing `chg`/`bso` fields in `REAL_TIME_VITALS`. Numeric, sleep,
freshness, alert-retention and command policies are unchanged. The guard adds
no cloud calls, library hook, pin change or registry/configuration migration.

Synthetic tests cover initial invalid flags, successive invalid values,
valid boolean/integer states, missing fields/values, recovery and two-sock
independence with preserved IDs, customisations and entry data/options.
Malformed wrappers or values that abort normalization still fail the whole
sock poll and withhold stored readings; recovery uses the next successful poll.

## Blocker and required follow-up

**Library normalization fix or supported pre-normalization hook required.** The
public update method exposes no per-field validation hook. Catching its exception
cannot recover unrelated current values: normalized properties still belong to
the previous poll. Reusing them would present historical readings as current.
Retrying the unchanged raw input cannot make normalization succeed. Filtering
normalized values after success cannot restore their original type/validity.
The post-success raw flag guard cannot isolate a numeric field, malformed
wrapper or charging value that already aborted the whole poll.

Complete isolation therefore needs a separately reviewed library change that
preserves invalid/missing values and normalizes valid fields independently, or a
supported library hook with that contract. A dependency change needs the full
[retained-library review](LIBRARY_CONTRACTS.md), including imports, exceptions,
refresh/session behavior and V2/V3 compatibility. Overriding private methods,
copying the parser or introducing another cloud client is outside this scope.

Keep the issue open with this blocker. Required future verification includes
malformed-field failure-before/success-after, honest unknown/unavailable states,
recovery and two-sock identity preservation on both locked profiles. Synthetic
missing/recovery UI and binding acceptance remains owner-run and unperformed;
no live account, device or Home Assistant access was used.
