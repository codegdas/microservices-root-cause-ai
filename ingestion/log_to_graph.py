def transform_log(log):
    service = log["service"]
    level = log["level"]
    message = log["message"]
    timestamp = log["timestamp"]

    # 🔥 Define service dependency chain
    dependency_map = {
        "gateway": "order",
        "order": "payment",
        "payment": "inventory"
    }

    query = """
    MERGE (s:Service {name: $service})
    SET s.updatedAt = timestamp()

    MERGE (e:Event {
        message: $message,
        timestamp: $timestamp
    })
    SET e.level = $level

    MERGE (s)-[:GENERATED]->(e)
    """

    params = {
        "service": service,
        "level": level,
        "message": message,
        "timestamp": timestamp
    }

    # 🔥 Add CALLS relationship
    if service in dependency_map:
        downstream = dependency_map[service]

        query += """
        MERGE (d:Service {name: $downstream})
        MERGE (s)-[:CALLS]->(d)
        """

        params["downstream"] = downstream

    # 🔥 Update metrics (VERY IMPORTANT)
    if level == "ERROR":
        query += """
        SET s.errorRate = coalesce(s.errorRate, 0) + 0.2
        SET s.status = "UNHEALTHY"
        """
    else:
        query += """
        SET s.errorRate = coalesce(s.errorRate, 0) * 0.9
        SET s.status = "HEALTHY"
        """

    # simulate latency
    query += """
    SET s.latencyP99 = coalesce(s.latencyP99, 100) + CASE WHEN $level = "ERROR" THEN 50 ELSE -5 END
    """

    return query, params