from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ValidationInfo
import yaml

from mp_builder.utils import get_nfcore_pipelines

logger = logging.getLogger()

CONFIG_VERSION_MIN = "0.0.1"
CONFIG_VERSION_MAX = "0.0.1"

class Workflow(BaseModel):
    id: str
    description: Optional[str] = None
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


class MetaworkflowConfig(BaseModel):
    metaworkflow_version: str
    nextflow_version: Optional[str]
    workflows: List[Workflow]
    workflow_opts: Optional[WorkflowOptions] = None
    workflow_opts_custom: Optional[WorkflowOptions] = None
    transitions: List[Transition]

    # ------------------------------
    # Validation: transitions refer to real workflow IDs
    # ------------------------------
    @model_validator(mode="after")
    def transitions_valid(self):
        all_ids = {w.id for w in self.workflows}
        for tr in self.transitions:
            if tr.run not in all_ids:
                raise ValueError(f"transition 'run' references unknown workflow id: {tr.run}")
            if tr.from_ and tr.from_ not in all_ids:
                raise ValueError(f"transition 'from' references unknown workflow id: {tr.from_}")
        return self
    
    # ------------------------------
    # Validation: transitions refer to nf-core workflow IDs
    # ------------------------------
    @field_validator("workflows")
    @classmethod
    def workflows_exists_in_nfcore(cls, workflows):
        nf_core_pipelines = get_nfcore_pipelines()
        if not len(nf_core_pipelines):
            logging.warning("Workflows could not be validated against nf-core")
            return workflows
        
        nf_core_pipeline_names = {w.get("name") for w in nf_core_pipelines}
        unknown_workflows = []
        for w in workflows:
            if w.name not in nf_core_pipeline_names:
                unknown_workflows.append(w.name)
        if len(unknown_workflows):
            logging.warning(f"Potentially uncompatible workflows found, which are not officially supported by nf-core: %s" % ", ".join(unknown_workflows))
        return workflows


def load_config(path: Path) -> MetaworkflowConfig:
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return MetaworkflowConfig.model_validate(data)


def dump_config(config: MetaworkflowConfig, path: Path):
    with open(path, "w") as fh:
        yaml.safe_dump(config.model_dump(by_alias=True), fh, sort_keys=False)

