// CREATE
CREATE (c:Customer {customer_id:'C-DEMO'})
RETURN c;

// READ
MATCH (c:Customer)
RETURN c
LIMIT 10;

// UPDATE
MATCH (c:Customer {customer_id:'C-DEMO'})
SET c.review_status='manual_review'
RETURN c;

// DELETE
MATCH (c:Customer {customer_id:'C-DEMO'})
DETACH DELETE c;
