"""titiler.core.algorithm."""

from copy import copy
from enum import Enum
from typing import Dict, List, Type

import attr

from titiler.core.algorithm.base import AlgorithmMetadata, BaseAlgorithm  # noqa
from titiler.core.algorithm.dem import Contours, HillShade, TerrainRGB, Terrarium
from titiler.core.algorithm.index import NormalizedIndex

default_algorithms: Dict[str, Type[BaseAlgorithm]] = {
    "hillshade": HillShade,
    "contours": Contours,
    "normalizedIndex": NormalizedIndex,
    "terrarium": Terrarium,
    "terrainrgb": TerrainRGB,
}


@attr.s(frozen=True)
class Algorithms:
    """Algorithms."""

    algos: Dict[str, Type[BaseAlgorithm]] = attr.ib()

    def get(self, name: str) -> BaseAlgorithm:
        """Fetch a TMS."""
        if name not in self.algos:
            raise KeyError(f"Invalid name: {name}")

        return self.algos[name]

    def list(self) -> List[str]:
        """List registered Algorithm."""
        return list(self.algos.keys())

    def register(
        self,
        algorithms: Dict[str, BaseAlgorithm],
        overwrite: bool = False,
    ) -> "Algorithms":
        """Register Algorithm(s)."""
        for name, algo in algorithms.items():
            if name in self.algos and not overwrite:
                raise Exception(f"{name} is already a registered. Use overwrite=True.")

        return Algorithms({**self.algos, **algorithms})

    @property
    def names(self) -> Enum:
        """return algorithms enumerations."""
        return Enum(  # type: ignore
            "AlgorithmName", [(a, a) for a in self.algos.keys()]
        )


algos = Algorithms(copy(default_algorithms))  # noqa
