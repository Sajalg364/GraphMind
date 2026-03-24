import json
import os
import glob
from pathlib import Path
from .database import get_connection, init_db

DATA_DIR = Path(__file__).parent.parent.parent / "sap-order-to-cash-dataset" / "sap-o2c-data"

TABLE_MAP = {
    "sales_order_headers": "sales_order_headers",
    "sales_order_items": "sales_order_items",
    "sales_order_schedule_lines": "sales_order_schedule_lines",
    "outbound_delivery_headers": "outbound_delivery_headers",
    "outbound_delivery_items": "outbound_delivery_items",
    "billing_document_headers": "billing_document_headers",
    "billing_document_items": "billing_document_items",
    "billing_document_cancellations": "billing_document_cancellations",
    "journal_entry_items_accounts_receivable": "journal_entry_items",
    "payments_accounts_receivable": "payments",
    "business_partners": "business_partners",
    "business_partner_addresses": "business_partner_addresses",
    "customer_company_assignments": "customer_company_assignments",
    "customer_sales_area_assignments": "customer_sales_area_assignments",
    "products": "products",
    "product_descriptions": "product_descriptions",
    "product_plants": "product_plants",
    "product_storage_locations": "product_storage_locations",
    "plants": "plants",
}

COLUMN_MAP = {
    "sales_order_headers": [
        "salesOrder", "salesOrderType", "salesOrganization", "distributionChannel",
        "organizationDivision", "salesGroup", "salesOffice", "soldToParty",
        "creationDate", "createdByUser", "lastChangeDateTime", "totalNetAmount",
        "overallDeliveryStatus", "overallOrdReltdBillgStatus", "overallSdDocReferenceStatus",
        "transactionCurrency", "pricingDate", "requestedDeliveryDate",
        "headerBillingBlockReason", "deliveryBlockReason", "incotermsClassification",
        "incotermsLocation1", "customerPaymentTerms", "totalCreditCheckStatus"
    ],
    "sales_order_items": [
        "salesOrder", "salesOrderItem", "salesOrderItemCategory", "material",
        "requestedQuantity", "requestedQuantityUnit", "transactionCurrency", "netAmount",
        "materialGroup", "productionPlant", "storageLocation", "salesDocumentRjcnReason",
        "itemBillingBlockReason"
    ],
    "sales_order_schedule_lines": [
        "salesOrder", "salesOrderItem", "scheduleLine", "confirmedDeliveryDate",
        "orderQuantityUnit", "confdOrderQtyByMatlAvailCheck"
    ],
    "outbound_delivery_headers": [
        "deliveryDocument", "actualGoodsMovementDate", "creationDate",
        "deliveryBlockReason", "hdrGeneralIncompletionStatus", "headerBillingBlockReason",
        "lastChangeDate", "overallGoodsMovementStatus", "overallPickingStatus",
        "overallProofOfDeliveryStatus", "shippingPoint"
    ],
    "outbound_delivery_items": [
        "deliveryDocument", "deliveryDocumentItem", "actualDeliveryQuantity", "batch",
        "deliveryQuantityUnit", "itemBillingBlockReason", "lastChangeDate", "plant",
        "referenceSdDocument", "referenceSdDocumentItem", "storageLocation"
    ],
    "billing_document_headers": [
        "billingDocument", "billingDocumentType", "creationDate", "billingDocumentDate",
        "billingDocumentIsCancelled", "cancelledBillingDocument", "totalNetAmount",
        "transactionCurrency", "companyCode", "fiscalYear", "accountingDocument",
        "soldToParty", "lastChangeDateTime"
    ],
    "billing_document_items": [
        "billingDocument", "billingDocumentItem", "material", "billingQuantity",
        "billingQuantityUnit", "netAmount", "transactionCurrency",
        "referenceSdDocument", "referenceSdDocumentItem"
    ],
    "billing_document_cancellations": [
        "billingDocument", "billingDocumentType", "creationDate", "billingDocumentDate",
        "billingDocumentIsCancelled", "cancelledBillingDocument", "totalNetAmount",
        "transactionCurrency", "companyCode", "fiscalYear", "accountingDocument",
        "soldToParty", "lastChangeDateTime"
    ],
    "journal_entry_items": [
        "companyCode", "fiscalYear", "accountingDocument", "accountingDocumentItem",
        "glAccount", "referenceDocument", "costCenter", "profitCenter",
        "transactionCurrency", "amountInTransactionCurrency", "companyCodeCurrency",
        "amountInCompanyCodeCurrency", "postingDate", "documentDate",
        "accountingDocumentType", "assignmentReference", "lastChangeDateTime",
        "customer", "financialAccountType", "clearingDate", "clearingAccountingDocument",
        "clearingDocFiscalYear"
    ],
    "payments": [
        "companyCode", "fiscalYear", "accountingDocument", "accountingDocumentItem",
        "clearingDate", "clearingAccountingDocument", "clearingDocFiscalYear",
        "amountInTransactionCurrency", "transactionCurrency", "amountInCompanyCodeCurrency",
        "companyCodeCurrency", "customer", "invoiceReference", "invoiceReferenceFiscalYear",
        "salesDocument", "salesDocumentItem", "postingDate", "documentDate",
        "assignmentReference", "glAccount", "financialAccountType", "profitCenter",
        "costCenter"
    ],
    "business_partners": [
        "businessPartner", "customer", "businessPartnerCategory", "businessPartnerFullName",
        "businessPartnerGrouping", "businessPartnerName", "correspondenceLanguage",
        "createdByUser", "creationDate", "firstName", "formOfAddress", "industry",
        "lastChangeDate", "lastName", "organizationBpName1", "organizationBpName2",
        "businessPartnerIsBlocked", "isMarkedForArchiving"
    ],
    "business_partner_addresses": [
        "businessPartner", "addressId", "validityStartDate", "validityEndDate",
        "addressTimeZone", "cityName", "country", "postalCode", "region", "streetName"
    ],
    "customer_company_assignments": [
        "customer", "companyCode", "reconciliationAccount", "deletionIndicator",
        "customerAccountGroup"
    ],
    "customer_sales_area_assignments": [
        "customer", "salesOrganization", "distributionChannel", "division",
        "currency", "customerPaymentTerms", "incotermsClassification",
        "incotermsLocation1", "shippingCondition"
    ],
    "products": [
        "product", "productType", "creationDate", "createdByUser", "lastChangeDate",
        "isMarkedForDeletion", "productOldId", "grossWeight", "weightUnit", "netWeight",
        "productGroup", "baseUnit", "division", "industrySector"
    ],
    "product_descriptions": ["product", "language", "productDescription"],
    "product_plants": ["product", "plant", "profitCenter", "mrpType", "availabilityCheckType"],
    "product_storage_locations": ["product", "plant", "storageLocation"],
    "plants": [
        "plant", "plantName", "valuationArea", "factoryCalendar", "salesOrganization",
        "distributionChannel", "division", "language", "isMarkedForArchiving"
    ],
}

def flatten_value(val):
    if isinstance(val, dict):
        return json.dumps(val)
    return val

def ingest_all():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    for folder_name, table_name in TABLE_MAP.items():
        folder_path = DATA_DIR / folder_name
        if not folder_path.exists():
            print(f"Skipping {folder_name}: directory not found")
            continue

        columns = COLUMN_MAP.get(table_name)
        if not columns:
            continue

        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT OR IGNORE INTO {table_name} ({col_str}) VALUES ({placeholders})"

        count = 0
        for jsonl_file in sorted(folder_path.glob("*.jsonl")):
            with open(jsonl_file, "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    values = [flatten_value(row.get(col)) for col in columns]
                    batch.append(values)
                    if len(batch) >= 1000:
                        cur.executemany(sql, batch)
                        count += len(batch)
                        batch = []
                if batch:
                    cur.executemany(sql, batch)
                    count += len(batch)

        conn.commit()
        print(f"Loaded {count} rows into {table_name}")

    conn.close()
    print("Data ingestion complete.")

if __name__ == "__main__":
    ingest_all()
