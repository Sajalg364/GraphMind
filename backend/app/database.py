import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "o2c.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS sales_order_headers (
            salesOrder TEXT PRIMARY KEY,
            salesOrderType TEXT,
            salesOrganization TEXT,
            distributionChannel TEXT,
            organizationDivision TEXT,
            salesGroup TEXT,
            salesOffice TEXT,
            soldToParty TEXT,
            creationDate TEXT,
            createdByUser TEXT,
            lastChangeDateTime TEXT,
            totalNetAmount REAL,
            overallDeliveryStatus TEXT,
            overallOrdReltdBillgStatus TEXT,
            overallSdDocReferenceStatus TEXT,
            transactionCurrency TEXT,
            pricingDate TEXT,
            requestedDeliveryDate TEXT,
            headerBillingBlockReason TEXT,
            deliveryBlockReason TEXT,
            incotermsClassification TEXT,
            incotermsLocation1 TEXT,
            customerPaymentTerms TEXT,
            totalCreditCheckStatus TEXT
        );

        CREATE TABLE IF NOT EXISTS sales_order_items (
            salesOrder TEXT,
            salesOrderItem TEXT,
            salesOrderItemCategory TEXT,
            material TEXT,
            requestedQuantity REAL,
            requestedQuantityUnit TEXT,
            transactionCurrency TEXT,
            netAmount REAL,
            materialGroup TEXT,
            productionPlant TEXT,
            storageLocation TEXT,
            salesDocumentRjcnReason TEXT,
            itemBillingBlockReason TEXT,
            PRIMARY KEY (salesOrder, salesOrderItem)
        );

        CREATE TABLE IF NOT EXISTS sales_order_schedule_lines (
            salesOrder TEXT,
            salesOrderItem TEXT,
            scheduleLine TEXT,
            confirmedDeliveryDate TEXT,
            orderQuantityUnit TEXT,
            confdOrderQtyByMatlAvailCheck REAL,
            PRIMARY KEY (salesOrder, salesOrderItem, scheduleLine)
        );

        CREATE TABLE IF NOT EXISTS outbound_delivery_headers (
            deliveryDocument TEXT PRIMARY KEY,
            actualGoodsMovementDate TEXT,
            creationDate TEXT,
            deliveryBlockReason TEXT,
            hdrGeneralIncompletionStatus TEXT,
            headerBillingBlockReason TEXT,
            lastChangeDate TEXT,
            overallGoodsMovementStatus TEXT,
            overallPickingStatus TEXT,
            overallProofOfDeliveryStatus TEXT,
            shippingPoint TEXT
        );

        CREATE TABLE IF NOT EXISTS outbound_delivery_items (
            deliveryDocument TEXT,
            deliveryDocumentItem TEXT,
            actualDeliveryQuantity REAL,
            batch TEXT,
            deliveryQuantityUnit TEXT,
            itemBillingBlockReason TEXT,
            lastChangeDate TEXT,
            plant TEXT,
            referenceSdDocument TEXT,
            referenceSdDocumentItem TEXT,
            storageLocation TEXT,
            PRIMARY KEY (deliveryDocument, deliveryDocumentItem)
        );

        CREATE TABLE IF NOT EXISTS billing_document_headers (
            billingDocument TEXT PRIMARY KEY,
            billingDocumentType TEXT,
            creationDate TEXT,
            billingDocumentDate TEXT,
            billingDocumentIsCancelled INTEGER,
            cancelledBillingDocument TEXT,
            totalNetAmount REAL,
            transactionCurrency TEXT,
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            soldToParty TEXT,
            lastChangeDateTime TEXT
        );

        CREATE TABLE IF NOT EXISTS billing_document_items (
            billingDocument TEXT,
            billingDocumentItem TEXT,
            material TEXT,
            billingQuantity REAL,
            billingQuantityUnit TEXT,
            netAmount REAL,
            transactionCurrency TEXT,
            referenceSdDocument TEXT,
            referenceSdDocumentItem TEXT,
            PRIMARY KEY (billingDocument, billingDocumentItem)
        );

        CREATE TABLE IF NOT EXISTS billing_document_cancellations (
            billingDocument TEXT PRIMARY KEY,
            billingDocumentType TEXT,
            creationDate TEXT,
            billingDocumentDate TEXT,
            billingDocumentIsCancelled INTEGER,
            cancelledBillingDocument TEXT,
            totalNetAmount REAL,
            transactionCurrency TEXT,
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            soldToParty TEXT,
            lastChangeDateTime TEXT
        );

        CREATE TABLE IF NOT EXISTS journal_entry_items (
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            accountingDocumentItem TEXT,
            glAccount TEXT,
            referenceDocument TEXT,
            costCenter TEXT,
            profitCenter TEXT,
            transactionCurrency TEXT,
            amountInTransactionCurrency REAL,
            companyCodeCurrency TEXT,
            amountInCompanyCodeCurrency REAL,
            postingDate TEXT,
            documentDate TEXT,
            accountingDocumentType TEXT,
            assignmentReference TEXT,
            lastChangeDateTime TEXT,
            customer TEXT,
            financialAccountType TEXT,
            clearingDate TEXT,
            clearingAccountingDocument TEXT,
            clearingDocFiscalYear TEXT,
            PRIMARY KEY (companyCode, fiscalYear, accountingDocument, accountingDocumentItem)
        );

        CREATE TABLE IF NOT EXISTS payments (
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            accountingDocumentItem TEXT,
            clearingDate TEXT,
            clearingAccountingDocument TEXT,
            clearingDocFiscalYear TEXT,
            amountInTransactionCurrency REAL,
            transactionCurrency TEXT,
            amountInCompanyCodeCurrency REAL,
            companyCodeCurrency TEXT,
            customer TEXT,
            invoiceReference TEXT,
            invoiceReferenceFiscalYear TEXT,
            salesDocument TEXT,
            salesDocumentItem TEXT,
            postingDate TEXT,
            documentDate TEXT,
            assignmentReference TEXT,
            glAccount TEXT,
            financialAccountType TEXT,
            profitCenter TEXT,
            costCenter TEXT,
            PRIMARY KEY (companyCode, fiscalYear, accountingDocument, accountingDocumentItem)
        );

        CREATE TABLE IF NOT EXISTS business_partners (
            businessPartner TEXT PRIMARY KEY,
            customer TEXT,
            businessPartnerCategory TEXT,
            businessPartnerFullName TEXT,
            businessPartnerGrouping TEXT,
            businessPartnerName TEXT,
            correspondenceLanguage TEXT,
            createdByUser TEXT,
            creationDate TEXT,
            firstName TEXT,
            formOfAddress TEXT,
            industry TEXT,
            lastChangeDate TEXT,
            lastName TEXT,
            organizationBpName1 TEXT,
            organizationBpName2 TEXT,
            businessPartnerIsBlocked INTEGER,
            isMarkedForArchiving INTEGER
        );

        CREATE TABLE IF NOT EXISTS business_partner_addresses (
            businessPartner TEXT,
            addressId TEXT,
            validityStartDate TEXT,
            validityEndDate TEXT,
            addressTimeZone TEXT,
            cityName TEXT,
            country TEXT,
            postalCode TEXT,
            region TEXT,
            streetName TEXT,
            PRIMARY KEY (businessPartner, addressId)
        );

        CREATE TABLE IF NOT EXISTS customer_company_assignments (
            customer TEXT,
            companyCode TEXT,
            reconciliationAccount TEXT,
            deletionIndicator INTEGER,
            customerAccountGroup TEXT,
            PRIMARY KEY (customer, companyCode)
        );

        CREATE TABLE IF NOT EXISTS customer_sales_area_assignments (
            customer TEXT,
            salesOrganization TEXT,
            distributionChannel TEXT,
            division TEXT,
            currency TEXT,
            customerPaymentTerms TEXT,
            incotermsClassification TEXT,
            incotermsLocation1 TEXT,
            shippingCondition TEXT,
            PRIMARY KEY (customer, salesOrganization, distributionChannel, division)
        );

        CREATE TABLE IF NOT EXISTS products (
            product TEXT PRIMARY KEY,
            productType TEXT,
            creationDate TEXT,
            createdByUser TEXT,
            lastChangeDate TEXT,
            isMarkedForDeletion INTEGER,
            productOldId TEXT,
            grossWeight REAL,
            weightUnit TEXT,
            netWeight REAL,
            productGroup TEXT,
            baseUnit TEXT,
            division TEXT,
            industrySector TEXT
        );

        CREATE TABLE IF NOT EXISTS product_descriptions (
            product TEXT,
            language TEXT,
            productDescription TEXT,
            PRIMARY KEY (product, language)
        );

        CREATE TABLE IF NOT EXISTS product_plants (
            product TEXT,
            plant TEXT,
            profitCenter TEXT,
            mrpType TEXT,
            availabilityCheckType TEXT,
            PRIMARY KEY (product, plant)
        );

        CREATE TABLE IF NOT EXISTS product_storage_locations (
            product TEXT,
            plant TEXT,
            storageLocation TEXT,
            PRIMARY KEY (product, plant, storageLocation)
        );

        CREATE TABLE IF NOT EXISTS plants (
            plant TEXT PRIMARY KEY,
            plantName TEXT,
            valuationArea TEXT,
            factoryCalendar TEXT,
            salesOrganization TEXT,
            distributionChannel TEXT,
            division TEXT,
            language TEXT,
            isMarkedForArchiving INTEGER
        );

        -- Indexes for common join paths
        CREATE INDEX IF NOT EXISTS idx_soi_salesorder ON sales_order_items(salesOrder);
        CREATE INDEX IF NOT EXISTS idx_soi_material ON sales_order_items(material);
        CREATE INDEX IF NOT EXISTS idx_sosl_salesorder ON sales_order_schedule_lines(salesOrder);
        CREATE INDEX IF NOT EXISTS idx_odi_ref ON outbound_delivery_items(referenceSdDocument);
        CREATE INDEX IF NOT EXISTS idx_odi_delivery ON outbound_delivery_items(deliveryDocument);
        CREATE INDEX IF NOT EXISTS idx_odi_plant ON outbound_delivery_items(plant);
        CREATE INDEX IF NOT EXISTS idx_bdi_ref ON billing_document_items(referenceSdDocument);
        CREATE INDEX IF NOT EXISTS idx_bdi_billing ON billing_document_items(billingDocument);
        CREATE INDEX IF NOT EXISTS idx_bdi_material ON billing_document_items(material);
        CREATE INDEX IF NOT EXISTS idx_bdh_soldto ON billing_document_headers(soldToParty);
        CREATE INDEX IF NOT EXISTS idx_bdh_acctdoc ON billing_document_headers(accountingDocument);
        CREATE INDEX IF NOT EXISTS idx_jei_refdoc ON journal_entry_items(referenceDocument);
        CREATE INDEX IF NOT EXISTS idx_jei_clearing ON journal_entry_items(clearingAccountingDocument);
        CREATE INDEX IF NOT EXISTS idx_jei_customer ON journal_entry_items(customer);
        CREATE INDEX IF NOT EXISTS idx_pay_clearing ON payments(clearingAccountingDocument);
        CREATE INDEX IF NOT EXISTS idx_pay_customer ON payments(customer);
        CREATE INDEX IF NOT EXISTS idx_soh_soldto ON sales_order_headers(soldToParty);
        CREATE INDEX IF NOT EXISTS idx_bp_customer ON business_partners(customer);
    """)

    conn.commit()
    conn.close()

SCHEMA_DESCRIPTION = """
Database: SAP Order-to-Cash (O2C) SQLite Database

Tables and their columns:

1. sales_order_headers - Sales orders placed by customers
   - salesOrder (PK), salesOrderType, salesOrganization, distributionChannel, organizationDivision, salesGroup, salesOffice, soldToParty (FK→business_partners.businessPartner), creationDate, createdByUser, lastChangeDateTime, totalNetAmount, overallDeliveryStatus, overallOrdReltdBillgStatus, overallSdDocReferenceStatus, transactionCurrency, pricingDate, requestedDeliveryDate, headerBillingBlockReason, deliveryBlockReason, incotermsClassification, incotermsLocation1, customerPaymentTerms, totalCreditCheckStatus

2. sales_order_items - Line items within a sales order
   - salesOrder (FK→sales_order_headers), salesOrderItem, salesOrderItemCategory, material (FK→products.product), requestedQuantity, requestedQuantityUnit, transactionCurrency, netAmount, materialGroup, productionPlant, storageLocation, salesDocumentRjcnReason, itemBillingBlockReason

3. sales_order_schedule_lines - Delivery schedules for sales order items
   - salesOrder (FK→sales_order_headers), salesOrderItem, scheduleLine, confirmedDeliveryDate, orderQuantityUnit, confdOrderQtyByMatlAvailCheck

4. outbound_delivery_headers - Delivery documents for shipping
   - deliveryDocument (PK), actualGoodsMovementDate, creationDate, deliveryBlockReason, hdrGeneralIncompletionStatus, headerBillingBlockReason, lastChangeDate, overallGoodsMovementStatus, overallPickingStatus, overallProofOfDeliveryStatus, shippingPoint

5. outbound_delivery_items - Line items within deliveries
   - deliveryDocument (FK→outbound_delivery_headers), deliveryDocumentItem, actualDeliveryQuantity, batch, deliveryQuantityUnit, itemBillingBlockReason, lastChangeDate, plant (FK→plants.plant), referenceSdDocument (FK→sales_order_headers.salesOrder), referenceSdDocumentItem, storageLocation

6. billing_document_headers - Invoices and billing documents
   - billingDocument (PK), billingDocumentType, creationDate, billingDocumentDate, billingDocumentIsCancelled, cancelledBillingDocument, totalNetAmount, transactionCurrency, companyCode, fiscalYear, accountingDocument (links to journal_entry_items.accountingDocument), soldToParty (FK→business_partners.businessPartner), lastChangeDateTime

7. billing_document_items - Line items within billing documents
   - billingDocument (FK→billing_document_headers), billingDocumentItem, material (FK→products.product), billingQuantity, billingQuantityUnit, netAmount, transactionCurrency, referenceSdDocument (FK→outbound_delivery_headers.deliveryDocument), referenceSdDocumentItem

8. billing_document_cancellations - Cancelled billing documents
   - billingDocument (PK), billingDocumentType, creationDate, billingDocumentDate, billingDocumentIsCancelled, cancelledBillingDocument, totalNetAmount, transactionCurrency, companyCode, fiscalYear, accountingDocument, soldToParty, lastChangeDateTime

9. journal_entry_items - Accounting journal entries (accounts receivable)
   - companyCode, fiscalYear, accountingDocument, accountingDocumentItem, glAccount, referenceDocument (FK→billing_document_headers.billingDocument), costCenter, profitCenter, transactionCurrency, amountInTransactionCurrency, companyCodeCurrency, amountInCompanyCodeCurrency, postingDate, documentDate, accountingDocumentType, assignmentReference, lastChangeDateTime, customer (FK→business_partners.customer), financialAccountType, clearingDate, clearingAccountingDocument, clearingDocFiscalYear

10. payments - Payment records for accounts receivable
    - companyCode, fiscalYear, accountingDocument, accountingDocumentItem, clearingDate, clearingAccountingDocument, clearingDocFiscalYear, amountInTransactionCurrency, transactionCurrency, amountInCompanyCodeCurrency, companyCodeCurrency, customer (FK→business_partners.customer), invoiceReference, invoiceReferenceFiscalYear, salesDocument, salesDocumentItem, postingDate, documentDate, assignmentReference, glAccount, financialAccountType, profitCenter, costCenter

11. business_partners - Customer/partner master data
    - businessPartner (PK), customer, businessPartnerCategory, businessPartnerFullName, businessPartnerGrouping, businessPartnerName, correspondenceLanguage, createdByUser, creationDate, firstName, formOfAddress, industry, lastChangeDate, lastName, organizationBpName1, organizationBpName2, businessPartnerIsBlocked, isMarkedForArchiving

12. business_partner_addresses - Addresses for business partners
    - businessPartner (FK→business_partners), addressId, validityStartDate, validityEndDate, addressTimeZone, cityName, country, postalCode, region, streetName

13. customer_company_assignments - Customer to company code assignments
    - customer, companyCode, reconciliationAccount, deletionIndicator, customerAccountGroup

14. customer_sales_area_assignments - Customer sales area config
    - customer, salesOrganization, distributionChannel, division, currency, customerPaymentTerms, incotermsClassification, incotermsLocation1, shippingCondition

15. products - Product master data
    - product (PK), productType, creationDate, createdByUser, lastChangeDate, isMarkedForDeletion, productOldId, grossWeight, weightUnit, netWeight, productGroup, baseUnit, division, industrySector

16. product_descriptions - Product text descriptions
    - product (FK→products), language, productDescription

17. product_plants - Product-plant assignments
    - product (FK→products), plant (FK→plants), profitCenter, mrpType, availabilityCheckType

18. product_storage_locations - Product storage location data
    - product (FK→products), plant (FK→plants), storageLocation

19. plants - Manufacturing/warehouse plant master data
    - plant (PK), plantName, valuationArea, factoryCalendar, salesOrganization, distributionChannel, division, language, isMarkedForArchiving

KEY RELATIONSHIPS (Order-to-Cash Flow):
- Sales Order Header → Sales Order Items (salesOrder)
- Sales Order Items → Outbound Delivery Items (outbound_delivery_items.referenceSdDocument = sales_order_items.salesOrder)
- Outbound Delivery Items → Outbound Delivery Headers (deliveryDocument)
- Billing Document Items → Outbound Delivery (billing_document_items.referenceSdDocument = outbound_delivery_headers.deliveryDocument)
- Billing Document Items → Billing Document Headers (billingDocument)
- Billing Document Headers → Journal Entry Items (journal_entry_items.referenceDocument = billing_document_headers.billingDocument)
- Journal Entry Items → Payments (payments.clearingAccountingDocument = journal_entry_items.accountingDocument)
- Sales Order Headers → Business Partners (soldToParty = businessPartner)
- Sales Order Items → Products (material = product)
- Outbound Delivery Items → Plants (plant)
- Billing Document Headers → Business Partners (soldToParty = businessPartner)
"""
