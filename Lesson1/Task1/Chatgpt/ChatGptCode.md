# 🍔 Food Management Web API

A complete **ASP.NET Core Web API** for **Food Management** using:

- ASP.NET Core Web API
- Entity Framework Core
- PostgreSQL
- Repository Pattern
- DTO Pattern
- Service Layer
- Swagger

---

# Project Setup

## Create Project

```bash
dotnet new webapi -n FoodManagementAPI
cd FoodManagementAPI

dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL
dotnet add package Microsoft.EntityFrameworkCore.Design
```

---

# Database Setup

## Create Database

```sql
CREATE DATABASE food_management;
```

---

## Categories Table

```sql
CREATE TABLE "Categories" (
    "CategoryId" SERIAL PRIMARY KEY,
    "CategoryName" VARCHAR(100) NOT NULL UNIQUE
);
```

---

## Foods Table

```sql
CREATE TABLE "Foods" (
    "FoodId" SERIAL PRIMARY KEY,
    "FoodName" VARCHAR(150) NOT NULL,
    "Price" DECIMAL(10,2) NOT NULL CHECK ("Price" > 0),
    "Quantity" INT NOT NULL CHECK ("Quantity" >= 0),
    "CategoryId" INT NOT NULL,
    "IsAvailable" BOOLEAN DEFAULT TRUE,
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_food_category
    FOREIGN KEY ("CategoryId")
    REFERENCES "Categories"("CategoryId")
    ON DELETE CASCADE
);
```

---

# Sample Data

```sql
INSERT INTO "Categories" ("CategoryName")
VALUES
('Breakfast'),
('Lunch'),
('Dinner'),
('Snacks'),
('Drinks');

INSERT INTO "Foods"
("FoodName","Price","Quantity","CategoryId","IsAvailable")
VALUES
('Idly',30,50,1,TRUE),
('Dosa',50,40,1,TRUE),
('Chicken Biryani',180,25,2,TRUE),
('Tea',15,100,5,TRUE);
```

---

# Connection Configuration

## appsettings.json

```json
{
  "ConnectionStrings": {
    "DefaultConnection":
"Host=localhost;Port=5432;Database=food_management;Username=postgres;Password=your_password"
  }
}
```

---

# Project Structure

```text
FoodManagementAPI
│
├── Controllers
│     └── FoodsController.cs
│
├── Services
│     ├── IFoodService.cs
│     └── FoodService.cs
│
├── Repositories
│     ├── IFoodRepository.cs
│     └── FoodRepository.cs
│
├── Models
│     ├── Food.cs
│     └── Category.cs
│
├── DTOs
│     ├── FoodCreateDto.cs
│     └── FoodResponseDto.cs
│
├── Data
│     └── FoodDbContext.cs
│
├── Program.cs
├── appsettings.json
└── README.md
```

---

# Models

## Category

```csharp
public class Category
{
    public int CategoryId { get; set; }

    public string CategoryName { get; set; }

    public ICollection<Food>? Foods { get; set; }
}
```

---

## Food

```csharp
public class Food
{
    public int FoodId { get; set; }

    public string FoodName { get; set; }

    public decimal Price { get; set; }

    public int Quantity { get; set; }

    public bool IsAvailable { get; set; }

    public DateTime CreatedAt { get; set; }

    public int CategoryId { get; set; }

    public Category? Category { get; set; }
}
```

---

# Features

✅ Add Food

✅ Update Food

✅ Delete Food

✅ Get All Foods

✅ Get Food By ID

✅ Category Mapping

✅ PostgreSQL Integration

✅ Swagger Documentation

---

# API Endpoints

| Method | Endpoint |
|---------|----------|
| GET | /api/Foods |
| GET | /api/Foods/{id} |
| POST | /api/Foods |
| PUT | /api/Foods/{id} |
| DELETE | /api/Foods/{id} |

---

# Useful SQL Queries

## Get All Foods

```sql
SELECT
f."FoodId",
f."FoodName",
f."Price",
f."Quantity",
c."CategoryName"
FROM "Foods" f
JOIN "Categories" c
ON f."CategoryId"=c."CategoryId";
```

---

## Get Available Foods

```sql
SELECT *
FROM "Foods"
WHERE "Quantity">0
AND "IsAvailable"=TRUE;
```

---

## Search Food

```sql
SELECT *
FROM "Foods"
WHERE "FoodName"
ILIKE '%dosa%';
```

---

## Filter By Category

```sql
SELECT
f."FoodName",
f."Price",
c."CategoryName"
FROM "Foods" f
JOIN "Categories" c
ON f."CategoryId"=c."CategoryId"
WHERE c."CategoryName"='Breakfast';
```

---

# Migration

```bash
dotnet ef migrations add InitialCreate

dotnet ef database update

dotnet run
```

---

# Swagger

```text
https://localhost:xxxx/swagger
```

---

# Architecture

```text
Controller
↓
Service Layer
↓
Repository Layer
↓
Entity Framework Core
↓
PostgreSQL
```

---
