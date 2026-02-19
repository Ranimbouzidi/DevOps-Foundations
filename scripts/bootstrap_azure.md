# Azure deployment notes

1. Create Azure Service Bus namespace with queues: discovery, page_scrape, product_scrape, pdf_fetch, ocr, diff (+ DLQ enabled).
2. Deploy lightweight workers as Azure Container Apps with queue-length KEDA rules.
3. Deploy headless and OCR workers in VM Scale Set Spot instances.
4. Run scheduler as a low-cost VM or Container App cron job.
5. Provision Azure Blob Storage and PostgreSQL Flexible Server.
