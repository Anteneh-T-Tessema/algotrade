-- Database Schema for Multi-Tier User System

-- Users Table: Stores all users regardless of role
CREATE TABLE Users (
    UserId UUID PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Email VARCHAR(255) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    PhoneNumber VARCHAR(20),
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastLogin TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    TwoFactorEnabled BOOLEAN DEFAULT FALSE,
    ProfilePictureUrl VARCHAR(255),
    CountryCode VARCHAR(5),
    VerificationStatus VARCHAR(20) DEFAULT 'UNVERIFIED',  -- UNVERIFIED, PENDING, VERIFIED
    ReferralCode VARCHAR(20) UNIQUE,
    ReferredBy UUID REFERENCES Users(UserId)
);

-- Roles Table: Defines system roles
CREATE TABLE Roles (
    RoleId INT PRIMARY KEY,
    RoleName VARCHAR(50) UNIQUE NOT NULL,
    Description TEXT,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Initialize roles
INSERT INTO Roles (RoleId, RoleName, Description) VALUES
(1, 'ADMIN', 'System administrator with full access'),
(2, 'MASTER_DISTRIBUTOR', 'Top-level distributor managing multiple distributors'),
(3, 'DISTRIBUTOR', 'Manages end users and earns commissions'),
(4, 'USER', 'End user of the trading platform');

-- UserRoles Table: Many-to-many relationship between users and roles
CREATE TABLE UserRoles (
    UserId UUID REFERENCES Users(UserId),
    RoleId INT REFERENCES Roles(RoleId),
    AssignedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AssignedBy UUID REFERENCES Users(UserId),
    PRIMARY KEY (UserId, RoleId)
);

-- DistributorNetwork Table: Tracks distributor relationships
CREATE TABLE DistributorNetwork (
    DistributorId UUID REFERENCES Users(UserId),
    UplineId UUID REFERENCES Users(UserId),
    Level INT NOT NULL, -- Level in hierarchy (0 for master distributors, 1, 2, etc. for lower levels)
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ModifiedAt TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (DistributorId, UplineId)
);

-- CommissionPlans Table: Defines commission structures
CREATE TABLE CommissionPlans (
    PlanId UUID PRIMARY KEY,
    PlanName VARCHAR(100) NOT NULL,
    Description TEXT,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ModifiedAt TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedBy UUID REFERENCES Users(UserId)
);

-- CommissionRates Table: Detailed commission rates by level
CREATE TABLE CommissionRates (
    RateId UUID PRIMARY KEY,
    PlanId UUID REFERENCES CommissionPlans(PlanId),
    DistributorLevel INT NOT NULL, -- 0=Master, 1=Level 1, etc.
    CommissionPercentage DECIMAL(5,2) NOT NULL,
    MinimumTradingVolume DECIMAL(20,8),
    MaximumCommission DECIMAL(20,2),
    IsActive BOOLEAN DEFAULT TRUE
);

-- UserCommissionPlans: Associates users with commission plans
CREATE TABLE UserCommissionPlans (
    UserId UUID REFERENCES Users(UserId),
    PlanId UUID REFERENCES CommissionPlans(PlanId),
    AssignedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (UserId, PlanId)
);

-- Subscriptions Table: Tracks user subscriptions
CREATE TABLE Subscriptions (
    SubscriptionId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    PlanId UUID,
    StartDate TIMESTAMP NOT NULL,
    EndDate TIMESTAMP,
    Price DECIMAL(10,2) NOT NULL,
    Currency VARCHAR(10) DEFAULT 'USD',
    PaymentStatus VARCHAR(20) NOT NULL,
    AutoRenew BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ModifiedAt TIMESTAMP,
    CancellationDate TIMESTAMP,
    DistributorId UUID REFERENCES Users(UserId)
);

-- Wallets Table: Manages user crypto wallets
CREATE TABLE Wallets (
    WalletId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    Currency VARCHAR(10) NOT NULL,
    Balance DECIMAL(20,8) DEFAULT 0,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastUpdated TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    UNIQUE (UserId, Currency)
);

-- Commission Transactions
CREATE TABLE CommissionTransactions (
    TransactionId UUID PRIMARY KEY,
    FromUserId UUID REFERENCES Users(UserId),
    ToUserId UUID REFERENCES Users(UserId),
    Amount DECIMAL(20,8) NOT NULL,
    Currency VARCHAR(10) NOT NULL,
    TransactionType VARCHAR(50) NOT NULL, -- COMMISSION, WITHDRAWAL, etc.
    ReferenceId VARCHAR(100), -- e.g., trade ID, subscription ID
    Status VARCHAR(20) NOT NULL, -- PENDING, COMPLETED, FAILED
    ProcessedAt TIMESTAMP,
    Description TEXT,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- API Keys for exchange connections
CREATE TABLE ApiKeys (
    KeyId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    ExchangeName VARCHAR(50) NOT NULL,
    ApiKey VARCHAR(255) NOT NULL,
    ApiSecret VARCHAR(255) NOT NULL,
    Label VARCHAR(100),
    Permissions TEXT[], -- READ, TRADE, WITHDRAW
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastUsed TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE
);

-- User Strategy Settings
CREATE TABLE UserStrategySettings (
    SettingId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    StrategyType VARCHAR(50) NOT NULL, -- e.g., DCA, GRID, SCALPING
    Symbol VARCHAR(20) NOT NULL,
    Parameters JSONB NOT NULL, -- Strategy-specific parameters
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ModifiedAt TIMESTAMP,
    LastExecuted TIMESTAMP,
    Performance JSONB -- Strategy performance metrics
);

-- Trading Activity
CREATE TABLE TradingActivity (
    ActivityId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    StrategyId UUID REFERENCES UserStrategySettings(SettingId),
    ExchangeName VARCHAR(50) NOT NULL,
    Symbol VARCHAR(20) NOT NULL,
    OrderId VARCHAR(100),
    OrderType VARCHAR(20), -- MARKET, LIMIT, etc.
    Side VARCHAR(10), -- BUY or SELL
    Quantity DECIMAL(20,8),
    Price DECIMAL(20,8),
    ExecutedAt TIMESTAMP,
    Fee DECIMAL(20,8),
    FeeCurrency VARCHAR(10),
    PnL DECIMAL(20,8),
    PnLPercentage DECIMAL(10,2),
    Status VARCHAR(20), -- OPEN, FILLED, CANCELLED, etc.
    Notes TEXT,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- User Notifications
CREATE TABLE Notifications (
    NotificationId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    Title VARCHAR(100) NOT NULL,
    Message TEXT NOT NULL,
    Type VARCHAR(20) NOT NULL, -- ALERT, INFO, SUCCESS, ERROR
    IsRead BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt TIMESTAMP,
    RelatedEntity VARCHAR(50), -- e.g., TRADE, SUBSCRIPTION, COMMISSION
    RelatedEntityId UUID
);

-- Audit Log for all major actions
CREATE TABLE AuditLog (
    LogId UUID PRIMARY KEY,
    UserId UUID REFERENCES Users(UserId),
    Action VARCHAR(100) NOT NULL,
    EntityType VARCHAR(50), -- USER, TRADE, COMMISSION, etc.
    EntityId UUID,
    OldValue JSONB,
    NewValue JSONB,
    IpAddress VARCHAR(45),
    UserAgent TEXT,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- System Settings
CREATE TABLE SystemSettings (
    SettingKey VARCHAR(100) PRIMARY KEY,
    SettingValue TEXT NOT NULL,
    DataType VARCHAR(20) NOT NULL, -- STRING, NUMBER, BOOLEAN, JSON
    Description TEXT,
    IsEditable BOOLEAN DEFAULT TRUE,
    ModifiedAt TIMESTAMP,
    ModifiedBy UUID REFERENCES Users(UserId)
);

-- Insert initial admin user
INSERT INTO Users (UserId, Username, Email, PasswordHash, FirstName, LastName, IsActive, VerificationStatus)
VALUES (
    'e7de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c',
    'admin',
    'admin@cryptotrading.com',
    '$2a$10$hACwQ5oIeKJwjzBG2vcQs.6RU3GsJy3LPTUaVWRhQK4OXmGQUC9Ny', -- Password hash for 'adminpassword'
    'System',
    'Administrator',
    TRUE,
    'VERIFIED'
);

-- Assign admin role
INSERT INTO UserRoles (UserId, RoleId, AssignedBy)
VALUES ('e7de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c', 1, 'e7de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c');

-- Create initial default commission plan
INSERT INTO CommissionPlans (PlanId, PlanName, Description, CreatedBy)
VALUES (
    'f8de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c',
    'Default Commission Plan',
    'Default three-tier commission structure for all distributors',
    'e7de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c'
);

-- Set commission rates for different levels
INSERT INTO CommissionRates (RateId, PlanId, DistributorLevel, CommissionPercentage)
VALUES
    (uuid_generate_v4(), 'f8de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c', 0, 30.00), -- Master Distributor
    (uuid_generate_v4(), 'f8de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c', 1, 15.00), -- Level 1 Distributor
    (uuid_generate_v4(), 'f8de3aeb-3d67-4d5b-9a35-d55c5c5c5c5c', 2, 5.00);  -- Level 2 Distributor
