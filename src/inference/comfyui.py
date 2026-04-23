"""Backend d'inférence ComfyUI : pilote un serveur ComfyUI distant via HTTP.

Pipeline d'une génération :
1. Patcher le workflow JSON avec les params de la requête
2. POST /prompt → récupère un `prompt_id`
3. Poll GET /history/{prompt_id} jusqu'à complétion
4. Pour chaque image générée par ComfyUI : GET /view?filename=...
5. Écrire l'image sur le volume partagé `/data/images/...`
6. Retourner les `GeneratedImage`
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import httpx

from src.common.config import get_settings
from src.common.logging import get_logger
from src.common.models import GeneratedImage, PromptSpec
from src.inference.base import InferenceBackend
from src.inference.workflow_patcher import WorkflowPatcher

log = get_logger(__name__)


class ComfyUIError(Exception):
    """Erreur générique côté ComfyUI (timeout, prompt rejeté, etc.)."""


class ComfyUIBackend(InferenceBackend):
    """Backend HTTP pour ComfyUI."""

    # Limites de polling : on attend au max ~5 min par image (CPU est lent)
    POLL_INTERVAL_SECONDS = 1.0
    POLL_TIMEOUT_SECONDS = 300.0

    def __init__(
        self,
        workflow_path: str | Path,
        base_url: str | None = None,
        output_dir: str | Path = "/data/images",
        client_id: str | None = None,
    ) -> None:
        self.base_url = (base_url or get_settings().comfyui_url).rstrip("/")
        self.output_dir = Path(output_dir)
        self.client_id = client_id or str(uuid.uuid4())
        self.patcher = WorkflowPatcher.from_file(workflow_path)
        log.info(
            "comfyui_backend.init",
            base_url=self.base_url,
            output_dir=str(self.output_dir),
            client_id=self.client_id,
        )

    # =========================================================================
    # Interface InferenceBackend
    # =========================================================================
    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/system_stats")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def generate(self, spec: PromptSpec, count: int) -> list[GeneratedImage]:
        """Génère `count` images avec des seeds successives `spec.seed_start + i`.

        Les images d'un même appel `generate()` sont rangées dans un sous-dossier
        unique pour éviter les collisions de noms entre batches.
        """
        sub_dir = self.output_dir / f"batch-{spec.seed_start}-{uuid.uuid4().hex[:8]}"
        sub_dir.mkdir(parents=True, exist_ok=True)

        results: list[GeneratedImage] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(count):
                seed = spec.seed_start + i
                log.info("comfyui_backend.generate.start", seed=seed, index=i)

                workflow = self.patcher.patch(spec, seed)
                image = await self._generate_one(client, workflow, seed, sub_dir)
                results.append(image)

                log.info("comfyui_backend.generate.done", seed=seed, file_path=image.file_path)

        return results

    # =========================================================================
    # Pipeline d'une génération unique
    # =========================================================================
    async def _generate_one(
        self,
        client: httpx.AsyncClient,
        workflow: dict[str, Any],
        seed: int,
        output_subdir: Path,
    ) -> GeneratedImage:
        """Soumet un workflow, attend la complétion, télécharge l'image."""
        prompt_id = await self._submit_prompt(client, workflow)
        log.debug("comfyui.prompt.submitted", prompt_id=prompt_id, seed=seed)

        history = await self._wait_completion(client, prompt_id)
        outputs = self._extract_image_refs(history)

        if not outputs:
            raise ComfyUIError(f"Aucune image dans l'historique pour prompt_id={prompt_id}")

        # Le workflow ne génère qu'une image par run (batch_size=1)
        first = outputs[0]
        image_bytes = await self._download_image(client, **first)

        local_path = output_subdir / f"{seed}.png"
        local_path.write_bytes(image_bytes)

        # Chemin relatif au output_dir pour stockage en DB
        relative_path = str(local_path.relative_to(self.output_dir))

        # Récupère les dimensions depuis le workflow patché
        empty_latent_id = WorkflowPatcher._find_unique_node(workflow, "EmptyLatentImage")
        width = workflow[empty_latent_id]["inputs"]["width"]
        height = workflow[empty_latent_id]["inputs"]["height"]

        return GeneratedImage(
            seed=seed,
            file_path=relative_path,
            width=width,
            height=height,
        )

    # =========================================================================
    # Helpers HTTP ComfyUI
    # =========================================================================
    async def _submit_prompt(self, client: httpx.AsyncClient, workflow: dict[str, Any]) -> str:
        """POST /prompt et retourne le prompt_id."""
        payload = {"prompt": workflow, "client_id": self.client_id}
        resp = await client.post(f"{self.base_url}/prompt", json=payload)

        if resp.status_code != 200:
            raise ComfyUIError(
                f"POST /prompt a retourné {resp.status_code} : {resp.text}"
            )

        data = resp.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError(f"Réponse /prompt sans prompt_id : {data}")
        return prompt_id

    async def _wait_completion(
        self, client: httpx.AsyncClient, prompt_id: str
    ) -> dict[str, Any]:
        """Poll /history/{prompt_id} jusqu'à voir un résultat avec outputs."""
        elapsed = 0.0
        while elapsed < self.POLL_TIMEOUT_SECONDS:
            resp = await client.get(f"{self.base_url}/history/{prompt_id}")
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data and "outputs" in data[prompt_id]:
                    log.debug("comfyui.poll.complete", prompt_id=prompt_id, elapsed=elapsed)
                    return data[prompt_id]

            await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
            elapsed += self.POLL_INTERVAL_SECONDS

        raise ComfyUIError(
            f"Timeout après {self.POLL_TIMEOUT_SECONDS}s pour prompt_id={prompt_id}"
        )

    @staticmethod
    def _extract_image_refs(history: dict[str, Any]) -> list[dict[str, str]]:
        """Extrait les refs (filename, subfolder, type) des images depuis l'historique.

        Format ComfyUI :
            outputs: {
                "<save_image_node_id>": {
                    "images": [
                        {"filename": "...", "subfolder": "...", "type": "output"},
                        ...
                    ]
                }
            }
        """
        outputs = history.get("outputs", {})
        refs: list[dict[str, str]] = []
        for _node_id, node_output in outputs.items():
            for img in node_output.get("images", []):
                refs.append(
                    {
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output"),
                    }
                )
        return refs

    async def _download_image(
        self,
        client: httpx.AsyncClient,
        filename: str,
        subfolder: str,
        type: str,
    ) -> bytes:
        """GET /view?filename=...&subfolder=...&type=... → bytes de l'image."""
        params = {"filename": filename, "subfolder": subfolder, "type": type}
        resp = await client.get(f"{self.base_url}/view", params=params)
        if resp.status_code != 200:
            raise ComfyUIError(
                f"GET /view {filename} a retourné {resp.status_code} : {resp.text}"
            )
        return resp.content