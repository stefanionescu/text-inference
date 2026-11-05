"""Unit tests for model-aware vLLM quantization policy."""

import pytest

from config.model.vllm import MOE_WNA16_BACKEND
from config.model.quantization import GPTQ_FORMAT, COMPRESSED_TENSORS_FORMAT
from src.quantization.vllm.policy import (
    select_policy,
    validate_sequence_length,
    choose_quantization_backend,
)


def test_dense_selects_asymmetric() -> None:
    """Test dense configuration selects the dense accuracy policy."""
    model_config = {"model_type": "dense-transformer"}
    policy = select_policy(model_config, model_config)

    assert policy.model_family == "dense"
    assert policy.is_symmetric is False
    assert policy.awq_duo_scaling == "both"
    assert policy.is_all_expert_calibration is False


def test_qwen_moe_symmetric() -> None:
    """Test Qwen3 MoE selects its validated symmetric recipe."""
    model_config = {"model_type": "qwen3_moe", "num_experts": 128}
    policy = select_policy(model_config, model_config)

    assert policy.model_family == "moe"
    assert policy.is_symmetric is True
    assert policy.is_all_expert_calibration is True
    assert "re:.*mlp.gate$" in policy.ignored_modules


def test_qwen_next_gate() -> None:
    """Test Qwen3 Next leaves its shared expert gate unquantized."""
    model_config = {"model_type": "qwen3_next", "num_experts": 512}
    policy = select_policy(model_config, model_config)

    assert "re:.*mlp.shared_expert_gate$" in policy.ignored_modules


@pytest.mark.parametrize(
    ("model_type", "text_config"),
    [
        ("qwen3_5_moe", {"num_experts": 256}),
        ("qwen3_vl_moe", {"num_experts": 128}),
        ("kimi_linear", {"num_experts": 384}),
        ("llama4", {"num_local_experts": 16}),
        ("ernie4_5_moe", {"moe_num_experts": 64}),
    ],
)
def test_unsupported_moe_rejected(
    model_type: str,
    text_config: dict[str, object],
) -> None:
    """Test nested and alternate expert fields cannot select a generic recipe.

    Args:
        model_type: Type of the model.
        text_config: Text config.

    """
    with pytest.raises(ValueError, match="is not supported"):
        select_policy({"model_type": model_type}, text_config)


def test_text_sequence_limit() -> None:
    """Test the nested text-model context limit constrains calibration."""
    with pytest.raises(ValueError, match="exceeds model limit"):
        validate_sequence_length({"max_position_embeddings": 256}, 512)


def test_qwen_gptq_backend() -> None:
    """Test Qwen 3.5 GPTQ checkpoints select vLLM's expert kernel."""
    model_config = {"model_type": "qwen3_5_moe"}

    backend = choose_quantization_backend(GPTQ_FORMAT, model_config)

    assert backend == MOE_WNA16_BACKEND


def test_other_gptq_backend() -> None:
    """Test another MoE architecture keeps vLLM's automatic GPTQ policy."""
    model_config = {"model_type": "gemma4", "num_experts": 128}

    backend = choose_quantization_backend(GPTQ_FORMAT, model_config)

    assert backend == GPTQ_FORMAT


def test_qwen_artifact_format() -> None:
    """Test non-GPTQ Qwen 3.5 checkpoints keep their configured format."""
    model_config = {"model_type": "qwen3_5_moe"}

    backend = choose_quantization_backend(COMPRESSED_TENSORS_FORMAT, model_config)

    assert backend == COMPRESSED_TENSORS_FORMAT
