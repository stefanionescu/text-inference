---
license: ${license_id_yaml}
license_name: ${license_name_yaml}
license_link: ${license_link_yaml}
base_model: ${base_model_yaml}
library_name: transformers
tags:
    - compressed-tensors
    - awq
    - quantized
    - ${weight_bits}-bit
language:
    - en
pipeline_tag: text-generation
---

# ${model_name}: AWQ ${weight_bits}-bit compressed-tensors

This model was quantized with [LLM Compressor](https://github.com/vllm-project/llm-compressor) from ${source_model_link}.

The exact source revision is `${source_revision}`.

## Quantization Overview

- Quantizer version: `${quantizer_version}`
- Scheme: `${quantization_scheme}`
- Model family policy: `${model_family}`
- Weights: ${weight_bits}-bit, group size ${group_size}, zero-point ${zero_point}
- Targets: ${targets}
- Ignored modules: ${ignored_modules}

## Calibration Data

- Dataset: `${calibration_dataset}`
- Samples: ${calibration_samples}
- Max sequence length: ${calibration_sequence_length}
- Batch size: ${calibration_batch_size}
- Calibration pipeline: `${calibration_pipeline}`
- MoE expert calibration: ${expert_calibration}

## Runtime Recommendations

- Engine: vLLM `${vllm_version}`
- Load this as a `compressed-tensors` checkpoint.
- vLLM selects compute dtype, attention backend, scheduler limits, chunked prefill, and prefix-caching support from the checkpoint and GPU.
- Hybrid and MoE models use vLLM's native cache and kernel policy.

### LLM Compressor recipe and exported metadata

```json
${quantization_summary}
```

## Provenance

- Source revision: `${source_revision}`
- Generated: `${generated_at}`

## License

This quantized model inherits the license from the original base model: **${license_name}**

See the [original model's license](${license_link}) for full terms.
