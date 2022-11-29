"""titiler.core.algorithm."""

import json
from copy import copy
from typing import Dict, List, Literal, Optional, Type

import attr
from pydantic import ValidationError

from titiler.core.algorithm.base import AlgorithmMetadata, BaseAlgorithm  # noqa
from titiler.core.algorithm.dem import Contours, HillShade, TerrainRGB, Terrarium
from titiler.core.algorithm.index import NormalizedIndex

from fastapi import HTTPException, Query

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

    data: Dict[str, Type[BaseAlgorithm]] = attr.ib()

    def get(self, name: str) -> BaseAlgorithm:
        """Fetch a TMS."""
        if name not in self.data:
            raise KeyError(f"Invalid name: {name}")

        return self.data[name]

    def list(self) -> List[str]:
        """List registered Algorithm."""
        return list(self.data.keys())

    def register(
        self,
        algorithms: Dict[str, BaseAlgorithm],
        overwrite: bool = False,
    ) -> "Algorithms":
        """Register Algorithm(s)."""
        for name, algo in algorithms.items():
            if name in self.data and not overwrite:
                raise Exception(f"{name} is already a registered. Use overwrite=True.")

        return Algorithms({**self.data, **algorithms})

    @property
    def dependency(self):
        """FastAPI PostProcess dependency."""

        def post_process(
            algorithm: Literal[tuple(self.data.keys())] = Query(
                None, description="Algorithm name"
            ),
            algorithm_params: str = Query(None, description="Algorithm parameter"),
        ) -> Optional[BaseAlgorithm]:
            """Data Post-Processing options."""
            kwargs = json.loads(algorithm_params) if algorithm_params else {}
            if algorithm:
                try:
                    return self.get(algorithm)(**kwargs)
                except ValidationError as e:
                    raise HTTPException(status_code=400, detail=str(e))

            return None

        return post_process


algorithms = Algorithms(copy(default_algorithms))  # noqa
