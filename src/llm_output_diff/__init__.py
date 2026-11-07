"""Diff two LLM outputs by JSON field, number and claim."""

from __future__ import annotations

import logging

from .core import (
    Change,
    DiffError,
    DiffErrorCode,
    DiffReport,
    Kind,
    Mode,
    ReportFormat,
    diff_json,
    diff_outputs,
    diff_text,
    format_report,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "Change",
    "DiffError",
    "DiffErrorCode",
    "DiffReport",
    "Kind",
    "Mode",
    "ReportFormat",
    "__version__",
    "diff_json",
    "diff_outputs",
    "diff_text",
    "format_report",
]

__version__ = "0.1.0"
