"""
Design2Build Project Configuration Model
=========================================
Encapsulates all project setup, target device, technology stack, run mode,
and reference interpretation settings into a strongly-typed configuration.
"""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ProjectType(str, Enum):
    WEBSITE = "website"
    WEB_APP = "web_app"
    LANDING_PAGE = "landing_page"
    UI_PROTOTYPE = "ui_prototype"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    COMPONENT = "component"
    FULL_PAGE = "full_page"
    MULTIPAGE = "multipage"
    REDESIGN = "redesign"


class TargetDevice(str, Enum):
    RESPONSIVE_ALL = "responsive_all"     # Mobile + Tablet + Desktop + Wide Desktop
    MOBILE_DESKTOP = "mobile_desktop"     # Mobile (375px) + Desktop (1280px)
    MOBILE_ONLY = "mobile_only"           # Mobile (375px)
    DESKTOP_ONLY = "desktop_only"         # Desktop (1024px / 1280px)
    TABLET_ONLY = "tablet_only"           # Tablet (768px)


class ResponsiveMode(str, Enum):
    FULLY_RESPONSIVE = "fully_responsive"
    MOBILE_FOCUSED = "mobile_focused"
    DESKTOP_FOCUSED = "desktop_focused"
    FIXED_SIZE = "fixed_size"
    FLUID_GRID = "fluid_grid"
    ADAPTIVE_BREAKPOINTS = "adaptive_breakpoints"
    FIXED_DESKTOP = "fixed_desktop"
    FIXED_MOBILE = "fixed_mobile"


class ReferenceIntent(str, Enum):
    RECREATE_CLOSELY = "recreate_closely"
    EXACT_CLONE = "exact_clone"
    DESIGN_REFERENCE = "design_reference"
    RESPONSIVE_REFERENCE = "responsive_reference"
    RESPONSIVE_SYSTEM = "responsive_system"
    COMPONENT_REFERENCE = "component_reference"
    INSPIRATION = "inspiration"
    DESIGN_INSPIRATION = "design_inspiration"


class ProjectState(str, Enum):
    NEW_PROJECT = "new_project"
    EXISTING_PROJECT = "existing_project"
    MODIFY_PAGE = "modify_page"
    ADD_PAGE = "add_page"
    ADD_COMPONENT = "add_component"


class RunMode(str, Enum):
    LIVE_SERVER = "live_server"
    STATIC = "static"
    VITE_DEV = "vite_dev"
    EXISTING_SERVER = "existing_server"


@dataclass
class ProjectConfig:
    """Complete specification of project targets, stacks, and verification rules."""
    project_type: ProjectType = ProjectType.WEBSITE
    stack: str = "html_tailwind"
    target_devices: TargetDevice = TargetDevice.RESPONSIVE_ALL
    responsive_mode: ResponsiveMode = ResponsiveMode.FULLY_RESPONSIVE
    reference_intent: ReferenceIntent = ReferenceIntent.RECREATE_CLOSELY
    project_state: ProjectState = ProjectState.NEW_PROJECT
    run_mode: RunMode = RunMode.LIVE_SERVER
    reference_images: List[str] = field(default_factory=list)
    reference_map: Dict[str, str] = field(default_factory=dict)
    output_dir: str = "./output"
    additional_requirements: Optional[str] = None
    inferred_fields: List[str] = field(default_factory=list)
    confirmed: bool = False

    def resolve_viewports(self) -> List[str]:
        """Map target device configuration to exact preview renderer viewports."""
        if self.target_devices == TargetDevice.MOBILE_ONLY:
            return ["mobile"]
        elif self.target_devices == TargetDevice.DESKTOP_ONLY:
            return ["desktop", "large_desktop"]
        elif self.target_devices == TargetDevice.TABLET_ONLY:
            return ["tablet"]
        elif self.target_devices == TargetDevice.MOBILE_DESKTOP:
            return ["mobile", "desktop_wide"]
        else:  # RESPONSIVE_ALL
            return ["mobile", "tablet", "desktop", "large_desktop"]

    def format_summary(self) -> str:
        """Render a clean, formatted Markdown summary block for user review."""
        ref_display = "\n".join(f"  - {r}" for r in self.reference_images) if self.reference_images else "  None"
        
        device_labels = {
            TargetDevice.RESPONSIVE_ALL: "All Responsive Devices (Mobile, Tablet, Desktop, Wide)",
            TargetDevice.MOBILE_DESKTOP: "Mobile + Desktop",
            TargetDevice.MOBILE_ONLY: "Mobile Only (375x812px)",
            TargetDevice.DESKTOP_ONLY: "Desktop Only (1024px+)",
            TargetDevice.TABLET_ONLY: "Tablet Only (768x1024px)",
        }
        
        intent_labels = {
            ReferenceIntent.RECREATE_CLOSELY: "Close Recreation",
            ReferenceIntent.DESIGN_REFERENCE: "Design Reference (Style & Layout Guide)",
            ReferenceIntent.RESPONSIVE_REFERENCE: "Responsive Multi-Device Reference",
            ReferenceIntent.COMPONENT_REFERENCE: "Isolated Component Reference",
            ReferenceIntent.INSPIRATION: "Visual Inspiration",
        }
        
        run_labels = {
            RunMode.LIVE_SERVER: "VS Code Live Server (Static Files)",
            RunMode.STATIC: "Direct Browser Double-Click (Static Files)",
            RunMode.VITE_DEV: "Vite Development Server",
            RunMode.EXISTING_SERVER: "Existing Project Server Command",
        }
        
        inferred_note = f"*(Inferred from context: {', '.join(self.inferred_fields)})*" if self.inferred_fields else ""

        return f"""----------------------------------------
## DESIGN2BUILD PROJECT CONFIGURATION {inferred_note}

Project Type:
  {self.project_type.value.replace('_', ' ').title()}

Technology / Stack:
  {self.stack}

Target Devices:
  {device_labels.get(self.target_devices, str(self.target_devices))}

Responsive Mode:
  {self.responsive_mode.value.replace('_', ' ').title()}

Reference Intent:
  {intent_labels.get(self.reference_intent, str(self.reference_intent))}

Project State:
  {self.project_state.value.replace('_', ' ').title()}

Run Mode:
  {run_labels.get(self.run_mode, str(self.run_mode))}

Backend:
  None (Frontend Only — Zero Python/FastAPI Server Required)

References:
{ref_display}
----------------------------------------"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary with string enum values."""
        d = asdict(self)
        d["project_type"] = self.project_type.value if isinstance(self.project_type, Enum) else self.project_type
        d["target_devices"] = self.target_devices.value if isinstance(self.target_devices, Enum) else self.target_devices
        d["responsive_mode"] = self.responsive_mode.value if isinstance(self.responsive_mode, Enum) else self.responsive_mode
        d["reference_intent"] = self.reference_intent.value if isinstance(self.reference_intent, Enum) else self.reference_intent
        d["project_state"] = self.project_state.value if isinstance(self.project_state, Enum) else self.project_state
        d["run_mode"] = self.run_mode.value if isinstance(self.run_mode, Enum) else self.run_mode
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Instantiate ProjectConfig safely converting enum string values."""
        payload = dict(data)
        if "project_type" in payload and isinstance(payload["project_type"], str):
            payload["project_type"] = ProjectType(payload["project_type"])
        if "target_devices" in payload and isinstance(payload["target_devices"], str):
            payload["target_devices"] = TargetDevice(payload["target_devices"])
        if "responsive_mode" in payload and isinstance(payload["responsive_mode"], str):
            payload["responsive_mode"] = ResponsiveMode(payload["responsive_mode"])
        if "reference_intent" in payload and isinstance(payload["reference_intent"], str):
            payload["reference_intent"] = ReferenceIntent(payload["reference_intent"])
        if "project_state" in payload and isinstance(payload["project_state"], str):
            payload["project_state"] = ProjectState(payload["project_state"])
        if "run_mode" in payload and isinstance(payload["run_mode"], str):
            payload["run_mode"] = RunMode(payload["run_mode"])
        return cls(**payload)

    def save(self, filepath: Union[str, Path]):
        """Persist configuration to a JSON file."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "ProjectConfig":
        """Load configuration from a JSON file."""
        p = Path(filepath)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)
