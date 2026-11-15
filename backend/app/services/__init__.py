"""
Backend services package.
Contains pipeline adapter and business logic layer.
"""

from backend.app.services.pipeline_adapter import pipeline_adapter, EduHyperRAGPipelineAdapter

__all__ = ["pipeline_adapter", "EduHyperRAGPipelineAdapter"]
