# Neo4j Database Dump

The Review 2 rubric asks for a database dump. A valid Neo4j `.dump` must be generated from the actual Neo4j database.

## Option 1: Neo4j Admin CLI

Stop the database before performing a dump when required by your Neo4j installation.

A typical Neo4j 5 command is:

```bash
neo4j-admin database dump neo4j --to-path=./database-dump
```

If your Neo4j Desktop installation uses a different CLI path or command syntax, use the `neo4j-admin database dump --help` output for that installed version.

Submit the resulting `.dump` file separately from the source-code ZIP if it is too large.

## Option 2: Portable logical export

Run the queries in:

`cypher/export.cypher`

This produces a logical Cypher representation that can be recreated in another Neo4j database. It is useful for source-code submission, but it is not a replacement for a binary `.dump` if the rubric specifically asks for a dump.
