"""Persisted model mappings."""

from game_catalog.persistence.models.identity import (
    Game,
    GameAlias,
    GameContent,
    GameEdition,
    GameRelation,
    Product,
    Release,
)
from game_catalog.persistence.models.operations import Backup, ExecutionRun, SchemaMetadata
from game_catalog.persistence.models.reference import (
    Company,
    Ecosystem,
    Franchise,
    FranchiseEcosystem,
    Manufacturer,
    Platform,
    Region,
)

__all__ = [
    "Backup",
    "Company",
    "Ecosystem",
    "ExecutionRun",
    "Franchise",
    "FranchiseEcosystem",
    "Game",
    "GameAlias",
    "GameContent",
    "GameEdition",
    "GameRelation",
    "Manufacturer",
    "Platform",
    "Product",
    "Region",
    "Release",
    "SchemaMetadata",
]
