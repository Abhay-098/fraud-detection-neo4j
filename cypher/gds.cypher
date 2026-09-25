// Optional Neo4j Graph Data Science queries.
// Run only if the Neo4j Graph Data Science library is installed.

// Project an account-to-account transaction graph
CALL gds.graph.project(
  'fraud-account-network',
  'Account',
  {SENT_TO: {orientation: 'NATURAL'}}
)
YIELD graphName, nodeCount, relationshipCount;

// PageRank
CALL gds.pageRank.stream('fraud-account-network')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).account_id AS account, score
ORDER BY score DESC
LIMIT 20;

// Louvain communities
CALL gds.louvain.stream('fraud-account-network')
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).account_id)[0..20] AS sample_accounts,
       count(*) AS members
ORDER BY members DESC;

// Drop projection when finished
CALL gds.graph.drop('fraud-account-network') YIELD graphName;
