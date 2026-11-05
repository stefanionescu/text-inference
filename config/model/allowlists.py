"""Engine-owned model allowlists for text inference.

Base and MoE lists contain source checkpoints that the named engine can run or
quantize. Quant lists contain ready-to-run quantized checkpoints in formats
accepted by that engine.

Models supported by both engines intentionally appear in both lists, which
copy the dual-engine source lists below.
"""

_DUAL_ENGINE_BASE_MODELS: list[str] = [
    # Mistral
    "SicariusSicariiStuff/Impish_Nemo_12B",  # unstable above 0.8 temp when using 4bit quant; decent <=0.6
    "TheDrummer/Theia-21B-v2",  # mid intelligence; ok for cheaper long runs
    "TheDrummer/Rocinante-12B-v1.1",  # mid intelligence; downgrade option, weak on instruction following
    "knifeayumu/Cydonia-v1.3-Magnum-v4-22B",  # pretty bad overall
    "Doctor-Shotgun/MS3.2-24B-Magnum-Diamond",
    "zerofata/MS3.2-PaintedFantasy-Visage-33B",  # better than Cydonia but still quirky
    "mistralai/Ministral-8B-Instruct-2410",
    "mistralai/Mistral-Nemo-Instruct-2407",
    "Delta-Vector/Ohashi-NeMo-12B",
    "concedo/Beepo-22B",
    "Gryphe/Pantheon-RP-Pure-1.6.2-22b-Small",
    "mistralai/Mistral-Small-24B-Instruct-2501",
    "Gryphe/Pantheon-RP-1.6.2-22b-Small",
    "Gryphe/Pantheon-RP-1.8-24b-Small-3.1",
    "TheDrummer/UnslopNemo-12B-v4.1",  # PRETTY GOOD: needs more testing tho
    "SicariusSicariiStuff/Impish_Bloodmoon_12B",
    "SicariusSicariiStuff/Angelic_Eclipse_12B",
    "flammenai/Mahou-1.3-mistral-nemo-12B",
    "mistralai/Mistral-Small-Instruct-2409",
    "ReadyArt/Broken-Tutu-24B-Unslop-v2.0",
    "Delta-Vector/Rei-24B-KTO",
    "ArliAI/Mistral-Small-22B-ArliAI-RPMax-v1.1",
    "ArliAI/Mistral-Small-24B-ArliAI-RPMax-v1.4",
    "Naphula/Goetia-24B-v1.1",
    "ReadyArt/Broken-Tutu-24B-Transgression-v2.0",
    "TheDrummer/Magidonia-24B-v4.3",
    # Mistral 3
    "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    "mistralai/Magistral-Small-2509",
    "dphn/Dolphin-Mistral-24B-Venice-Edition",
    # Qwen 2 and QwQ
    "anthracite-org/magnum-v2-32b",  # a bit cheesy and yaps too much (good for general RP tho)
    "djuna/magnum-v2-32b-chatml",  # yaps too much; prompt tuning is the fix to try (good for general RP tho)
    "anthracite-org/magnum-v4-72b",  # amazing on OpenRouter but too big
    "anthracite-org/magnum-v1-72b",  # amazing on OpenRouter but too big
    "ArliAI/Qwen2.5-32B-ArliAI-RPMax-v1.3",
    "Qwen/QwQ-32B",
    # Qwen 3
    "ArliAI/DS-R1-Qwen3-8B-ArliAI-RpR-v4-Small",
    "Qwen/Qwen3-14B",
    "soob3123/GrayLine-Qwen3-14B",
    "Jinx-org/Jinx-Qwen3-32B",
    "Jinx-org/Jinx-Qwen3-14B",
    "Qwen/Qwen3-32B",
    "Mawdistical/Squelching-Fantasies-qw3-14B",
    # Llama and Nemotron
    "dphn/Dolphin3.0-Llama3.1-8B",
    "zerofata/L3.3-GeneticLemonade-Unleashed-v3-70B",
    "chargoddard/storytime-13b",
    "SteelStorage/L3-Aethora-15B-V2",
    "nvidia/Llama-3_1-Nemotron-51B-Instruct",
    # Gemma 4
    "google/gemma-4-31B-it",
    "llmfan46/gemma-4-31B-it-uncensored-heretic",
    "Gryphe/Gemma-4-31B-StyleTune",
]

_DUAL_ENGINE_MOE_MODELS: list[str] = [
    # Qwen 3 and Qwen 3.5
    "trohrbaugh/Qwen3.5-35B-A3B-heretic",
    "Qwen/Qwen3.5-35B-A3B",
    "llmfan46/Qwen3.5-35B-A3B-uncensored-heretic",
    "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "ArliAI/Qwen3-30B-A3B-ArliAI-RpR-v4-Fast",
    "DavidAU/Qwen3-33B-A3B-Stranger-Thoughts-IPONDER",
    "Ewere/Qwen3-30B-A3B-abliterated-erotic",
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
    "bgg1996/Melinoe-30B-A3B-Thinking",
    # DeepSeek-family architectures
    "deepseek-ai/DeepSeek-V2-Lite-Chat",
    "moonshotai/Moonlight-16B-A3B-Instruct",
    # Mixtral-family architecture
    "kakaocorp/kanana-1.5-15.7b-a3b-instruct",
    # Llama 4
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    # Gemma 4
    "google/gemma-4-26B-A4B-it",
    "TrevorJS/gemma-4-26B-A4B-it-uncensored",
    "Gryphe/Gemma-4-26B-A4B-StyleTune-V2",
    "zerofata/G4-MeroMero-26B-A4B",
    "google/gemma-4-26B-A4B-it-qat-q4_0-unquantized",
    "llmfan46/gemma-4-26B-A4B-it-qat-q4_0-unquantized-uncensored-heretic",
]

ALLOWED_VLLM_BASE_MODELS: list[str] = list(_DUAL_ENGINE_BASE_MODELS)

ALLOWED_VLLM_MOE_MODELS: list[str] = [
    *_DUAL_ENGINE_MOE_MODELS,
    # vLLM-only architectures
    "baidu/ERNIE-4.5-21B-A3B-PT",
    "moonshotai/Kimi-Linear-48B-A3B-Instruct",
    "cerebras/Kimi-Linear-REAP-35B-A3B-Instruct",
]

ALLOWED_VLLM_QUANTIZED_MODELS: list[str] = [
    # GPTQ
    "SicariusSicariiStuff/Impish_Nemo_12B_GPTQ_4-bit-32",
    "SicariusSicariiStuff/Impish_Nemo_12B_GPTQ_4-bit-64",
    "SicariusSicariiStuff/Impish_Nemo_12B_GPTQ_4-bit-128",
    "Qwen/Qwen3.5-35B-A3B-GPTQ-Int4",
    "llmfan46/gemma-4-26B-A4B-it-qat-q4_0-uncensored-heretic-GPTQ-Int4",
    "llmfan46/Qwen3.5-35B-A3B-uncensored-heretic-v2-Native-MTP-Preserved-GPTQ-Int4",
    # AWQ
    "cyankiwi/Kimi-Linear-48B-A3B-Instruct-AWQ-4bit",
    "NaomiBTW/Cydonia-v1.3-Magnum-v4-22B-AWQ",  # stupid and random as fuck
    "TheBloke/30B-Lazarus-AWQ",  # completely ignores instructions, super dumb
    "cpatonn/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit",  # GOOD but lots of GPT-isms
    "Qwen/Qwen3-32B-AWQ",
    "Qwen/Qwen3-14B-AWQ",
    "warshanks/Ministral-8B-Instruct-2410-AWQ",
    "TheBloke/mixtral-8x7b-v0.1-AWQ",
    "casperhansen/mistral-nemo-instruct-2407-awq",
    "cpatonn/Llama-3_3-Nemotron-Super-49B-v1_5-AWQ-4bit",
    "jeffcookio/Mistral-Small-3.2-24B-Instruct-2506-awq-sym",  # BEST CHAT MODEL
    # Compressed-tensors and FP8
    "mistralai/Ministral-3-14B-Instruct-2512",
    "RedHatAI/Mistral-Small-3.1-24B-Instruct-2503-quantized.w4a16",
    "RedHatAI/gemma-4-26B-A4B-it-NVFP4",
    "RedHatAI/gemma-4-31B-it-NVFP4",
    "Deaquay/G4-MeroMero-26B-A4B-NVFP4",
    "RedHatAI/Qwen3.5-35B-A3B-FP8-dynamic",
    "leon-se/gemma-3-27b-it-qat-W4A16-G128",
    "yapwithai/arliai-qwen3-30B-a3b-arliai-rpr-v4-fast-w4a16",
    "yapwithai/bgg1996-melinoe-30B-A3B-thinking-w4a16",
    # ModelOpt NVFP4
    "llmfan46/gemma-4-26B-A4B-it-qat-q4_0-uncensored-heretic-NVFP4",
    "llmfan46/gemma-4-31B-it-uncensored-heretic-NVFP4",
    "llmfan46/Qwen3.5-35B-A3B-uncensored-heretic-v2-Native-MTP-Preserved-NVFP4",
]

ALLOWED_TRT_BASE_MODELS: list[str] = list(_DUAL_ENGINE_BASE_MODELS)

ALLOWED_TRT_MOE_MODELS: list[str] = list(_DUAL_ENGINE_MOE_MODELS)

ALLOWED_TRT_QUANTIZED_MODELS: list[str] = [
    # ModelOpt checkpoints
    "yapwithai/readyart-broken-tutu-24B-transgression-v2.0-trt-awq",  # LOVE the initial reactions, gotta test more
    "llmfan46/gemma-4-26B-A4B-it-qat-q4_0-uncensored-heretic-NVFP4",
    "llmfan46/gemma-4-31B-it-uncensored-heretic-NVFP4",
    "llmfan46/Qwen3.5-35B-A3B-uncensored-heretic-v2-Native-MTP-Preserved-NVFP4",
]

__all__ = [
    "ALLOWED_TRT_BASE_MODELS",
    "ALLOWED_TRT_MOE_MODELS",
    "ALLOWED_TRT_QUANTIZED_MODELS",
    "ALLOWED_VLLM_BASE_MODELS",
    "ALLOWED_VLLM_MOE_MODELS",
    "ALLOWED_VLLM_QUANTIZED_MODELS",
]
