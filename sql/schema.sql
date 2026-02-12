IF DB_ID('ExcelImportDB') IS NULL
BEGIN
    CREATE DATABASE ExcelImportDB;
END
GO

USE ExcelImportDB;
GO

IF OBJECT_ID('dbo.sales_records', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.sales_records (
        id INT IDENTITY(1,1) PRIMARY KEY,
        business_key NVARCHAR(100) NOT NULL UNIQUE,
        name NVARCHAR(255) NOT NULL,
        amount DECIMAL(18,2) NOT NULL,
        record_date DATE NOT NULL,
        invoice_date DATE NULL,
        invoice_no NVARCHAR(100) NULL,
        item_description NVARCHAR(255) NULL,
        product_value DECIMAL(18,2) NULL,
        tax_value DECIMAL(18,2) NULL,
        total_value DECIMAL(18,2) NULL,
        vin_no NVARCHAR(100) NULL,
        cancel_flag NVARCHAR(50) NULL,
        cancel_product_value DECIMAL(18,2) NULL,
        cancel_tax_value DECIMAL(18,2) NULL,
        cancel_total_value DECIMAL(18,2) NULL,
        org_type_hq NVARCHAR(50) NULL,
        org_type_branch_no INT NULL,
        taxpayer_id NVARCHAR(20) NULL,
        sale_price DECIMAL(18,2) NULL,
        com_fn DECIMAL(18,2) NULL,
        com_value DECIMAL(18,2) NULL,
        rule_applied NVARCHAR(100) NULL,
        is_duplicate_tank BIT NULL,
        group_id NVARCHAR(150) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

IF COL_LENGTH('dbo.sales_records', 'invoice_date') IS NULL
    ALTER TABLE dbo.sales_records ADD invoice_date DATE NULL;
IF COL_LENGTH('dbo.sales_records', 'invoice_no') IS NULL
    ALTER TABLE dbo.sales_records ADD invoice_no NVARCHAR(100) NULL;
IF COL_LENGTH('dbo.sales_records', 'item_description') IS NULL
    ALTER TABLE dbo.sales_records ADD item_description NVARCHAR(255) NULL;
IF COL_LENGTH('dbo.sales_records', 'product_value') IS NULL
    ALTER TABLE dbo.sales_records ADD product_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'tax_value') IS NULL
    ALTER TABLE dbo.sales_records ADD tax_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'total_value') IS NULL
    ALTER TABLE dbo.sales_records ADD total_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'vin_no') IS NULL
    ALTER TABLE dbo.sales_records ADD vin_no NVARCHAR(100) NULL;
IF COL_LENGTH('dbo.sales_records', 'cancel_flag') IS NULL
    ALTER TABLE dbo.sales_records ADD cancel_flag NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.sales_records', 'cancel_product_value') IS NULL
    ALTER TABLE dbo.sales_records ADD cancel_product_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'cancel_tax_value') IS NULL
    ALTER TABLE dbo.sales_records ADD cancel_tax_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'cancel_total_value') IS NULL
    ALTER TABLE dbo.sales_records ADD cancel_total_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'org_type_hq') IS NULL
    ALTER TABLE dbo.sales_records ADD org_type_hq NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.sales_records', 'org_type_branch_no') IS NULL
    ALTER TABLE dbo.sales_records ADD org_type_branch_no INT NULL;
IF COL_LENGTH('dbo.sales_records', 'taxpayer_id') IS NULL
    ALTER TABLE dbo.sales_records ADD taxpayer_id NVARCHAR(20) NULL;
IF COL_LENGTH('dbo.sales_records', 'sale_price') IS NULL
    ALTER TABLE dbo.sales_records ADD sale_price DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'com_fn') IS NULL
    ALTER TABLE dbo.sales_records ADD com_fn DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'com_value') IS NULL
    ALTER TABLE dbo.sales_records ADD com_value DECIMAL(18,2) NULL;
IF COL_LENGTH('dbo.sales_records', 'rule_applied') IS NULL
    ALTER TABLE dbo.sales_records ADD rule_applied NVARCHAR(100) NULL;
IF COL_LENGTH('dbo.sales_records', 'is_duplicate_tank') IS NULL
    ALTER TABLE dbo.sales_records ADD is_duplicate_tank BIT NULL;
IF COL_LENGTH('dbo.sales_records', 'group_id') IS NULL
    ALTER TABLE dbo.sales_records ADD group_id NVARCHAR(150) NULL;
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_sales_records_group_id'
      AND object_id = OBJECT_ID('dbo.sales_records')
)
    CREATE INDEX IX_sales_records_group_id ON dbo.sales_records(group_id);
GO

IF OBJECT_ID('dbo.import_jobs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.import_jobs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        correlation_id NVARCHAR(64) NOT NULL,
        filename NVARCHAR(255) NOT NULL,
        status NVARCHAR(20) NOT NULL,
        total_rows INT NOT NULL DEFAULT 0,
        imported_rows INT NOT NULL DEFAULT 0,
        failed_rows INT NOT NULL DEFAULT 0,
        message NVARCHAR(MAX) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_import_jobs_status ON dbo.import_jobs(status);
    CREATE INDEX IX_import_jobs_correlation_id ON dbo.import_jobs(correlation_id);
END
GO

IF OBJECT_ID('dbo.import_errors', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.import_errors (
        id INT IDENTITY(1,1) PRIMARY KEY,
        job_id INT NOT NULL,
        row_number INT NOT NULL,
        column_name NVARCHAR(100) NULL,
        error_message NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_import_errors_job FOREIGN KEY (job_id) REFERENCES dbo.import_jobs(id)
    );
    CREATE INDEX IX_import_errors_job_id ON dbo.import_errors(job_id);
END
GO
