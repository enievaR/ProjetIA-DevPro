"""Module de patching de workflows ComfyUI.

Auto-détecte les nodes à modifier par leur `class_type` plutôt que par ID,
ce qui rend le code robuste à la régénération du workflow depuis l'UI.

Pour distinguer le CLIPTextEncode positive du négatif, on suit les références
depuis le KSampler (qui a deux entrées nommées `positive` et `negative`).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from src.common.logging import get_logger
from src.common.models import PromptSpec

log = get_logger(__name__)

# Type alias pour la lisibilité
WorkflowDict = dict[str, dict[str, Any]]


class WorkflowPatchError(Exception):
    """Levé quand le workflow ne contient pas les nodes attendus."""


class WorkflowPatcher:
    """Charge un workflow ComfyUI JSON et applique des patches dynamiques.

    Usage :
        patcher = WorkflowPatcher.from_file("workflows/sd15_txt2img.json")
        patched = patcher.patch(spec=PromptSpec(...), seed=42)
        # patched est un dict prêt à être POST-é à ComfyUI /prompt
    """

    def __init__(self, template: WorkflowDict) -> None:
        self.template = template
        # Indexe les nodes par class_type au chargement, validation immédiate
        self._validate()

    @classmethod
    def from_file(cls, path: str | Path) -> WorkflowPatcher:
        """Charge un workflow depuis un fichier JSON."""
        with Path(path).open(encoding="utf-8") as f:
            template = json.load(f)
        log.info("workflow.loaded", path=str(path), node_count=len(template))
        return cls(template)

    # -------------------------------------------------------------------------
    # Helpers de découverte de nodes
    # -------------------------------------------------------------------------
    @staticmethod
    def _find_nodes_by_type(workflow: WorkflowDict, class_type: str) -> list[str]:
        """Retourne les IDs des nodes ayant le `class_type` donné."""
        return [
            node_id
            for node_id, node in workflow.items()
            if node.get("class_type") == class_type
        ]

    @staticmethod
    def _find_unique_node(workflow: WorkflowDict, class_type: str) -> str:
        """Retourne l'ID unique d'un node, ou lève si 0 ou >1 trouvés."""
        ids = WorkflowPatcher._find_nodes_by_type(workflow, class_type)
        if len(ids) == 0:
            raise WorkflowPatchError(f"Aucun node de type '{class_type}' trouvé")
        if len(ids) > 1:
            raise WorkflowPatchError(
                f"Plusieurs nodes de type '{class_type}' trouvés ({len(ids)}), "
                f"attendu : 1. IDs : {ids}"
            )
        return ids[0]

    @staticmethod
    def _resolve_input_node(workflow: WorkflowDict, source_node_id: str, input_name: str) -> str:
        """Résout la référence d'un input vers son node source.

        Dans ComfyUI, les inputs reliés à d'autres nodes sont sous la forme
        `[node_id, output_index]`. Cette fonction retourne le `node_id`.
        """
        node = workflow[source_node_id]
        input_value = node["inputs"].get(input_name)
        if not isinstance(input_value, list) or len(input_value) != 2:
            raise WorkflowPatchError(
                f"Le node {source_node_id} n'a pas d'input '{input_name}' référencé "
                f"(valeur : {input_value})"
            )
        return str(input_value[0])

    # -------------------------------------------------------------------------
    # Validation au chargement
    # -------------------------------------------------------------------------
    def _validate(self) -> None:
        """Vérifie que le workflow contient tout ce qu'on a besoin de patcher."""
        ksampler_id = self._find_unique_node(self.template, "KSampler")
        self._find_unique_node(self.template, "EmptyLatentImage")

        # Suit les refs depuis KSampler pour identifier positive vs negative
        positive_clip_id = self._resolve_input_node(self.template, ksampler_id, "positive")
        negative_clip_id = self._resolve_input_node(self.template, ksampler_id, "negative")

        if self.template[positive_clip_id]["class_type"] != "CLIPTextEncode":
            raise WorkflowPatchError(
                f"Le node 'positive' du KSampler (id={positive_clip_id}) n'est pas un CLIPTextEncode"
            )
        if self.template[negative_clip_id]["class_type"] != "CLIPTextEncode":
            raise WorkflowPatchError(
                f"Le node 'negative' du KSampler (id={negative_clip_id}) n'est pas un CLIPTextEncode"
            )

        log.info(
            "workflow.validated",
            ksampler_id=ksampler_id,
            positive_clip_id=positive_clip_id,
            negative_clip_id=negative_clip_id,
        )

    # -------------------------------------------------------------------------
    # Patching
    # -------------------------------------------------------------------------
    def patch(self, spec: PromptSpec, seed: int) -> WorkflowDict:
        """Applique les paramètres de `spec` + seed sur une copie du template.

        Le template d'origine n'est jamais modifié (deep copy).
        """
        wf = copy.deepcopy(self.template)

        ksampler_id = self._find_unique_node(wf, "KSampler")
        empty_latent_id = self._find_unique_node(wf, "EmptyLatentImage")
        positive_clip_id = self._resolve_input_node(wf, ksampler_id, "positive")
        negative_clip_id = self._resolve_input_node(wf, ksampler_id, "negative")

        # Patch des prompts
        wf[positive_clip_id]["inputs"]["text"] = spec.prompt
        wf[negative_clip_id]["inputs"]["text"] = spec.negative_prompt

        # Patch de la résolution
        wf[empty_latent_id]["inputs"]["width"] = spec.width
        wf[empty_latent_id]["inputs"]["height"] = spec.height

        # Patch de la seed
        wf[ksampler_id]["inputs"]["seed"] = seed

        log.debug(
            "workflow.patched",
            seed=seed,
            width=spec.width,
            height=spec.height,
            prompt_len=len(spec.prompt),
        )
        return wf