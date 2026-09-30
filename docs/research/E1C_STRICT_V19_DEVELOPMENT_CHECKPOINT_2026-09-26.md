# E1-C Strict-v19 development checkpoint — 2026-09-26

Strict-v19 tested complete-production-source AST assignment corroboration using only already-exposed development sources. It did not modify frozen predecessors or inspect a new independent canary. Provider/model calls remained zero.

Focused regression: **48 passed**. Exposed development replay: **6/6 executable, 4/6 consensus**. Replay SHA-256: `00a9e3f7fec6a509b1fe2b3ab804c529ea24f915d79888a950503c7ca49517d9`.

The full source is available and useful, but repository-wide `self.model = ...` ownership is legitimately non-unique across Django managers, options, queries, fields, descriptors, and reverse relations. Strict-v19 deliberately requires a unique production file for repository-wide attribute assignment evidence, so `django__django-13233` remains uncorroborated. Selecting an arbitrary matching assignment would weaken fail-closed semantics and is rejected.

The next legal development direction is therefore **bounded full-source dataflow**: derive a type/module boundary from task-agnostic issue/localization evidence first, then use complete-source AST only inside that independently justified boundary. Strict-v19 is not frozen; no new canary is consumed. Official image, live, C5, DEV30, and Fresh30 remain closed.
