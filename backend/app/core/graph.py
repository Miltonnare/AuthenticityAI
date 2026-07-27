import logging

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    _has_neo4j = True
except ImportError:
    _has_neo4j = False
    GraphDatabase = None

class Neo4jConnector:
    def __init__(self):
        self.driver = None
        if _has_neo4j:
            self.uri = "bolt://localhost:7687"
            self.user = "neo4j"
            self.password = "password"
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j driver: {e}")
        else:
            logger.info("Neo4j driver not found. Running graph service in mock-mode.")

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query: str, parameters: dict = None):
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(query, parameters)
                    return [record.data() for record in result]
            except Exception as e:
                logger.warning(f"Neo4j transaction failed: {e}")
                return []
        else:
            logger.info(f"Mock Neo4j query executed: {query} with params {parameters}")
            if "Politician" in query and "depth" in query:
                return [
                    {
                        "nodes": [{"id": "pol-1", "label": "Politician", "properties": {"name": "Senator Doe"}}],
                        "edges": []
                     }
                ]
            return []

neo4j_connector = Neo4jConnector()
