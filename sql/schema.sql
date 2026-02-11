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
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
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
