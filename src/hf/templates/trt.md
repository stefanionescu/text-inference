---
license: ${license_id_yaml}
license_name: ${license_name_yaml}
license_link: ${license_link_yaml}
base_model: ${base_model_yaml}
library_name: transformers
tags:
    - tensorrt-llm
    - modelopt
    - quantized
    - ${quantization_format}
language:
    - en
pipeline_tag: text-generation
---

# ${model_name}: ${quantization_label} (TensorRT-LLM)

This is a ${quantization_label} quantized version of ${source_model_link}, exported as a portable NVIDIA Model Optimizer Hugging Face checkpoint for TensorRT-LLM.

The exact source revision is `${source_revision}`.

---

## Model Overview

**Key Features:**

- **High-Performance Inference**: Prepared for the TensorRT-LLM public PyTorch backend
- **Memory Efficient**: Uses ${weight_precision} weights
- **Checkpoint Native**: No serialized TensorRT engine is included or required
- **Portable Provenance**: Quantization inputs and exported metadata are recorded with the checkpoint

---

## Technical Specifications

| Specification           | Details                   |
| ----------------------- | ------------------------- |
| **Source Model**        | ${source_model_link}      |
| **Source Revision**     | `${source_revision}`      |
| **Quantization Method** | ${quantization_label}     |
| **Precision**           | ${weight_precision}       |
| **KV Cache Format**     | ${kv_cache_format}        |
| **AWQ Block Size**      | ${awq_block_size}         |
| **Model Optimizer**     | `${modelopt_version}`     |
| **ModelOpt Revision**   | `${modelopt_revision}`    |
| **TensorRT-LLM Tested** | `${tensorrt_llm_version}` |
| **Quantization GPU**    | ${gpu_name}               |
| **SM Architecture**     | ${sm_arch}                |
| **CUDA Toolkit**        | ${cuda_version}           |
| **Python**              | ${python_version}         |
| **Generated**           | ${generated_at}           |

---

## Artifact Layout

```text
config.json
model*.safetensors
tokenizer_config.json
tokenizer assets
quantization_metadata.json
README.md
```

---

## Quantization Details

| Parameter                  | Value                          |
| -------------------------- | ------------------------------ |
| **Method**                 | ${quantization_label}          |
| **Calibration Dataset**    | `${calibration_dataset}`       |
| **Calibration Size**       | ${calibration_samples} samples |
| **Calibration Seq Length** | ${calibration_sequence_length} |
| **Calibration Batch Size** | ${calibration_batch_size}      |
| **GPU Memory Fraction**    | ${gpu_memory_fraction}         |
| **Sequential Device Map**  | ${sequential_device_map}       |
| **AWQ Block Size**         | ${awq_block_size}              |

Model Optimizer calculates calibration batch size from available GPU memory.

```json
${quantization_summary}
```

---

## Compatibility

### Requirements

- **GPU**: ${gpu_requirement}
- **TensorRT-LLM**: `${tensorrt_llm_version}`
- **Python**: ${python_requirement}

### Portability Notes

- The ModelOpt Hugging Face checkpoint is portable across compatible TensorRT-LLM installations.
- Runtime tensor parallelism, batching, and sequence limits are selected at deployment time.
- Serialized `rank*.engine` artifacts are not part of this repository design.

---

## Troubleshooting

### Checkpoint Metadata Is Rejected

Confirm that `config.json` contains the ModelOpt unified `quantization_config` and that `quantization_metadata.json` describes the same format.

### Calibration Runs Out of Memory

Model Optimizer automatically sizes calibration batches. Enable sequential device mapping and reduce its GPU memory fraction when model loading requires additional headroom.

---

## Resources

- [TensorRT-LLM Documentation](https://nvidia.github.io/TensorRT-LLM/)
- [NVIDIA Model Optimizer](https://github.com/NVIDIA/Model-Optimizer)
- [Source Model](${license_link})

---

## License

This quantized model inherits the license from the original base model: **${license_name}**

See the [original model's license](${license_link}) for full terms.
