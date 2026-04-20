import uuid

def transform_log(log):

    return """
MERGE (s:Service {name: $service})
ON CREATE SET 
    s.uuid = randomUUID(),
    s.createdAt = timestamp(),
    s.createdBy = "system"
ON MATCH SET 
    s.updatedAt = timestamp()

CREATE (e:Event {
    uuid: randomUUID(),
    level: $level,
    message: $message,
    timestamp: $timestamp,
    createdAt: timestamp(),
    updatedAt: timestamp()
})

MERGE (s)-[:GENERATED]->(e)
""", log