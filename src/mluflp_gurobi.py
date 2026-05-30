from __future__ import annotations
import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import gurobipy as gp
from gurobipy import GRB

@dataclass(frozen=True)
class Site:
    site_id: str
    fixed_cost: float

@dataclass(frozen=True)
class Level:
    name: str
    sites: list[Site]

@dataclass(frozen=True)
class Instance:
    levels: list[Level]
    clients: list[str]
    transitions: list[dict[str, dict[str, float]]]

def load_instance(path: Path) -> Instance:
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    levels = [
        Level(
            name=level["name"],
            sites=[Site(site["id"], float(site["fixed_cost"])) for site in level["sites"]],
        )
        for level in raw["levels"]
    ]
    clients = [client["id"] for client in raw["clients"]]
    transitions = raw["transitions"]
    if len(transitions) != len(levels):
        raise ValueError(
            "O número de matrizes de transporte deve ser igual ao número de níveis de instalações."
        )
    return Instance(levels=levels, clients=clients, transitions=transitions)


def build_model(instance: Instance) -> tuple[gp.Model, dict[str, gp.Var], dict[tuple[int, str, str], gp.Var]]:
    model = gp.Model("mluflp")
    model.Params.OutputFlag = 0
    y: dict[str, gp.Var] = {}
    for level in instance.levels:
        for site in level.sites:
            y[site.site_id] = model.addVar(vtype=GRB.BINARY, name=f"y[{site.site_id}]")
    z: dict[tuple[int, str, str], gp.Var] = {}
    for transition_idx, transition in enumerate(instance.transitions):
        for source_id, destinations in transition.items():
            for dest_id in destinations:
                z[(transition_idx, dest_id, source_id)] = model.addVar(
                    vtype=GRB.CONTINUOUS,
                    lb=0.0,
                    name=f"z[{transition_idx},{dest_id},{source_id}]",
                )
    model.update()
    objective = gp.quicksum(site.fixed_cost * y[site.site_id] for level in instance.levels for site in level.sites)
    for transition_idx, transition in enumerate(instance.transitions):
        for source_id, destinations in transition.items():
            for dest_id, cost in destinations.items():
                objective += cost * z[(transition_idx, dest_id, source_id)]
    model.setObjective(objective, GRB.MINIMIZE)
    num_clients = len(instance.clients)
    first_transition = instance.transitions[0]
    last_facility_level = instance.levels[-1]
    for client_id in instance.clients:
        model.addConstr(
            gp.quicksum(z[(len(instance.levels) - 1, client_id, source.site_id)] for source in last_facility_level.sites)
            == 1,
            name=f"client_assignment[{client_id}]",
        )
    for level_idx in range(1, len(instance.levels)):
        current_level = instance.levels[level_idx]
        previous_level = instance.levels[level_idx - 1]
        next_is_clients = level_idx == len(instance.levels) - 1
        for site in current_level.sites:
            inflow = gp.quicksum(
                z[(level_idx - 1, site.site_id, source.site_id)] for source in previous_level.sites
            )
            if next_is_clients:
                outflow = gp.quicksum(
                    z[(level_idx, client_id, site.site_id)] for client_id in instance.clients
                )
            else:
                next_level = instance.levels[level_idx + 1]
                outflow = gp.quicksum(
                    z[(level_idx, dest.site_id, site.site_id)] for dest in next_level.sites
                )
            model.addConstr(inflow == outflow, name=f"flow_balance[{level_idx},{site.site_id}]")
    for level_idx, level in enumerate(instance.levels):
        if level_idx == len(instance.levels) - 1:
            destinations = instance.clients
            for source in level.sites:
                for client_id in destinations:
                    model.addConstr(
                        z[(level_idx, client_id, source.site_id)] <= num_clients * y[source.site_id],
                        name=f"open_link[{level_idx},{client_id},{source.site_id}]",
                    )
        else:
            next_level = instance.levels[level_idx + 1]
            for source in level.sites:
                for dest in next_level.sites:
                    model.addConstr(
                        z[(level_idx, dest.site_id, source.site_id)] <= num_clients * y[source.site_id],
                        name=f"open_link[{level_idx},{dest.site_id},{source.site_id}]",
                    )
    model.optimize()
    return model, y, z

def extract_paths(instance: Instance, z: dict[tuple[int, str, str], gp.Var]) -> dict[str, list[str]]:
    paths: dict[str, list[str]] = {}
    last_level_idx = len(instance.levels) - 1
    for client_id in instance.clients:
        path = [client_id]
        current_node = client_id
        for level_idx in range(last_level_idx, -1, -1):
            candidates = []
            if level_idx == last_level_idx:
                sources = instance.levels[level_idx].sites
            else:
                sources = instance.levels[level_idx].sites
            for source in sources:
                var = z[(level_idx, current_node, source.site_id)]
                if var.X > 1e-6:
                    candidates.append((var.X, source.site_id))
            if not candidates:
                break
            candidates.sort(reverse=True)
            _, selected_source = candidates[0]
            path.append(selected_source)
            current_node = selected_source
        paths[client_id] = list(reversed(path))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve a formulação MILP do artigo via Gurobi.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "article_example.json",
        help="Caminho para o arquivo JSON com a instância.",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=None,
        help="Limite de tempo do Gurobi em segundos.",
    )
    parser.add_argument(
        "--check-optimal",
        action="store_true",
        help="Valida o valor ótimo esperado do exemplo do artigo.",
    )
    args = parser.parse_args()
    instance = load_instance(args.data)
    model, y, z = build_model(instance)
    if args.time_limit is not None:
        model.Params.TimeLimit = args.time_limit
        model.optimize()
    if model.SolCount == 0:
        raise RuntimeError("O modelo não encontrou solução viável.")
    opened = [site_id for site_id, var in y.items() if var.X > 0.5]
    paths = extract_paths(instance, z)
    print(f"Objetivo: {model.ObjVal:.0f}")
    print(f"Instalações abertas: {', '.join(opened)}")
    print("Caminhos por cliente:")
    for client_id, path in paths.items():
        print(f"  {client_id}: {' -> '.join(path)}")
    if args.check_optimal:
        expected = 329.0
        if abs(model.ObjVal - expected) > 1e-6:
            raise AssertionError(f"Valor ótimo inesperado: {model.ObjVal}, esperado: {expected}")
        print("Validação do exemplo do artigo concluída com sucesso.")

if __name__ == "__main__":
    main()
