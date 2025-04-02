"""
Call graph analysis for the Oregon Trail decompiler.
"""

from typing import Dict, List, Set, Tuple
import networkx as nx
import matplotlib.pyplot as plt
from .models import DOSFunction


class CallGraphAnalyzer:
    """Analyzes function call relationships."""

    def __init__(self, functions: List[DOSFunction]):
        """Initialize with a list of functions."""
        self.functions = functions
        self.call_graph = nx.DiGraph()
        self.function_map = {func.start_address: func for func in functions}
        self.entry_points = set()
        self.leaf_functions = set()
        self.highly_called = set()
        self.callers_map = {}  # Maps function to its callers

    def build_call_graph(self) -> nx.DiGraph:
        """Build a directed graph of function calls."""
        # Add all functions as nodes
        for func in self.functions:
            self.call_graph.add_node(func.start_address, name=func.name, function=func)
            
        # Add call edges
        for func in self.functions:
            for call_addr in func.calls:
                if call_addr in self.function_map:
                    self.call_graph.add_edge(func.start_address, call_addr)
                    
                    # Track callers for each function
                    if call_addr not in self.callers_map:
                        self.callers_map[call_addr] = set()
                    self.callers_map[call_addr].add(func.start_address)
        
        # Find entry points (functions with no callers)
        for func in self.functions:
            if func.start_address not in self.callers_map:
                self.entry_points.add(func.start_address)
                
        # Find leaf functions (functions that don't call others)
        for func in self.functions:
            if not func.calls:
                self.leaf_functions.add(func.start_address)
                
        # Find highly called functions (called by many others)
        for addr, callers in self.callers_map.items():
            if len(callers) > 5:  # Arbitrary threshold
                self.highly_called.add(addr)
                
        return self.call_graph
    
    def identify_function_groups(self) -> Dict[str, Set[int]]:
        """Identify groups of related functions."""
        # Use community detection to find related function groups
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(nx.Graph(self.call_graph))
            
            # Group functions by community
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = set()
                communities[community_id].add(node)
                
            # Name communities based on the most central function in each
            named_communities = {}
            for community_id, nodes in communities.items():
                # Find the most central node in this community
                subgraph = nx.subgraph(self.call_graph, nodes)
                try:
                    centrality = nx.betweenness_centrality(subgraph)
                    most_central = max(centrality.items(), key=lambda x: x[1])[0]
                    central_function = self.function_map[most_central]
                    
                    # Use function name or purpose for community name
                    community_name = central_function.purpose if hasattr(central_function, "purpose") and central_function.purpose else central_function.name
                    named_communities[community_name] = nodes
                except:
                    named_communities[f"Community_{community_id}"] = nodes
                    
            return named_communities
        except ImportError:
            # Fallback to a simpler approach if community detection isn't available
            return self._identify_function_groups_simple()
    
    def _identify_function_groups_simple(self) -> Dict[str, Set[int]]:
        """Simple function grouping based on call relationships."""
        groups = {}
        
        # Group by entry points - functions called by each entry point
        for entry in self.entry_points:
            if entry in self.function_map:
                entry_func = self.function_map[entry]
                group_name = entry_func.purpose if hasattr(entry_func, "purpose") and entry_func.purpose else entry_func.name
                groups[group_name] = set()
                
                # DFS to find all functions called from this entry point
                to_visit = [entry]
                visited = set()
                
                while to_visit:
                    current = to_visit.pop()
                    if current in visited:
                        continue
                        
                    visited.add(current)
                    groups[group_name].add(current)
                    
                    if current in self.function_map:
                        current_func = self.function_map[current]
                        for call in current_func.calls:
                            if call in self.function_map and call not in visited:
                                to_visit.append(call)
        
        return groups
    
    def generate_function_relationships(self) -> Dict[int, Dict]:
        """Generate detailed relationship information for each function."""
        relationships = {}
        
        for func in self.functions:
            addr = func.start_address
            relationships[addr] = {
                "callers": list(self.callers_map.get(addr, set())),
                "calls": func.calls,
                "is_entry_point": addr in self.entry_points,
                "is_leaf": addr in self.leaf_functions,
                "is_highly_called": addr in self.highly_called,
                "call_depth": self._calculate_call_depth(addr)
            }
            
        return relationships
    
    def _calculate_call_depth(self, func_addr: int) -> int:
        """Calculate the maximum depth of calls from this function."""
        visited = set()
        
        def dfs_depth(addr, depth=0):
            if addr in visited:
                return depth
                
            visited.add(addr)
            max_depth = depth
            
            if addr in self.function_map:
                func = self.function_map[addr]
                for call in func.calls:
                    if call in self.function_map and call not in visited:
                        call_depth = dfs_depth(call, depth + 1)
                        max_depth = max(max_depth, call_depth)
                        
            return max_depth
            
        return dfs_depth(func_addr)
    
    def visualize_call_graph(self, output_file: str = "call_graph.png"):
        """Generate a visualization of the call graph."""
        # Create a simplified graph for visualization
        if len(self.call_graph) > 100:
            # If there are too many nodes, only visualize important ones
            important_nodes = list(self.entry_points) + list(self.highly_called)
            subgraph = nx.subgraph(self.call_graph, important_nodes)
        else:
            subgraph = self.call_graph
            
        # Set up node labels and colors
        labels = {}
        node_colors = []
        
        for node in subgraph.nodes():
            func = self.function_map[node]
            labels[node] = func.name
            
            if node in self.entry_points:
                node_colors.append('green')
            elif node in self.highly_called:
                node_colors.append('red')
            elif node in self.leaf_functions:
                node_colors.append('blue')
            else:
                node_colors.append('gray')
        
        # Generate the visualization
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(subgraph)
        nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, alpha=0.8)
        nx.draw_networkx_edges(subgraph, pos, alpha=0.5, arrows=True)
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=8)
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        return output_file
    
    def enhance_function_purposes(self):
        """Enhance function purpose descriptions based on call relationships."""
        # Functions called by many others might be utility functions
        for addr in self.highly_called:
            if addr in self.function_map:
                func = self.function_map[addr]
                if not hasattr(func, "purpose") or not func.purpose:
                    callers_count = len(self.callers_map.get(addr, []))
                    func.purpose = f"Utility function called by {callers_count} other functions"
                    
        # Entry points might be major game functions
        for addr in self.entry_points:
            if addr in self.function_map:
                func = self.function_map[addr]
                if not hasattr(func, "purpose") or not func.purpose:
                    if func.calls:
                        func.purpose = "Entry point or major subsystem"
                        
        # Leaf functions might be simple operations
        for addr in self.leaf_functions:
            if addr in self.function_map:
                func = self.function_map[addr]
                if not hasattr(func, "purpose") or not func.purpose:
                    func.purpose = "Leaf function (performs simple operation)"