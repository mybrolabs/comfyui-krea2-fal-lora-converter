import json
import os
import struct

import folder_paths
from safetensors.torch import load_file, save_file


class Krea2LoraConverterFal:
    """Convert fal.ai Krea 2 LoRA (base_model.model.*) to ComfyUI format (diffusion_model.*)"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_name": (folder_paths.get_filename_list("loras"),),
                "output_name": ("STRING", {"default": ""}),
                "overwrite": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "convert"
    CATEGORY = "loaders"
    OUTPUT_NODE = True

    def convert(self, lora_name, output_name="", overwrite=False):
        input_path = folder_paths.get_full_path("loras", lora_name)
        if input_path is None:
            return (f"File not found: {lora_name}",)

        state_dict = load_file(input_path)

        prefix = "base_model.model."
        fal_keys = [k for k in state_dict if k.startswith(prefix)]

        if not fal_keys:
            sample = list(state_dict.keys())[:3]
            return (
                "No fal.ai prefix found — this file already uses ComfyUI "
                f"key names, so there is nothing to do. First keys: {sample}",
            )

        new_sd = {}
        for key, tensor in state_dict.items():
            if key.startswith(prefix):
                new_sd["diffusion_model." + key[len(prefix):]] = tensor
            else:
                new_sd[key] = tensor

        if not output_name.strip():
            base = os.path.splitext(os.path.basename(input_path))[0]
            output_name = base + "_comfyui"
        if not output_name.endswith(".safetensors"):
            output_name += ".safetensors"

        output_path = os.path.join(os.path.dirname(input_path), output_name)

        if os.path.exists(output_path) and not overwrite:
            return (f"{output_name} is already in your loras folder — enable overwrite to replace it.",)

        save_file(new_sd, output_path)
        return (
            f"OK: renamed {len(fal_keys)} keys from base_model.model.* "
            f"to diffusion_model.* and wrote {output_name}",
        )


def _read_safetensors_header(path):
    """Read only the safetensors JSON header (key names + shapes), not the tensors."""
    with open(path, "rb") as f:
        header_len = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(header_len).decode("utf-8"))
    header.pop("__metadata__", None)
    return header


try:
    import asyncio

    from aiohttp import web
    from server import PromptServer

    _routes = PromptServer.instance.routes

    @_routes.get("/mybrolabs/krea2/inspect")
    async def _krea2_inspect(request):
        lora = request.rel_url.query.get("lora", "")
        path = folder_paths.get_full_path("loras", lora)
        if path is None:
            return web.json_response({"error": f"File not found: {lora}"})

        try:
            header = _read_safetensors_header(path)
        except Exception as e:
            return web.json_response({"error": f"Cannot read safetensors header: {e}"})

        prefix = "base_model.model."
        fal_keys = [k for k in header if k.startswith(prefix)]
        if not fal_keys:
            return web.json_response({"fal_format": False})

        rank = None
        for k in fal_keys:
            if k.endswith("lora_A.weight"):
                shape = header[k].get("shape") or []
                if shape:
                    rank = shape[0]
                break

        base = os.path.splitext(os.path.basename(path))[0]
        return web.json_response({
            "fal_format": True,
            "fal_keys": len(fal_keys),
            "rank": rank,
            "suggested_name": base + "_comfyui.safetensors",
        })

    @_routes.post("/mybrolabs/krea2/convert")
    async def _krea2_convert(request):
        data = await request.json()
        node = Krea2LoraConverterFal()
        loop = asyncio.get_running_loop()
        status = await loop.run_in_executor(
            None,
            lambda: node.convert(
                data.get("lora_name", ""),
                data.get("output_name", ""),
                bool(data.get("overwrite", False)),
            )[0],
        )
        return web.json_response({"status": status})

except Exception:
    # Not running inside the ComfyUI server; the queue-based convert path still works.
    pass


WEB_DIRECTORY = "./web"

NODE_CLASS_MAPPINGS = {
    "Krea2LoraConverterFal": Krea2LoraConverterFal,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2LoraConverterFal": "Krea 2 LoRA Converter mybrolabs",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
