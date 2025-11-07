"""
Data Lineage Tracker

Tracks data provenance, transformations, dependencies, and impact analysis
throughout the data pipeline lifecycle.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Lineage node types"""
    SOURCE = "source"  # Original data source
    DATASET = "dataset"  # Data collection/table
    TRANSFORMATION = "transformation"  # Data transformation
    MODEL = "model"  # ML model
    METRIC = "metric"  # Derived metric
    REPORT = "report"  # Report/dashboard
    API = "api"  # API endpoint


class TransformationType(Enum):
    """Types of data transformations"""
    FILTER = "filter"
    AGGREGATE = "aggregate"
    JOIN = "join"
    UNION = "union"
    PIVOT = "pivot"
    NORMALIZE = "normalize"
    DENORMALIZE = "denormalize"
    CLEANSE = "cleanse"
    ENRICH = "enrich"
    COMPUTE = "compute"


@dataclass
class LineageNode:
    """Node in the lineage graph"""
    node_id: str
    node_type: NodeType
    name: str
    description: str
    created_at: datetime
    created_by: str
    metadata: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class LineageEdge:
    """Edge connecting lineage nodes"""
    edge_id: str
    source_node_id: str
    target_node_id: str
    transformation_type: Optional[TransformationType]
    transformation_logic: str
    created_at: datetime
    metadata: Dict = field(default_factory=dict)


@dataclass
class DataFlow:
    """Complete data flow path"""
    flow_id: str
    start_node_id: str
    end_node_id: str
    path: List[str]  # List of node IDs
    transformations: List[LineageEdge]
    distance: int  # Number of hops


@dataclass
class ImpactAnalysis:
    """Impact analysis result"""
    source_node_id: str
    affected_nodes: List[str]
    affected_types: Dict[str, int]
    depth: int
    critical_paths: List[DataFlow]


class DataLineageTracker:
    """
    Data Lineage Tracking System

    Features:
    - Automatic lineage capture
    - Data provenance tracking
    - Transformation logging
    - Dependency graph management
    - Impact analysis
    - Upstream/downstream tracing
    - Lineage visualization data
    - Data quality propagation
    """

    def __init__(self):
        # Lineage graph
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: Dict[str, LineageEdge] = {}

        # Adjacency lists for efficient graph traversal
        self.upstream: Dict[str, Set[str]] = {}  # node -> upstream nodes
        self.downstream: Dict[str, Set[str]] = {}  # node -> downstream nodes

        # Index by type
        self.nodes_by_type: Dict[NodeType, Set[str]] = {
            node_type: set() for node_type in NodeType
        }

        logger.info("Initialized DataLineageTracker")

    def register_node(
        self,
        node_id: str,
        node_type: NodeType,
        name: str,
        description: str,
        created_by: str = "system",
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> LineageNode:
        """
        Register a lineage node

        Args:
            node_id: Unique node identifier
            node_type: Type of node
            name: Node name
            description: Node description
            created_by: Creator identifier
            metadata: Additional metadata
            tags: Tags for categorization

        Returns:
            LineageNode
        """
        if node_id in self.nodes:
            raise ValueError(f"Node already exists: {node_id}")

        node = LineageNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            description=description,
            created_at=datetime.now(),
            created_by=created_by,
            metadata=metadata or {},
            tags=tags or [],
        )

        self.nodes[node_id] = node
        self.nodes_by_type[node_type].add(node_id)
        self.upstream[node_id] = set()
        self.downstream[node_id] = set()

        logger.info(f"Registered lineage node: {node_id} ({node_type.value})")
        return node

    def register_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        transformation_type: Optional[TransformationType] = None,
        transformation_logic: str = "",
        metadata: Optional[Dict] = None,
    ) -> LineageEdge:
        """
        Register a lineage edge (dependency)

        Args:
            source_node_id: Source node ID
            target_node_id: Target node ID
            transformation_type: Type of transformation
            transformation_logic: Description/code of transformation
            metadata: Additional metadata

        Returns:
            LineageEdge
        """
        if source_node_id not in self.nodes:
            raise ValueError(f"Source node not found: {source_node_id}")

        if target_node_id not in self.nodes:
            raise ValueError(f"Target node not found: {target_node_id}")

        edge_id = f"{source_node_id}->{target_node_id}"

        if edge_id in self.edges:
            logger.warning(f"Edge already exists: {edge_id}")
            return self.edges[edge_id]

        edge = LineageEdge(
            edge_id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            transformation_type=transformation_type,
            transformation_logic=transformation_logic,
            created_at=datetime.now(),
            metadata=metadata or {},
        )

        self.edges[edge_id] = edge
        self.upstream[target_node_id].add(source_node_id)
        self.downstream[source_node_id].add(target_node_id)

        logger.info(f"Registered lineage edge: {edge_id}")
        return edge

    def get_upstream_nodes(
        self,
        node_id: str,
        max_depth: Optional[int] = None,
    ) -> List[str]:
        """Get all upstream (parent) nodes"""
        if node_id not in self.nodes:
            return []

        visited = set()
        result = []

        def dfs(current_id: str, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            visited.add(current_id)

            for upstream_id in self.upstream.get(current_id, []):
                if upstream_id not in visited:
                    result.append(upstream_id)
                    dfs(upstream_id, depth + 1)

        dfs(node_id, 0)
        return result

    def get_downstream_nodes(
        self,
        node_id: str,
        max_depth: Optional[int] = None,
    ) -> List[str]:
        """Get all downstream (child) nodes"""
        if node_id not in self.nodes:
            return []

        visited = set()
        result = []

        def dfs(current_id: str, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            visited.add(current_id)

            for downstream_id in self.downstream.get(current_id, []):
                if downstream_id not in visited:
                    result.append(downstream_id)
                    dfs(downstream_id, depth + 1)

        dfs(node_id, 0)
        return result

    def trace_lineage(
        self,
        node_id: str,
        direction: str = "both",  # upstream, downstream, both
    ) -> Dict:
        """Trace complete lineage for a node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node not found: {node_id}")

        node = self.nodes[node_id]
        result = {
            'node': node,
            'upstream': [],
            'downstream': [],
        }

        if direction in ["upstream", "both"]:
            upstream_ids = self.get_upstream_nodes(node_id)
            result['upstream'] = [self.nodes[nid] for nid in upstream_ids]

        if direction in ["downstream", "both"]:
            downstream_ids = self.get_downstream_nodes(node_id)
            result['downstream'] = [self.nodes[nid] for nid in downstream_ids]

        return result

    def find_data_flow(
        self,
        source_node_id: str,
        target_node_id: str,
    ) -> Optional[DataFlow]:
        """Find data flow path between two nodes"""
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            return None

        # BFS to find shortest path
        queue = [(source_node_id, [source_node_id])]
        visited = {source_node_id}

        while queue:
            current_id, path = queue.pop(0)

            if current_id == target_node_id:
                # Found path - collect transformations
                transformations = []
                for i in range(len(path) - 1):
                    edge_id = f"{path[i]}->{path[i+1]}"
                    if edge_id in self.edges:
                        transformations.append(self.edges[edge_id])

                return DataFlow(
                    flow_id=f"flow-{source_node_id}-to-{target_node_id}",
                    start_node_id=source_node_id,
                    end_node_id=target_node_id,
                    path=path,
                    transformations=transformations,
                    distance=len(path) - 1,
                )

            # Explore downstream nodes
            for next_id in self.downstream.get(current_id, []):
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))

        return None  # No path found

    def analyze_impact(
        self,
        node_id: str,
        max_depth: int = 10,
    ) -> ImpactAnalysis:
        """Analyze impact of changes to a node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node not found: {node_id}")

        # Get all downstream nodes
        affected = self.get_downstream_nodes(node_id, max_depth)

        # Count by type
        affected_types = {}
        for affected_id in affected:
            node_type = self.nodes[affected_id].node_type.value
            affected_types[node_type] = affected_types.get(node_type, 0) + 1

        # Find critical paths (to reports, APIs, models)
        critical_types = {NodeType.REPORT, NodeType.API, NodeType.MODEL}
        critical_paths = []

        for affected_id in affected:
            if self.nodes[affected_id].node_type in critical_types:
                flow = self.find_data_flow(node_id, affected_id)
                if flow:
                    critical_paths.append(flow)

        return ImpactAnalysis(
            source_node_id=node_id,
            affected_nodes=affected,
            affected_types=affected_types,
            depth=max_depth,
            critical_paths=critical_paths,
        )

    def get_root_sources(self, node_id: str) -> List[LineageNode]:
        """Get all root data sources for a node"""
        upstream = self.get_upstream_nodes(node_id)

        # Find nodes with no upstream dependencies
        root_ids = [
            nid for nid in upstream
            if not self.upstream.get(nid, set())
        ]

        # Add the starting node if it's a root
        if not self.upstream.get(node_id, set()):
            root_ids.append(node_id)

        return [self.nodes[nid] for nid in set(root_ids)]

    def get_transformation_chain(
        self,
        node_id: str,
    ) -> List[Dict]:
        """Get complete transformation chain leading to a node"""
        upstream = self.get_upstream_nodes(node_id)

        transformations = []
        for upstream_id in upstream:
            edge_id = f"{upstream_id}->{node_id}"
            if edge_id in self.edges:
                edge = self.edges[edge_id]
                transformations.append({
                    'from': self.nodes[upstream_id].name,
                    'to': self.nodes[node_id].name,
                    'type': edge.transformation_type.value if edge.transformation_type else None,
                    'logic': edge.transformation_logic,
                })

        return transformations

    def export_lineage_graph(
        self,
        format: str = "graphviz",
    ) -> str:
        """Export lineage graph for visualization"""
        if format == "graphviz":
            return self._export_graphviz()
        elif format == "json":
            return self._export_json()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_graphviz(self) -> str:
        """Export as Graphviz DOT format"""
        lines = ["digraph lineage {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")

        # Add nodes
        for node_id, node in self.nodes.items():
            label = f"{node.name}\\n({node.node_type.value})"
            color = self._get_node_color(node.node_type)
            lines.append(f'  "{node_id}" [label="{label}", fillcolor="{color}", style=filled];')

        # Add edges
        for edge in self.edges.values():
            label = edge.transformation_type.value if edge.transformation_type else ""
            lines.append(f'  "{edge.source_node_id}" -> "{edge.target_node_id}" [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)

    def _export_json(self) -> str:
        """Export as JSON"""
        data = {
            'nodes': [
                {
                    'id': node.node_id,
                    'type': node.node_type.value,
                    'name': node.name,
                    'description': node.description,
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {
                    'source': edge.source_node_id,
                    'target': edge.target_node_id,
                    'type': edge.transformation_type.value if edge.transformation_type else None,
                }
                for edge in self.edges.values()
            ],
        }
        return json.dumps(data, indent=2)

    def _get_node_color(self, node_type: NodeType) -> str:
        """Get visualization color for node type"""
        colors = {
            NodeType.SOURCE: "lightblue",
            NodeType.DATASET: "lightgreen",
            NodeType.TRANSFORMATION: "lightyellow",
            NodeType.MODEL: "lightpink",
            NodeType.METRIC: "lightcoral",
            NodeType.REPORT: "lightsalmon",
            NodeType.API: "lightcyan",
        }
        return colors.get(node_type, "white")

    def get_statistics(self) -> Dict:
        """Get lineage statistics"""
        # Count nodes by type
        nodes_by_type = {
            node_type.value: len(nodes)
            for node_type, nodes in self.nodes_by_type.items()
        }

        # Find orphaned nodes (no upstream or downstream)
        orphaned = sum(
            1 for node_id in self.nodes
            if not self.upstream[node_id] and not self.downstream[node_id]
        )

        # Calculate graph metrics
        avg_upstream = sum(len(deps) for deps in self.upstream.values()) / len(self.nodes) if self.nodes else 0
        avg_downstream = sum(len(deps) for deps in self.downstream.values()) / len(self.nodes) if self.nodes else 0

        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'nodes_by_type': nodes_by_type,
            'orphaned_nodes': orphaned,
            'avg_upstream_dependencies': avg_upstream,
            'avg_downstream_dependencies': avg_downstream,
        }
