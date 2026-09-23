"""
HarnessAdapter Interface
========================
Abstract base class defining the contract for AI coding agent harnesses
(Antigravity, Codex, Claude Code, and Standalone API runners).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class VisualAnalysis:
    """Structured inspection of the reference screenshot."""
    layout_hierarchy: List[str] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    typography_styles: List[str] = field(default_factory=list)
    candidate_assets: List[Dict[str, Any]] = field(default_factory=list)
    suggested_stack: str = "html_tailwind"
    raw_summary: str = ""


@dataclass
class GenerationContext:
    """Context passed to the harness to generate initial code."""
    screenshot_path: Path
    stack: str
    extracted_assets: Dict[str, str] = field(default_factory=dict)
    additional_instructions: Optional[str] = None
    project_dir: Optional[Path] = None
    config: Optional[Any] = None


@dataclass
class RefinementContext:
    """Context passed to the harness to apply iterative visual fixes."""
    screenshot_path: Path
    rendered_screenshot_path: Path
    current_code: str
    discrepancy_notes: str
    project_dir: Optional[Path] = None
    selected_element_html: Optional[str] = None
    iteration: int = 1
    config: Optional[Any] = None


class HarnessAdapter(ABC):
    """Abstract interface for driving Design2Build workflows across agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the harness (e.g. 'antigravity', 'standalone', 'claude_code', 'codex')."""
        pass

    @abstractmethod
    async def analyze_visual(self, image_path: Path, prompt: str = "") -> VisualAnalysis:
        """Inspect reference screenshot to extract composition, assets, and hierarchy."""
        pass

    @abstractmethod
    async def generate_code(self, context: GenerationContext) -> str:
        """Generate full, self-contained project code matching the screenshot."""
        pass

    @abstractmethod
    async def refine_code(self, context: RefinementContext) -> str:
        """Apply surgical corrections to the code based on visual discrepancies."""
        pass
