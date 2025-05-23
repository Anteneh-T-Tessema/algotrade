# Trading Platform API Documentation

## Overview

This document outlines the API endpoints for the crypto trading automation platform. The API follows RESTful principles and uses JSON for request and response bodies. All endpoints require authentication unless otherwise specified.

## Base URL

```
https://api.cryptotrading-platform.com/v1
```

## Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer {JWT_TOKEN}
```

### Auth Endpoints

#### Register User

```
POST /auth/register
```

Request body:
```json
{
  "username": "trader1",
  "email": "trader@example.com",
  "password": "securePassword123!",
  "firstName": "John",
  "lastName": "Doe",
  "referralCode": "ABC123" // Optional
}
```

#### Login

```
POST /auth/login
```

Request body:
```json
{
  "email": "trader@example.com",
  "password": "securePassword123!",
  "twoFactorCode": "123456" // Optional, required if 2FA is enabled
}
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "rtEyJhbGciOiJIUzI1NiIsIn...",
  "expiresAt": "2023-06-01T12:00:00Z",
  "user": {
    "id": "uuid",
    "username": "trader1",
    "email": "trader@example.com",
    "roles": ["USER"],
    "lastLogin": "2023-05-01T10:30:00Z"
  }
}
```

#### Refresh Token

```
POST /auth/refresh-token
```

Request body:
```json
{
  "refreshToken": "rtEyJhbGciOiJIUzI1NiIsIn..."
}
```

#### Logout

```
POST /auth/logout
```

#### Reset Password Request

```
POST /auth/reset-password-request
```

Request body:
```json
{
  "email": "trader@example.com"
}
```

#### Reset Password

```
POST /auth/reset-password
```

Request body:
```json
{
  "token": "reset-token-from-email",
  "newPassword": "newSecurePassword456!"
}
```

#### Setup Two-Factor Authentication

```
POST /auth/2fa/setup
```

Response:
```json
{
  "qrCodeUrl": "data:image/png;base64...",
  "secret": "JBSWY3DPEHPK3PXP"
}
```

#### Verify Two-Factor Authentication

```
POST /auth/2fa/verify
```

Request body:
```json
{
  "code": "123456"
}
```

---

## User Management

These endpoints require ADMIN or MASTER_DISTRIBUTOR role.

#### List Users

```
GET /users
```

Query parameters:
- page (default: 1)
- limit (default: 20)
- role (filter by role)
- searchTerm (search by username or email)
- sortBy (field to sort by)
- sortDir (asc or desc)

#### Get User by ID

```
GET /users/{userId}
```

#### Create User

```
POST /users
```

Request body:
```json
{
  "username": "newtrader",
  "email": "newtrader@example.com",
  "password": "securePassword123!",
  "firstName": "Jane",
  "lastName": "Smith",
  "roles": ["USER"],
  "distributorId": "uuid-of-distributor" // Required for non-admin creators
}
```

#### Update User

```
PUT /users/{userId}
```

#### Delete User

```
DELETE /users/{userId}
```

#### Assign Role to User

```
POST /users/{userId}/roles
```

Request body:
```json
{
  "roleId": 2
}
```

#### Remove Role from User

```
DELETE /users/{userId}/roles/{roleId}
```

---

## Distributor Network

#### Get Distributor Hierarchy

```
GET /distributors/network
```

Response:
```json
{
  "id": "uuid-of-master-distributor",
  "username": "masterdist",
  "level": 0,
  "totalUsers": 125,
  "totalCommissions": 1250.75,
  "children": [
    {
      "id": "uuid-of-distributor-1",
      "username": "distributor1",
      "level": 1,
      "totalUsers": 75,
      "totalCommissions": 750.50,
      "children": [...]
    },
    {
      "id": "uuid-of-distributor-2",
      "username": "distributor2",
      "level": 1,
      "totalUsers": 50,
      "totalCommissions": 500.25,
      "children": [...]
    }
  ]
}
```

#### Get Downline Users

```
GET /distributors/{distributorId}/users
```

#### Add User to Distributor

```
POST /distributors/{distributorId}/users
```

Request body:
```json
{
  "userId": "uuid-of-user"
}
```

#### Remove User from Distributor

```
DELETE /distributors/{distributorId}/users/{userId}
```

---

## Commission Management

#### Get Commission Plan

```
GET /commissions/plans/{planId}
```

#### Create Commission Plan

```
POST /commissions/plans
```

Request body:
```json
{
  "planName": "Premium Distribution",
  "description": "Higher rates for premium distributors",
  "rates": [
    {
      "distributorLevel": 0,
      "commissionPercentage": 35.00
    },
    {
      "distributorLevel": 1,
      "commissionPercentage": 20.00
    },
    {
      "distributorLevel": 2,
      "commissionPercentage": 7.50
    }
  ]
}
```

#### Update Commission Plan

```
PUT /commissions/plans/{planId}
```

#### Delete Commission Plan

```
DELETE /commissions/plans/{planId}
```

#### Assign Commission Plan to User

```
POST /commissions/users/{userId}/plans
```

Request body:
```json
{
  "planId": "uuid-of-plan"
}
```

#### Get Commission Transactions

```
GET /commissions/transactions
```

Query parameters:
- userId
- fromDate
- toDate
- status (PENDING, COMPLETED, FAILED)
- page
- limit

#### Get Commission Statistics

```
GET /commissions/statistics
```

Query parameters:
- userId
- period (daily, weekly, monthly, yearly)
- fromDate
- toDate

---

## Trading Bot Management

#### Get Available Strategies

```
GET /trading/strategies
```

Response:
```json
{
  "strategies": [
    {
      "id": "dca",
      "name": "Dollar-Cost Averaging",
      "description": "Buys assets at regular intervals regardless of price",
      "parameters": [
        {
          "name": "interval_hours",
          "type": "integer",
          "default": 24,
          "description": "Hours between regular purchases"
        },
        {
          "name": "buy_amount",
          "type": "decimal",
          "default": 100,
          "description": "Amount in USD to buy at each interval"
        },
        // ... other parameters
      ],
      "marketTypes": ["normal", "trending", "volatile", "gappy"],
      "riskLevel": "low"
    },
    {
      "id": "grid",
      "name": "Grid Trading",
      "description": "Places a grid of buy and sell orders at fixed price intervals",
      // ... strategy details
    },
    // ... more strategies
  ]
}
```

#### Get User Strategies

```
GET /trading/user-strategies
```

#### Create User Strategy

```
POST /trading/user-strategies
```

Request body:
```json
{
  "strategyType": "dca",
  "symbol": "BTCUSDT",
  "parameters": {
    "interval_hours": 12,
    "buy_amount": 50,
    "dip_threshold_pct": 3.5,
    "dip_multiplier": 2.0,
    "use_rsi": true,
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_multiplier": 1.3,
    "take_profit_pct": 15.0
  },
  "isActive": true
}
```

#### Update User Strategy

```
PUT /trading/user-strategies/{strategyId}
```

#### Delete User Strategy

```
DELETE /trading/user-strategies/{strategyId}
```

#### Start Strategy

```
POST /trading/user-strategies/{strategyId}/start
```

#### Stop Strategy

```
POST /trading/user-strategies/{strategyId}/stop
```

#### Backtest Strategy

```
POST /trading/backtest
```

Request body:
```json
{
  "strategyType": "dca",
  "symbol": "BTCUSDT",
  "parameters": {
    // Strategy parameters
  },
  "startDate": "2023-01-01T00:00:00Z",
  "endDate": "2023-05-01T00:00:00Z",
  "initialCapital": 10000
}
```

Response:
```json
{
  "backtestId": "uuid",
  "summary": {
    "totalTrades": 42,
    "winRate": 68.5,
    "profitFactor": 2.3,
    "netProfit": 1523.75,
    "netProfitPercentage": 15.24,
    "maxDrawdown": 8.7,
    "sharpeRatio": 1.8
  },
  "equity": [
    // Time series data for equity curve
  ],
  "trades": [
    // List of individual trades
  ],
  "charts": [
    // URLs to chart images
  ]
}
```

---

## Exchange Connection

#### List Connected Exchanges

```
GET /exchanges
```

#### Connect Exchange API

```
POST /exchanges
```

Request body:
```json
{
  "exchangeName": "binance",
  "apiKey": "your-api-key",
  "apiSecret": "your-api-secret",
  "label": "Binance Main Account",
  "permissions": ["READ", "TRADE"]
}
```

#### Update Exchange API

```
PUT /exchanges/{exchangeId}
```

#### Delete Exchange API

```
DELETE /exchanges/{exchangeId}
```

#### Test Exchange Connection

```
POST /exchanges/{exchangeId}/test
```

#### Get Exchange Balance

```
GET /exchanges/{exchangeId}/balance
```

---

## Trading Activity

#### Get Trading History

```
GET /trading/history
```

Query parameters:
- exchangeId
- symbol
- strategyId
- startDate
- endDate
- side (BUY, SELL)
- page
- limit

#### Get Open Positions

```
GET /trading/positions
```

#### Get Trading Statistics

```
GET /trading/statistics
```

Query parameters:
- period (daily, weekly, monthly)
- startDate
- endDate
- strategyId
- symbol

---

## Notifications

#### Get Notifications

```
GET /notifications
```

Query parameters:
- read (true or false)
- type (ALERT, INFO, SUCCESS, ERROR)
- page
- limit

#### Mark Notification as Read

```
PUT /notifications/{notificationId}/read
```

#### Delete Notification

```
DELETE /notifications/{notificationId}
```

#### Get Notification Settings

```
GET /notifications/settings
```

#### Update Notification Settings

```
PUT /notifications/settings
```

Request body:
```json
{
  "email": {
    "tradeExecuted": true,
    "takeProfitTriggered": true,
    "stopLossTriggered": true,
    "commissionReceived": true
  },
  "push": {
    "tradeExecuted": true,
    "takeProfitTriggered": true,
    "stopLossTriggered": true,
    "commissionReceived": true
  },
  "telegram": {
    "enabled": true,
    "chatId": "12345678",
    "tradeExecuted": true,
    "takeProfitTriggered": true,
    "stopLossTriggered": true,
    "commissionReceived": false
  }
}
```

---

## Wallet Management

#### Get User Wallets

```
GET /wallets
```

#### Get Wallet Transactions

```
GET /wallets/{walletId}/transactions
```

#### Request Withdrawal

```
POST /wallets/{walletId}/withdrawals
```

Request body:
```json
{
  "amount": 100.00,
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "network": "ETH",
  "description": "Monthly commission withdrawal"
}
```

#### Get Withdrawal Status

```
GET /wallets/withdrawals/{withdrawalId}
```

---

## Admin Dashboard

#### Get System Statistics

```
GET /admin/statistics
```

Response:
```json
{
  "users": {
    "total": 1250,
    "active": 875,
    "newToday": 15,
    "growthRate": 2.5
  },
  "trades": {
    "total": 12500,
    "today": 750,
    "volume": 1250000,
    "volumeToday": 75000
  },
  "commissions": {
    "totalGenerated": 25000.50,
    "todayGenerated": 1250.25,
    "pending": 2500.75,
    "withdrawn": 22500.00
  },
  "performance": {
    "avgWinRate": 65.5,
    "avgProfitPercentage": 12.5,
    "bestStrategy": "GridTrading",
    "bestMarketType": "trending"
  }
}
```

#### Get Audit Logs

```
GET /admin/audit-logs
```

Query parameters:
- userId
- action
- entityType
- fromDate
- toDate
- page
- limit

#### Get System Settings

```
GET /admin/settings
```

#### Update System Settings

```
PUT /admin/settings
```

Request body:
```json
{
  "settings": [
    {
      "key": "MIN_DEPOSIT_AMOUNT",
      "value": "50"
    },
    {
      "key": "MAX_WITHDRAWAL_AMOUNT",
      "value": "10000"
    },
    {
      "key": "DEFAULT_COMMISSION_PLAN_ID",
      "value": "uuid-of-plan"
    }
  ]
}
```

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "The provided parameters are invalid",
    "details": {
      "field": "email",
      "issue": "Must be a valid email address"
    }
  }
}
```

Common error codes:
- AUTHENTICATION_FAILED
- AUTHORIZATION_FAILED
- RESOURCE_NOT_FOUND
- INVALID_PARAMETERS
- RATE_LIMIT_EXCEEDED
- EXCHANGE_ERROR
- INTERNAL_SERVER_ERROR

---

## Rate Limiting

API requests are subject to rate limiting:
- Authentication endpoints: 10 requests per minute
- Trading endpoints: 60 requests per minute
- Admin endpoints: 120 requests per minute

Rate limit headers included in all responses:
- X-RateLimit-Limit: Maximum requests per window
- X-RateLimit-Remaining: Remaining requests in current window
- X-RateLimit-Reset: Timestamp when the rate limit resets
