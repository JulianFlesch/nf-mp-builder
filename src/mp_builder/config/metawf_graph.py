from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from pydantic import ValidationError
import networkx as nx

from .models import MetaworkflowConfig


class MetaworkflowGraph:
    """
    A wrapper around networkx.DiGraph that provides:
    - validation
    - config ↔ graph conversion
    - utilities for workflow orchestration
    """
    ROOT_NODE = "START"

    def __init__(self):
        self.G = nx.DiGraph()

    @classmethod
    def from_file(cls, cfg_file: Path) -> "MetaworkflowGraph":
        with open(cfg_file) as fh:
            data = yaml.safe_load(fh)
        
        return cls.from_config(data)

    @classmethod
    def from_config(cls, cfg_dict: Dict[str, Any]) -> "MetaworkflowGraph":
        # Validate config structure using Pydantic
        try:
            cfg = MetaworkflowConfig(**cfg_dict)
        except ValidationError as e:
            raise ValueError(f"Config validation failed:\n{e}")

        obj = cls()

        # Add workflow nodes
        for wf in cfg.workflows:
            obj.G.add_node(
                wf.id,
                name=wf.name,
                version=wf.version,
            )

        # Add transition metadata
        for t in cfg.transitions:
            src = t.from_ if t.from_ else cls.ROOT_NODE
            tgt = t.run

            if (src != cls.ROOT_NODE and src not in obj.G.nodes) or tgt not in obj.G.nodes:
                raise ValueError(f"Unknown node: {src}->{tgt}")

            if src == cls.ROOT_NODE:
                if cls.ROOT_NODE not in obj.G.nodes:
                    obj.G.add_node(cls.ROOT_NODE, virtual=True)
                obj.G.add_edge(cls.ROOT_NODE, tgt, metadata=t.dict(exclude_none=True))
            else:
                if not obj.G.has_edge(src, tgt):
                    # Transition not declared in metalayout → auto-add
                    obj.G.add_edge(src, tgt, metadata={})
                obj.G.edges[src, tgt]["metadata"].update(
                    t.dict(exclude_none=True, by_alias=True)
                )

        # Run graph validation
        obj.validate()

        return obj

    # ===========================
    #        VALIDATION
    # ===========================
    def validate(self):
        # 1. Detect cycles
        if not nx.is_directed_acyclic_graph(self.G):
            cycle = nx.find_cycle(self.G)
            raise ValueError(f"Workflow graph contains a cycle: {cycle}")

        # 2. Detect missing workflow nodes
        for src, tgt in self.G.edges():
            if src not in self.G or tgt not in self.G:
                raise ValueError(f"Edge refers to nonexistent node: {src}->{tgt}")

        # 3. Ensure workflow IDs are valid (non-empty)
        for n in self.G.nodes:
            if n == self.ROOT_NODE:
                continue
            if not isinstance(n, str) or not n:
                raise ValueError("Workflow id must be a non-empty string.")

    # ===========================
    #   EXPORT BACK TO CONFIG
    # ===========================
    def to_config(self) -> Dict[str, Any]:
        nodes = [n for n in self.G.nodes if n != self.ROOT_NODE]

        workflows = [
            {
                "id": n,
                "name": self.G.nodes[n]["name"],
                "version": self.G.nodes[n]["version"],
            }
            for n in nodes
        ]

        # metalayout adjacency list
        metalayout = {
            n: [
                t for t in self.G.successors(n)
                if t != self.ROOT_NODE
            ]
            for n in nodes
        }

        transitions = []
        for src, tgt, data in self.G.edges(data=True):
            meta = data.get("metadata", {})
            if src == self.ROOT_NODE:
                t = {"run": tgt}
            else:
                t = {"from": src, "run": tgt}

            t.update(meta)
            transitions.append(t)

        return {
            "metaworkflow_version": "0.0.1",
            "workflows": workflows,
            "metalayout": metalayout,
            "transitions": transitions,
        }

    # ===========================
    #        UTILITIES
    # ===========================
    def execution_order(self):
        """Returns workflow ids in valid execution order."""
        return [
            n for n in nx.topological_sort(self.G)
            if n != self.ROOT_NODE
        ]

    def successors(self, workflow_id: str):
        return list(self.G.successors(workflow_id))

    def predecessors(self, workflow_id: str):
        return list(self.G.predecessors(workflow_id))
