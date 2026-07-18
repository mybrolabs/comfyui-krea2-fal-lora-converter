import os
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
                "Already ComfyUI-compatible (not the fal format). "
                f"Nothing to convert. Sample keys: {sample}",
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
            return (f"Output already exists: {output_name}. Set overwrite=true to replace.",)

        save_file(new_sd, output_path)
        return (
            f"OK: {len(fal_keys)} keys converted "
            f"(base_model.model. -> diffusion_model.). Saved: {output_name}",
        )


NODE_CLASS_MAPPINGS = {
    "Krea2LoraConverterFal": Krea2LoraConverterFal,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2LoraConverterFal": "Krea 2 LoRA Converter (fal → ComfyUI)",
}
