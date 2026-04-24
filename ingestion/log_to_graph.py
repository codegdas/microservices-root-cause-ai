def transform_log(log):
    service = log["service"]
    level = log["level"]
    message = log["message"]
    timestamp = log["timestamp"]
    trace_id = log.get("traceId", "unknown")
    cause_type = log.get("causeType")
    database_name = log.get("databaseName")
    dependency_type = log.get("dependencyType")
    deployment_id = log.get("deploymentId")
    deployment_version = log.get("deploymentVersion")
    deployed_at = log.get("deployedAt")

    calls_map = {
        "gateway": "order",
        "order": "payment",
        "payment": "inventory"
    }

    next_service = calls_map.get(service)
    event_key = f"{service}|{trace_id}|{timestamp}|{level}|{message}"
    alert_key = f"{event_key}|alert"

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
    MERGE (e:Event {id: $event_id})
    ON CREATE SET
        e.timestamp = $timestamp,
        e.level = $level,
        e.message = $message,
        e.traceId = $trace_id,
        e.causeType = $cause_type
    SET
        e.timestamp = $timestamp,
        e.level = $level,
        e.message = $message,
        e.traceId = $trace_id,
        e.causeType = $cause_type

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
        MERGE (s)-[:CALLS]->(s2)
    )

    WITH s, e

    // =======================
    // 5. OPTIONAL DEPENDENCIES
    // =======================
    FOREACH (_ IN CASE WHEN $database_name IS NOT NULL THEN [1] ELSE [] END |
        MERGE (db:Database {name: $database_name})
        ON CREATE SET db.type = coalesce($dependency_type, "database")
        SET db.lastSeen = timestamp()
        MERGE (s)-[:DEPENDS_ON]->(db)
        MERGE (db)-[:GENERATED]->(e)
    )

    FOREACH (_ IN CASE WHEN $deployment_id IS NOT NULL THEN [1] ELSE [] END |
        MERGE (d:Deployment {id: $deployment_id})
        ON CREATE SET
            d.version = $deployment_version,
            d.deployedAt = $deployed_at
        SET
            d.lastSeen = timestamp(),
            d.version = coalesce($deployment_version, d.version),
            d.deployedAt = coalesce($deployed_at, d.deployedAt)
        MERGE (d)-[:DEPLOYED_TO]->(s)
        MERGE (d)-[:RELATED_TO]->(e)
    )

    WITH s, e

    // =======================
    // 6. ALERT (FROM EVENT)
    // =======================
    WITH s, e
    WHERE $level = "ERROR"

    MERGE (a:Alert {id: $alert_id})
    ON CREATE SET
        a.severity = "HIGH",
        a.message = $message,
        a.firedAt = $timestamp
    SET
        a.severity = "HIGH",
        a.message = $message,
        a.firedAt = $timestamp

    MERGE (e)-[:TRIGGERS]->(a)

    WITH s, e, a

    // =======================
    // 7. INCIDENT (FROM ALERT)
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
        i.causeType = coalesce($cause_type, i.causeType)

    MERGE (a)-[:ESCALATES_TO]->(i)

    FOREACH (_ IN CASE WHEN $database_name IS NOT NULL THEN [1] ELSE [] END |
        MERGE (db:Database {name: $database_name})
        MERGE (i)-[:RELATED_DATABASE]->(db)
    )

    FOREACH (_ IN CASE WHEN $deployment_id IS NOT NULL THEN [1] ELSE [] END |
        MERGE (d:Deployment {id: $deployment_id})
        MERGE (i)-[:RELATED_DEPLOYMENT]->(d)
    )

    RETURN s
    """

    params = {
        "service": service,
        "level": level,
        "message": message,
        "timestamp": timestamp,
        "trace_id": trace_id,
        "event_id": event_key,
        "alert_id": alert_key,
        "next_service": next_service,
        "cause_type": cause_type,
        "database_name": database_name,
        "dependency_type": dependency_type,
        "deployment_id": deployment_id,
        "deployment_version": deployment_version,
        "deployed_at": deployed_at
    }

    return query, params
