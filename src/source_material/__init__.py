"""Operator-curated source material loader (R5–R10 / U13).

article_engine reads operator-curated handoff content from
`clients/<slug>/source_material/` (paths referenced from
`ClientConfig.source_material_paths`). Supports markdown, PDF, and
HTML in v1 per the plan's source-material acquisition section.
"""

from src.source_material.loader import (
    SUPPORTED_SOURCE_MATERIAL_EXTENSIONS,
    SourceMaterialFile,
    UnsupportedSourceMaterialFormatError,
    load_source_material,
)

__all__ = [
    "SUPPORTED_SOURCE_MATERIAL_EXTENSIONS",
    "SourceMaterialFile",
    "UnsupportedSourceMaterialFormatError",
    "load_source_material",
]
