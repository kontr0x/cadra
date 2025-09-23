from dataclasses import dataclass
from neo4j import Record
from typing import Any, List

from models.active_directory import UAC_FLAGS, GENERIC_PROPERTIES, PRINCIPAL_PROPERTIES
from models.bloodhound import NODE_ATTRIBUTES, EdgeType
from modules.logging_base import Logging
from modules.neo4j_utils import get_node_type_from_labels, get_uac_flags_from_properties

logger = Logging().getLogger()


@dataclass
class UserPaths:
    def __init__(self, records: List[Record]) -> None:
        self.user: User = None
        self.paths: List[Path] = []
        self._consume_paths(records)

    def _consume_paths(self, records: List[Record]) -> None:
        for record in records:
            path = Path(record["p"])
            if isinstance(path.start_node, User):
                if self.user is None:
                    self.user = path.start_node
                elif self.user.id != path.start_node.id:
                    logger.error("Inconsistent user in paths")
                    return
            else:
                logger.error("Path does not start with a User node")
                return
            self.paths.append(path)
            if path.relationship.type == EdgeType.MEMBER_OF.value:
                self.user.memberof.append(path.end_node.samaccountname)
            if path.relationship.type not in self.user.edges:
                self.user.edges.append(path.relationship.type)


@dataclass
class Path:
    def __init__(self, record: Record) -> None:
        self.relationship = Edge(record.relationships[0])
        self.start_node = Node(record.start_node)
        if self.start_node.type == "User":
            self.start_node = User(record.start_node)
        self.end_node = Node(record.end_node)
        if self.end_node.type == "User":
            self.end_node = User(record.end_node)

        if not self.validate():
            logger.error("Path validation failed")

    def validate(self) -> bool:
        if self.start_node.id != self.relationship.start_node_id:
            logger.error(
                f"Start node ID '{self.start_node.id}' does not match relationship start node ID '{self.relationship.start_node_id}'")
            return False
        if self.end_node.id != self.relationship.end_node_id:
            logger.error(
                f"End node ID '{self.end_node.id}' does not match relationship end node ID '{self.relationship.end_node_id}'")
            return False
        return True

    def __str__(self):
        start_node_name = self.start_node.properties.get('name')
        end_node_name = self.end_node.properties.get('name')
        r_type = self.relationship.type
        return f"({start_node_name}: {self.start_node.type})" + \
            f" - [{r_type}] -> ({end_node_name}: {self.end_node.type})"


@dataclass
class Node:
    def __init__(self, record: Record) -> None:
        self.id = record.element_id
        self.type = get_node_type_from_labels(record.labels)
        self.properties = record._properties
        self.name = self.properties.get('name')
        self.edges: List[str] = []

        if not self.validate():
            logger.error("Node validation failed")
            return

    def validate(self) -> bool:
        if self.id is None or self.type is None or self.properties is None:
            logger.error("Node validation failed: Missing id, type, or properties")
            return False
        return True

    def __getattr__(self, item: str) -> Any:
        if item.lower() in self.properties:
            return self.properties.get(item.lower())
        elif item.lower() in GENERIC_PROPERTIES:
            return GENERIC_PROPERTIES[item.lower()]
        elif item.lower() in NODE_ATTRIBUTES:
            return NODE_ATTRIBUTES[item.lower()]
        else:
            raise AttributeError(f"Unknown property: {item}")

    def __str__(self):
        return f"Node(id={self.id}, type={self.type})"


@dataclass
class Edge:
    def __init__(self, relationship) -> None:
        self.id = relationship.id
        self.type = relationship.type
        self.start_node_id = relationship.start_node.element_id
        self.start_name = relationship.start_node._properties.get('name')
        self.end_node_id = relationship.end_node.element_id
        self.end_name = relationship.end_node._properties.get('name')
        self.relationship_description = f"{self.start_name} -[{self.type}]-> {self.end_name}"

    def __str__(self):
        return f"Edge(type={self.type}, from={self.start_name}, to={self.end_name})"


@dataclass
class User(Node):
    def __init__(self, record: Record) -> None:
        super().__init__(record)
        self.uac_flags: List[str] = get_uac_flags_from_properties(self.properties)
        self.memberof: List[str] = []
        self.edges: List[str] = []

    def __getattr__(self, item: str) -> Any:
        # Check if the item is a UAC flag
        if item.upper() in UAC_FLAGS:
            # Return True if the flag is present, else False
            return item.upper() in self.uac_flags
        elif item.lower() in self.properties:
            return self.properties.get(item.lower())
        # TODO: Support custom properties
        # elif item.lower() in custom_user_properties:
        #     return custom_user_properties[item.lower()]
        elif item.lower() in PRINCIPAL_PROPERTIES:
            return PRINCIPAL_PROPERTIES[item.lower()]
        else:
            return getattr(super(), item)

    def __str__(self):
        return f"""
            User(id={self.id}
                name={self.name}
                uac_flags={self.uac_flags}
                memberof={self.memberof}
                edges={self.edges}  
            )
        """
