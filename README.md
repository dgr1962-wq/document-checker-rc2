# Document Checker RC2

**Experimental Development Preview 1 — proposed prerelease `v0.1.0-dev.1`**

An Any Key Cafe / Little Oogway independent research project by Darren Russell, developed with substantial contributions from ChatGPT, Claude and Codex. See [NOTICE](NOTICE) for roles and licensing scope.

This source release contains analytical specifications, schemas, bounded Python helpers and existing synthetic deterministic tests. It supports inspection and local contract testing; it is not a turnkey assessment service. No semantic validation, calibration, reliability, PDF equivalence, held-out performance or successful controlled assessment is claimed. Passing local checks does not establish any of those properties.

Start with [quick start](docs/QUICKSTART.md), [architecture](docs/ARCHITECTURE.md), [limitations and privacy](docs/LIMITATIONS.md), and [contributing](CONTRIBUTING.md). Please inspect, test, modify separately versioned copies and report concrete findings using synthetic reproductions.

The package preserves exact selected bytes from Neutral R1/R2, Admission 0.1.5, Pass A 0.5, Pass B 0.4.6, Operator R2.1 and the R3.1 external documentation overlay. Pass A retains its older Neutral binding; no paired A/B pipeline or Join is supplied. `tools_available=[]` is unchanged. Controlled assessment remains stopped; this release does not authorize execution.

`freezes/` contains selected immutable component artifacts, not full historical freezes. `provenance/` maps included files to original hashes and freeze identities. Use [PUBLIC-INVENTORY.json](PUBLIC-INVENTORY.json) and [SHA256SUMS](SHA256SUMS) to verify this distribution. Missing historical evidence is deliberately excluded, not reconstructed. [Scope and exclusions](docs/SCOPE.md) explain the boundary.

Licensed under [Apache-2.0](LICENSE) for rights the respective licensors can grant. Upstream licenses and notices remain applicable. This grants no ownership in provider services and makes no exclusive-copyright claim about AI-generated text.
