import os
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

EDGE_NODES = {
    "edge_node_1": os.getenv("EDGE_NODE_1_URL", "http://127.0.0.1:8001")
}