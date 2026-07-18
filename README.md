# comfyui-krea2-fal-lora-converter

## What this is

A ComfyUI custom node that fixes the "lora key not loaded" problem for Krea 2 LoRAs trained on fal.ai. fal.ai saves these LoRAs with PEFT-style key names that ComfyUI does not recognize, so the LoRA silently fails to apply. This node renames the keys to the format ComfyUI expects and saves a converted copy — the weights themselves are never touched.

## The problem

fal.ai exports Krea 2 LoRA keys with a `base_model.model.` prefix, while ComfyUI expects `diffusion_model.`:

```
fal:     base_model.model.blocks.0.attn.wk.lora_A.weight
ComfyUI: diffusion_model.blocks.0.attn.wk.lora_A.weight
```

When the prefix does not match, ComfyUI skips every key ("lora key not loaded") and the LoRA has no effect.

## Install

```
cd ComfyUI/custom_nodes
git clone https://github.com/mybrolabs/comfyui-krea2-fal-lora-converter
```

Then restart ComfyUI.

## Usage

1. Add the node **Krea 2 LoRA Converter (fal → ComfyUI)** (category: `loaders`).
2. Pick the fal.ai LoRA file from the `loras` dropdown.
3. Queue the workflow. The converted file is written to the same `loras` folder with a `_comfyui.safetensors` suffix (or a custom name if you set `output_name`).
4. Refresh the dropdown in your LoraLoader node and select the converted file.

## Notes

- The weights are not modified in any way — only the key names are renamed.
- If the selected file is already in ComfyUI format, the node reports that there is nothing to convert and writes no output.

## Prior art

The same key-format mismatch happens with Flux 2 LoRAs trained on fal.ai. See the Flux 2 converter: https://github.com/lovisdotio/conversion-lora-fal-to-comfy — this repo is the Krea 2 version of that fix.
