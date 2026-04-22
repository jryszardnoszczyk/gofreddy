"""Cross-pipeline primitives shared by harness, autoresearch, and audit pipelines.

Sub-packages co-locate utilities that were duplicated or about to diverge across
pipelines. Each sub-package documents its threat model and consumer pattern;
nothing here unifies behavior — the shared root is for *primitives*, not for
hidden frameworks.
"""
