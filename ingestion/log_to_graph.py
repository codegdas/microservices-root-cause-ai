def transform_log(log):
    service = log["service"]
    level = log["level"]
    message = log["message"]
    timestamp = log["timestamp"]
    trace_id = log.get("traceId", "unknown")
    service_label = service.capitalize()

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

    FOREACH (_ IN CASE WHEN $service_label = "Gateway" THEN [1] ELSE [] END |
        SET s:Gateway
    )
    FOREACH (_ IN CASE WHEN $service_label = "Order" THEN [1] ELSE [] END |
        SET s:Order
    )
    FOREACH (_ IN CASE WHEN $service_label = "Payment" THEN [1] ELSE [] END |
        SET s:Payment
    )
    FOREACH (_ IN CASE WHEN $service_label = "Inventory" THEN [1] ELSE [] END |
        SET s:Inventory
    )

    // =======================
    // 2. EVENT
    // =======================
    CREATE (e:Event {
        id: randomUUID(),
        timestamp: $timestamp,
        level: $level,
        message: $message,
        traceId: $trace_id
    })

    MERGE (s)-[:GENERATED]->(e)

    // =======================
    // 3. METRICS
    // =======================
    SET s.totalCount = s.totalCount + 1

    WITH s, e

    SET s.errorCount =
        CASE 
            WHEN $level = "ERROR" THEN s.errorCount + 1
            ELSE s.errorCount
        END

    WITH s, e

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
    // 4. CALLS
    // =======================
    WITH s, e
    FOREACH (_ IN CASE WHEN $next_service IS NOT NULL THEN [1] ELSE [] END |
        MERGE (s2:Service {name: $next_service})
        FOREACH (_ IN CASE WHEN $next_service = "gateway" THEN [1] ELSE [] END |
            SET s2:Gateway
        )
        FOREACH (_ IN CASE WHEN $next_service = "order" THEN [1] ELSE [] END |
            SET s2:Order
        )
        FOREACH (_ IN CASE WHEN $next_service = "payment" THEN [1] ELSE [] END |
            SET s2:Payment
        )
        FOREACH (_ IN CASE WHEN $next_service = "inventory" THEN [1] ELSE [] END |
            SET s2:Inventory
        )
        MERGE (s)-[:CALLS]->(s2)
    )

    WITH s, e

    // =======================
    // 5. ALERT (FROM EVENT)
    // =======================
    WITH s, e
    WHERE $level = "ERROR"

    CREATE (a:Alert {
        id: randomUUID(),
        severity: "HIGH",
        message: $message,
        firedAt: $timestamp
    })

    MERGE (e)-[:TRIGGERS]->(a)

    WITH s, e, a

    // =======================
    // 6. INCIDENT (FROM ALERT)
    // =======================
    // Create an incident for each failing trace so the demo flow is reliable.
    WHERE $trace_id <> "unknown"

    MERGE (i:Incident {traceId: $trace_id})
    ON CREATE SET
        i.id = randomUUID(),
        i.createdAt = timestamp()
    SET
        i.updatedAt = timestamp(),
        i.severity = "CRITICAL",
        i.status = "OPEN",
        i.rootCause = s.name

    MERGE (i)-[:ROOT_CAUSE]->(s)
    MERGE (a)-[:ESCALATES_TO]->(i)

    WITH i, s

    MATCH (s)-[:CALLS*1..3]->(downstream:Service)
    MERGE (i)-[:IMPACTS]->(downstream)

    RETURN s
    """

    params = {
        "service": service,
        "level": level,
        "message": message,
        "timestamp": timestamp,
        "trace_id": trace_id,
        "service_label": service_label,
        "next_service": next_service
    }

    return query, params
