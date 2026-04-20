from neo4j import GraphDatabase


def transform_log(log):
    service = log["service"]
    level = log["level"]
    message = log["message"]
    timestamp = log["timestamp"]

    calls_map = {
        "gateway": "order",
        "order": "payment",
        "payment": "inventory"
    }

    next_service = calls_map.get(service)

    query = """
    // =======================
    // 1. SERVICE
    // =======================
    MERGE (s:Service {name: $service})
    ON CREATE SET 
        s.errorCount = 0,
        s.totalCount = 0,
        s.errorRate = 0.0,
        s.latencyP99 = 100,
        s.status = "HEALTHY"

    SET s.lastSeen = timestamp()

    // =======================
    // 2. EVENT
    // =======================
    CREATE (e:Event {
        id: randomUUID(),
        timestamp: $timestamp,
        level: $level,
        message: $message
    })

    MERGE (s)-[:GENERATED]->(e)

    // =======================
    // 3. METRICS
    // =======================
    SET s.totalCount = s.totalCount + 1

    WITH s

    SET s.errorCount =
        CASE 
            WHEN $level = "ERROR" THEN s.errorCount + 1
            ELSE s.errorCount
        END

    WITH s

    SET s.errorRate =
        CASE
            WHEN s.totalCount = 0 THEN 0
            ELSE toFloat(s.errorCount) / s.totalCount
        END

    SET s.latencyP99 =
        CASE
            WHEN $level = "ERROR" THEN s.latencyP99 + 100
            ELSE s.latencyP99
        END

    SET s.status =
        CASE
            WHEN s.errorRate > 0.2 THEN "UNHEALTHY"
            ELSE "HEALTHY"
        END

    // =======================
    // 4. CALLS RELATIONSHIP
    // =======================
    WITH s
    WHERE $next_service IS NOT NULL

    MERGE (s2:Service {name: $next_service})
    MERGE (s)-[:CALLS]->(s2)

    // =======================
    // 5. ALERT
    // =======================
    WITH s
    WHERE s.errorRate > 0.2

    MERGE (a:Alert {service: s.name, active: true})
    ON CREATE SET
        a.id = randomUUID(),
        a.severity = "HIGH",
        a.firedAt = timestamp(),
        a.message = "High error rate"

    MERGE (s)-[:EMITS]->(a)

    // =======================
    // 6. INCIDENT
    // =======================
    WITH s
    WHERE s.errorRate > 0.3

    MERGE (i:Incident {service: s.name, status: "OPEN"})
    ON CREATE SET
        i.id = randomUUID(),
        i.createdAt = timestamp(),
        i.severity = "CRITICAL",
        i.rootCause = s.name

    MERGE (i)-[:ROOT_CAUSE]->(s)

    WITH s, i
    MATCH (s)-[:CALLS*1..3]->(downstream:Service)
    MERGE (i)-[:IMPACTS]->(downstream)

    RETURN s
    """

    params = {
        "service": service,
        "level": level,
        "message": message,
        "timestamp": timestamp,
        "next_service": next_service
    }

    return query, params