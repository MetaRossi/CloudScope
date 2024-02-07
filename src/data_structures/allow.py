import json
import logging
import re
from typing import Optional, Set, List

from pydantic import BaseModel, Field, PrivateAttr


class AllowSet(BaseModel):
    """A class for storing the allow set configuration settings."""
    full_set: Set[str] = Field(default_factory=set, frozen=True)
    allow_set: Set[str] = Field(default_factory=set, frozen=True)
    _computed_set: Set[str] = PrivateAttr(default_factory=set)

    def __init__(self, **data):
        super().__init__(**data)

        # Validate the characters in the sets and compute the computed set
        self._validate_characters()
        self._compute_computed_set()

    def __hash__(self):
        return hash(str(self._computed_set))

    def _validate_characters(self) -> None:
        """Validate the characters in the sets."""
        # If any value in any set does not match the regex, raise an error
        regex = r"^[*a-zA-Z0-9-_]*$"
        for value in self.full_set:
            if not re.match(regex, value):
                raise ValueError(f"Invalid character in full_set value: {value}")
        for value in self.allow_set:
            if not re.match(regex, value):
                raise ValueError(f"Invalid character in allow_set value: {value}")

    def _compute_computed_set(self) -> None:
        """Compute the computed set based on the allow_set and ignore_set."""

        # Handle absence of allow_set
        if not self.allow_set:
            self._computed_set = self.full_set

        # Handle presence of allow_set
        else:
            # Handle allow_set special value: "*"
            if "*" in self.allow_set and len(self.allow_set) == 1:
                self._computed_set = self.full_set
                return
            # Disallow allow_set special value "*" if there are other values
            elif "*" in self.allow_set and len(self.allow_set) > 1:
                raise ValueError("If '*' is in allow_set, it must be the only value: {self.allow_set}")
            else:
                # Build the computed set from the allow_set
                buffer: Set[str] = set()
                for value in self.allow_set:
                    # Handle allow_set special values like: "us*", "*8x*", "*h100", "*8x*smx*"
                    # Use regex to match the values against the full_set
                    if "*" in value:
                        regex = "|".join(f"^{value.replace('*', '.*')}$" for value in self.allow_set)
                        new_instances = set(filter(lambda x: re.match(regex, x), self.full_set))
                        buffer.update(new_instances)
                    elif value in self.full_set:
                        buffer.add(value)
                    else:
                        raise ValueError(f"Value in allow_set not in full_set: {value}; {self.full_set}")

                self._computed_set = buffer

    def is_allowed(self, name: str) -> bool:
        """Check if the name is in the computed set."""
        return name in self._computed_set

    def get_computed_set(self) -> set:
        """Return the computed set."""
        return self._computed_set

    def log_allow_set(self, label: Optional[str] = None) -> None:
        """Log the computed set."""
        if label:
            logging.info(f"Computed set for {label}: {self._computed_set}")
        else:
            logging.info(f"Computed set: {self._computed_set}")


class AllowPair(BaseModel):
    """A class for storing the allow pair configuration settings."""
    instance_names: AllowSet = Field(default_factory=AllowSet, frozen=True)
    regions: AllowSet = Field(default_factory=AllowSet, frozen=True)

    def is_allowed(self, instance_name: str, region: str) -> bool:
        """Check if the instance_name and region are in the computed sets."""
        return self.instance_names.is_allowed(instance_name) and self.regions.is_allowed(region)

    def log_allow_pair(self, label: Optional[str] = None) -> None:
        """Log the computed sets."""
        if label:
            logging.info(f"For {label}, "
                         f"computed instance names: {self.instance_names.get_computed_set()}; "
                         f"computed regions: {self.regions.get_computed_set()}")
        else:
            logging.info(f"Computed instance names: {self.instance_names.get_computed_set()}; "
                         f"computed regions: {self.regions.get_computed_set()}")

    def __hash__(self):
        return hash(self.instance_names)


class AllowInstances(BaseModel):
    """A class for storing the allow instances configuration settings."""
    allow_pairs: Set[AllowPair] = Field(default_factory=set, frozen=True)

    @staticmethod
    def from_config_json_array(config_json_array: List[str],
                               instances_full_set: Set[str],
                               regions_full_set: Set[str]
                               ) -> "AllowInstances":
        """Create an AllowInstances object from a config json array."""
        allow_pairs = set()
        for json_str in config_json_array:
            # Parse the json string like: '{"instance_names": ["gpu_1x_h100"], "regions": ["*"]}'
            data: dict = json.loads(json_str)
            instance_names = AllowSet(full_set=instances_full_set,
                                      allow_set=data['instance_names'])
            regions = AllowSet(full_set=regions_full_set,
                               allow_set=data['regions'])

            # Ensure that the AllowPair is not a duplicate
            if AllowPair(instance_names=instance_names, regions=regions) in allow_pairs:
                raise ValueError(f"Duplicate AllowPair: {json_str}")

            # Add the AllowPair to the set
            allow_pairs.add(AllowPair(instance_names=instance_names, regions=regions))

        return AllowInstances(allow_pairs=allow_pairs)

    def is_allowed(self, instance_name: str, region: str) -> bool:
        """Check if the instance_name and region are in the computed sets."""
        return any(allow_pair.is_allowed(instance_name, region) for allow_pair in self.allow_pairs)

    def log_allow_instances(self, label: Optional[str] = None) -> None:
        """Log the computed sets with multiple lines."""
        if label:
            logging.info(f"For {label}, computed sets:")
        else:
            logging.info(f"Computed sets:")
        for allow_pair in self.allow_pairs:
            allow_pair.log_allow_pair(label)
