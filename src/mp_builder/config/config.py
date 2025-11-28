from pathlib import Path
from typing import Optional, Dict, List, Any

from pydantic import BaseModel, Field, field_validator, ValidationError
import yaml


class Workflow(BaseModel):
    id: str
    name: str
    version: str


class WorkflowOptions(BaseModel):
    wf_opts: str


class Transition(BaseModel):
    run: str
    from_: Optional[str] = Field(default=None, alias="from")
    params_file: Optional[Path] = Field(default=None, alias="params-file")
    config_file: Optional[Path] = Field(default=None, alias="config-file")
    adapter: Optional[str] = None
    params: Optional[List[Dict[str, Any]]] = None


class Config(BaseModel):
    metaworkflow_version: str
    nextflow_version: str
    workflows: List[Workflow]
    workflow_opts: Optional[WorkflowOptions] = None
    workflow_opts_custom: Optional[WorkflowOptions] = None
    metalayout: Optional[Dict[str, List[str]]] = None
    transitions: List[Transition]

    # ------------------------------
    # Validation: workflow IDs exist
    # ------------------------------
    @field_validator("metalayout")
    def valid_workflow_ids(cls, value, info):
        if value is None:
            return value
        all_ids = {w.id for w in info.data["workflows"]}
        for src, targets in value.items():
            if src not in all_ids:
                raise ValueError(f"metalayout references unknown workflow id: {src}")
            for t in targets:
                if t not in all_ids:
                    raise ValueError(f"metalayout targets unknown workflow id: {t}")
        return value

    # ------------------------------
    # Validation: transitions refer to real workflow IDs
    # ------------------------------
    @field_validator("transitions")
    def transitions_valid(cls, transitions, info):
        all_ids = {w.id for w in info.data["workflows"]}
        for tr in transitions:
            if tr.run not in all_ids:
                raise ValueError(f"transition 'run' references unknown workflow id: {tr.run}")
            if tr.from_ and tr.from_ not in all_ids:
                raise ValueError(f"transition 'from' references unknown workflow id: {tr.from_}")
        return transitions

