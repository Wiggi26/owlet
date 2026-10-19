# Raw property parser boundary

Investigation at fork base `2f1556652897ab1ec9d504017ef770ba84d363c5`, using
the retained `pyowletapi==2025.4.1`. This documents the remaining raw-field
scope of [OWL-014 / #9](https://github.com/Wiggi26/owlet/issues/9), after the
normalized-getter and numeric-validity fixes. It makes no runtime change and
does not satisfy malformed optional-field isolation acceptance.

The installed `pyowletapi.sock.Sock.update_properties()` calls the library API,
stores the response in `raw_properties`, and invokes its private normalization
method before replacing `properties` or returning tokens. The private method
casts fields with `bool`, `int` and `float`, catching only `KeyError`.

[Synthetic contract tests](../tests/test_raw_properties.py) demonstrate:

| Raw input | Retained behavior | Integration consequence |
| --- | --- | --- |
| V2/V3 optional movement `null`, signal strength `"bad"` | `TypeError` / `ValueError` aborts normalization; raw data is replaced but previous normalized properties remain stored. | The coordinator fails that whole sock poll, making unrelated entities unavailable. Its stored old readings are withheld from HA state. Another sock continues, and recovery retains registered IDs/bindings and entry data/options. |
| V2/V3 alert missing / `null` / `"false"` | Missing stays absent; other inputs become `False` / `True`. | Missing becomes unknown, but invalid present values appear as ordinary off/on states after a successful poll. |
| V2/V3 charging `0.5` / `true` | Both are cast to integers (`0` / `1`). | Original type/validity is lost; a fractional input can appear as known not charging and permit physiological values. |
| V2 base-station flag `null` / `"false"` | Values become `False` / `True`. | The switch appears off/on. V3 passes these raw values through, so existing getters correctly withhold its switch state. No commands are sent by these tests. |

Existing [numeric contracts](../tests/test_numeric_validity.py) also demonstrate
raw null/malformed float failures and boolean-to-numeric coercion. These tests
record confirmed defects; passing them proves the boundary, not a repair or
current cloud/firmware behavior. No new expected failure is introduced.
When the parser is fixed, replace defective-behavior expectations with the
intended isolation/validity assertions.

## Blocker and required follow-up

**Library normalization fix or supported pre-normalization hook required.** The
public update method exposes no per-field validation hook. Catching its exception
cannot recover unrelated current values: normalized properties still belong to
the previous poll. Reusing them would present historical readings as current.
Retrying the unchanged raw input cannot make normalization succeed. Filtering
normalized values after success cannot restore their original type/validity.
Inspecting raw values after success could identify coerced flags, but cannot
isolate a numeric field that already aborted the whole poll.

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
