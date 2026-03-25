from .database import get_connection

ENTITY_CONFIG = {
    "SalesOrder": {
        "table": "sales_order_headers",
        "id_col": "salesOrder",
        "label_col": "salesOrder",
        "color": "#4A90D9",
    },
    "Delivery": {
        "table": "outbound_delivery_headers",
        "id_col": "deliveryDocument",
        "label_col": "deliveryDocument",
        "color": "#2ECC71",
    },
    "BillingDocument": {
        "table": "billing_document_headers",
        "id_col": "billingDocument",
        "label_col": "billingDocument",
        "color": "#E74C3C",
    },
    "JournalEntry": {
        "table": "journal_entry_items",
        "id_col": "accountingDocument",
        "label_col": "accountingDocument",
        "color": "#F39C12",
    },
    "Payment": {
        "table": "payments",
        "id_col": "accountingDocument",
        "label_col": "accountingDocument",
        "color": "#9B59B6",
    },
    "Customer": {
        "table": "business_partners",
        "id_col": "businessPartner",
        "label_col": "businessPartnerName",
        "color": "#00BCD4",
    },
    "Product": {
        "table": "products",
        "id_col": "product",
        "label_col": "product",
        "color": "#FF6F61",
    },
    "Plant": {
        "table": "plants",
        "id_col": "plant",
        "label_col": "plantName",
        "color": "#8BC34A",
    },
}

EDGE_QUERIES = [
    {
        "name": "SalesOrder_has_Item_linked_to_Delivery",
        "sql": """
            SELECT DISTINCT
                'SalesOrder' as source_type, soi.salesOrder as source_id,
                'Delivery' as target_type, odi.deliveryDocument as target_id,
                'HAS_DELIVERY' as relation
            FROM sales_order_items soi
            JOIN outbound_delivery_items odi ON odi.referenceSdDocument = soi.salesOrder
        """,
    },
    {
        "name": "Delivery_billed_in_BillingDocument",
        "sql": """
            SELECT DISTINCT
                'Delivery' as source_type, bdi.referenceSdDocument as source_id,
                'BillingDocument' as target_type, bdi.billingDocument as target_id,
                'BILLED_AS' as relation
            FROM billing_document_items bdi
            JOIN outbound_delivery_headers odh ON odh.deliveryDocument = bdi.referenceSdDocument
        """,
    },
    {
        "name": "BillingDocument_has_JournalEntry",
        "sql": """
            SELECT DISTINCT
                'BillingDocument' as source_type, jei.referenceDocument as source_id,
                'JournalEntry' as target_type, jei.accountingDocument as target_id,
                'GENERATES_ENTRY' as relation
            FROM journal_entry_items jei
            JOIN billing_document_headers bdh ON bdh.billingDocument = jei.referenceDocument
        """,
    },
    {
        "name": "JournalEntry_cleared_by_Payment",
        "sql": """
            SELECT DISTINCT
                'JournalEntry' as source_type, jei.accountingDocument as source_id,
                'Payment' as target_type, p.accountingDocument as target_id,
                'CLEARED_BY' as relation
            FROM journal_entry_items jei
            JOIN payments p ON p.clearingAccountingDocument = jei.accountingDocument
            WHERE jei.clearingAccountingDocument IS NOT NULL AND jei.clearingAccountingDocument != ''
        """,
    },
    {
        "name": "SalesOrder_placed_by_Customer",
        "sql": """
            SELECT DISTINCT
                'SalesOrder' as source_type, soh.salesOrder as source_id,
                'Customer' as target_type, soh.soldToParty as target_id,
                'PLACED_BY' as relation
            FROM sales_order_headers soh
            WHERE soh.soldToParty IS NOT NULL AND soh.soldToParty != ''
        """,
    },
    {
        "name": "SalesOrder_contains_Product",
        "sql": """
            SELECT DISTINCT
                'SalesOrder' as source_type, soi.salesOrder as source_id,
                'Product' as target_type, soi.material as target_id,
                'CONTAINS_PRODUCT' as relation
            FROM sales_order_items soi
            WHERE soi.material IS NOT NULL AND soi.material != ''
        """,
    },
    {
        "name": "Delivery_from_Plant",
        "sql": """
            SELECT DISTINCT
                'Delivery' as source_type, odi.deliveryDocument as source_id,
                'Plant' as target_type, odi.plant as target_id,
                'FROM_PLANT' as relation
            FROM outbound_delivery_items odi
            WHERE odi.plant IS NOT NULL AND odi.plant != ''
        """,
    },
    {
        "name": "BillingDocument_for_Customer",
        "sql": """
            SELECT DISTINCT
                'BillingDocument' as source_type, bdh.billingDocument as source_id,
                'Customer' as target_type, bdh.soldToParty as target_id,
                'BILLED_TO' as relation
            FROM billing_document_headers bdh
            WHERE bdh.soldToParty IS NOT NULL AND bdh.soldToParty != ''
        """,
    },
]


def build_graph_data(limit_nodes=500):
    conn = get_connection()
    cur = conn.cursor()

    nodes = {}
    edges = []

    for entity_type, cfg in ENTITY_CONFIG.items():
        cur.execute(f"SELECT DISTINCT {cfg['id_col']}, {cfg['label_col']} FROM {cfg['table']} LIMIT ?", (limit_nodes,))
        for row in cur.fetchall():
            nid = f"{entity_type}:{row[0]}"
            nodes[nid] = {
                "id": nid,
                "entity": entity_type,
                "entityId": str(row[0]),
                "label": str(row[1]) if row[1] else str(row[0]),
                "color": cfg["color"],
            }

    valid_ids = set(nodes.keys())

    for eq in EDGE_QUERIES:
        try:
            cur.execute(eq["sql"])
            for row in cur.fetchall():
                src = f"{row[0]}:{row[1]}"
                tgt = f"{row[2]}:{row[3]}"
                if src in valid_ids and tgt in valid_ids:
                    edges.append({
                        "source": src,
                        "target": tgt,
                        "relation": row[4],
                    })
        except Exception as e:
            print(f"Edge query {eq['name']} failed: {e}")

    conn.close()
    return {"nodes": list(nodes.values()), "edges": edges}


DIRECTED_EDGE_LOOKUPS = [
    ("SalesOrder", "salesOrder", "outbound_delivery_items", "referenceSdDocument",
     "deliveryDocument", "Delivery", "HAS_DELIVERY"),
    ("Delivery", "deliveryDocument", "billing_document_items", "referenceSdDocument",
     "billingDocument", "BillingDocument", "BILLED_AS"),
    ("BillingDocument", "billingDocument", "journal_entry_items", "referenceDocument",
     "accountingDocument", "JournalEntry", "GENERATES_ENTRY"),
    ("JournalEntry", "accountingDocument", "payments", "clearingAccountingDocument",
     "accountingDocument", "Payment", "CLEARED_BY"),
    ("SalesOrder", "soldToParty", "business_partners", "businessPartner",
     "businessPartner", "Customer", "PLACED_BY"),
    ("BillingDocument", "soldToParty", "business_partners", "businessPartner",
     "businessPartner", "Customer", "BILLED_TO"),
]


def get_node_details(entity_type: str, entity_id: str):
    cfg = ENTITY_CONFIG.get(entity_type)
    if not cfg:
        return None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {cfg['table']} WHERE {cfg['id_col']} = ?", (entity_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    details = dict(row)
    connections = _get_connections(cur, entity_type, entity_id, details)
    conn.close()
    return {"entity": entity_type, "entityId": entity_id, "details": details, "connections": connections}


def _get_connections(cur, entity_type, entity_id, details):
    connections = []

    if entity_type == "SalesOrder":
        cur.execute("SELECT DISTINCT odi.deliveryDocument FROM outbound_delivery_items odi WHERE odi.referenceSdDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "Delivery", "id": str(r[0]), "relation": "HAS_DELIVERY", "direction": "outgoing"})
        cur.execute("SELECT DISTINCT soi.material FROM sales_order_items soi WHERE soi.salesOrder = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "Product", "id": str(r[0]), "relation": "CONTAINS_PRODUCT", "direction": "outgoing"})
        if details.get("soldToParty"):
            connections.append({"type": "Customer", "id": str(details["soldToParty"]), "relation": "PLACED_BY", "direction": "outgoing"})

    elif entity_type == "Delivery":
        cur.execute("SELECT DISTINCT bdi.billingDocument FROM billing_document_items bdi WHERE bdi.referenceSdDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "BillingDocument", "id": str(r[0]), "relation": "BILLED_AS", "direction": "outgoing"})
        cur.execute("SELECT DISTINCT odi.referenceSdDocument FROM outbound_delivery_items odi WHERE odi.deliveryDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "SalesOrder", "id": str(r[0]), "relation": "HAS_DELIVERY", "direction": "incoming"})
        cur.execute("SELECT DISTINCT odi.plant FROM outbound_delivery_items odi WHERE odi.deliveryDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "Plant", "id": str(r[0]), "relation": "FROM_PLANT", "direction": "outgoing"})

    elif entity_type == "BillingDocument":
        cur.execute("SELECT DISTINCT jei.accountingDocument FROM journal_entry_items jei WHERE jei.referenceDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "JournalEntry", "id": str(r[0]), "relation": "GENERATES_ENTRY", "direction": "outgoing"})
        cur.execute("SELECT DISTINCT bdi.referenceSdDocument FROM billing_document_items bdi WHERE bdi.billingDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "Delivery", "id": str(r[0]), "relation": "BILLED_AS", "direction": "incoming"})
        if details.get("soldToParty"):
            connections.append({"type": "Customer", "id": str(details["soldToParty"]), "relation": "BILLED_TO", "direction": "outgoing"})

    elif entity_type == "JournalEntry":
        cur.execute("SELECT DISTINCT p.accountingDocument FROM payments p WHERE p.clearingAccountingDocument = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "Payment", "id": str(r[0]), "relation": "CLEARED_BY", "direction": "outgoing"})
        if details.get("referenceDocument"):
            connections.append({"type": "BillingDocument", "id": str(details["referenceDocument"]), "relation": "GENERATES_ENTRY", "direction": "incoming"})

    elif entity_type == "Customer":
        cur.execute("SELECT DISTINCT soh.salesOrder FROM sales_order_headers soh WHERE soh.soldToParty = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "SalesOrder", "id": str(r[0]), "relation": "PLACED_BY", "direction": "incoming"})
        cur.execute("SELECT DISTINCT bdh.billingDocument FROM billing_document_headers bdh WHERE bdh.soldToParty = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "BillingDocument", "id": str(r[0]), "relation": "BILLED_TO", "direction": "incoming"})

    elif entity_type == "Product":
        cur.execute("SELECT DISTINCT soi.salesOrder FROM sales_order_items soi WHERE soi.material = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "SalesOrder", "id": str(r[0]), "relation": "CONTAINS_PRODUCT", "direction": "incoming"})

    elif entity_type == "Plant":
        cur.execute("SELECT DISTINCT odi.deliveryDocument FROM outbound_delivery_items odi WHERE odi.plant = ?", (entity_id,))
        for r in cur.fetchall():
            connections.append({"type": "Delivery", "id": str(r[0]), "relation": "FROM_PLANT", "direction": "incoming"})

    return connections


def get_neighbors(entity_type: str, entity_id: str):
    conn = get_connection()
    cur = conn.cursor()
    nodes = {}
    edges = []

    cur.execute(f"SELECT * FROM {ENTITY_CONFIG[entity_type]['table']} WHERE {ENTITY_CONFIG[entity_type]['id_col']} = ?", (entity_id,))
    row = cur.fetchone()
    details = dict(row) if row else {}
    connections = _get_connections(cur, entity_type, entity_id, details)

    for conn_item in connections:
        n_type = conn_item["type"]
        n_id = conn_item["id"]
        nid = f"{n_type}:{n_id}"
        cfg = ENTITY_CONFIG.get(n_type, {})
        if nid not in nodes:
            nodes[nid] = {
                "id": nid,
                "entity": n_type,
                "entityId": n_id,
                "label": n_id,
                "color": cfg.get("color", "#999"),
            }
        if conn_item["direction"] == "outgoing":
            edges.append({"source": f"{entity_type}:{entity_id}", "target": nid, "relation": conn_item["relation"]})
        else:
            edges.append({"source": nid, "target": f"{entity_type}:{entity_id}", "relation": conn_item["relation"]})

    conn.close()
    return {"nodes": list(nodes.values()), "edges": edges}
