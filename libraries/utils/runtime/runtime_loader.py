import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Callable

def load_runtime_definition(path: Path) -> Dict[str, Any]:
    """
    Load a runtime definition JSON file.
    """
    if not path.exists():
        raise FileNotFoundError(f"Runtime definition not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_kpi_registry(registry_path: Path) -> Dict[str, Callable]:
    """
    Dynamically load KPI_REGISTRY from a Python module.
    The module must define: KPI_REGISTRY: Dict[str, Callable]
    """
    if not registry_path.exists():
        raise FileNotFoundError(f"KPI registry not found: {registry_path}")
    spec = importlib.util.spec_from_file_location(
        "kpi_registry", registry_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "KPI_REGISTRY"):
        raise ValueError(
            f"{registry_path} must define KPI_REGISTRY"
        )
    return module.KPI_REGISTRY

def resolve_kpi_mapping(
    kpi_defs: List[Dict[str, Any]],
    registry: Dict[str, Callable],
    ) -> List[Dict[str, Any]]:
    """
    Convert runtime KPI definitions into the structure expected by
    generate_result_dict (with callable 'val').
    """
    resolved: List[Dict[str, Any]] = []
    for kpi in kpi_defs:
        fn_name = kpi.get("fn")
        if fn_name not in registry:
            raise ValueError(
                f"Unknown KPI function '{fn_name}'. "
                f"Available: {sorted(registry.keys())}"
            )
        resolved.append(
            {
                "name": kpi["name"],
                "key": kpi["key"],
                "type": kpi["type"],
                "val": registry[fn_name],
            }
        )
    return resolved

def load_runtime_context(runtime_dir: Path) -> Dict[str, Any]:
    """
    Load a complete runtime context from a runtime directory.
    Returns:
        { "config": <runner.json dict>,
          "kpi_mapping": <resolved KPI mapping>}
        OR {"config": <runner.json dict>}
    """
    runtime_dir = Path(runtime_dir)
    config = load_runtime_definition(runtime_dir / "runner.json")
    result = {"config": config}
    kpi_registry_path = config.get("kpi_registry")
    if kpi_registry_path:
        registry_path = (runtime_dir / kpi_registry_path).resolve()
        if not registry_path.exists():
            raise FileNotFoundError(
                f"kpi_registry declared but not found: {registry_path}"
            )
        registry = load_kpi_registry(registry_path)
        kpi_mapping = resolve_kpi_mapping(config["kpis"], registry)
        result["kpi_mapping"] = kpi_mapping
    return result