from __future__ import annotations


def mlx_status() -> dict[str, object]:
    try:
        import mlx.core as mx
    except ModuleNotFoundError:
        return {"available": False, "backend": "mlx", "reason": "mlx is not installed"}

    return {
        "available": True,
        "backend": "mlx",
        "default_device": str(mx.default_device()),
    }

