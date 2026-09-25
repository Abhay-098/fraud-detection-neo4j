// Logical export helpers. Run in Neo4j Browser and save results as CSV.
// Nodes:
MATCH (n) RETURN labels(n) AS labels, properties(n) AS properties;

// Relationships:
MATCH (a)-[r]->(b)
RETURN labels(a) AS from_labels, properties(a) AS from_properties,
       type(r) AS relationship, properties(r) AS relationship_properties,
       labels(b) AS to_labels, properties(b) AS to_properties;
