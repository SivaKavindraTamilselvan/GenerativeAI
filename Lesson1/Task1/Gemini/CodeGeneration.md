# To use PostgreSQL with a .NET Web API, you will use the Npgsql driver.

Here is the complete setup from scratch.

## 1. Database Schema (PostgreSQL)

Run this in your PostgreSQL query tool (like pgAdmin or psql):

```sql
CREATE DATABASE food_management;

\c food_management;

CREATE TABLE food_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(18, 2),
    expiry_date TIMESTAMP
);
```

---

## 2. Setup the Project

Create a new Web API project:

```bash
dotnet new webapi -n FoodManagementApi
```

Install the necessary NuGet packages:

```bash
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL

dotnet add package Dapper
```

---

## 3. The Model

Create `Models/FoodItem.cs`.

Note that PostgreSQL uses `snake_case` by default, but C# uses `PascalCase`.

```csharp
public class FoodItem
{
    public int Id { get; set; }

    public string Name { get; set; }

    public string Category { get; set; }

    public decimal Price { get; set; }

    public DateTime ExpiryDate { get; set; }
}
```

---

## 4. Configuration (`appsettings.json`)

Add your connection string here.

Replace with your actual database credentials.

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Database=food_management;Username=postgres;Password=yourpassword"
  }
}
```

---

## 5. The Controller (Dapper + PostgreSQL)

This controller handles the connection and the raw SQL queries.

```csharp
using Microsoft.AspNetCore.Mvc;
using Npgsql;
using Dapper;

[ApiController]
[Route("api/[controller]")]
public class FoodController : ControllerBase
{
    private readonly string _connectionString;

    public FoodController(IConfiguration configuration)
    {
        _connectionString =
            configuration.GetConnectionString("DefaultConnection");
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        using var connection =
            new NpgsqlConnection(_connectionString);

        var sql =
            @"SELECT
                id as Id,
                name as Name,
                category as Category,
                price as Price,
                expiry_date as ExpiryDate
              FROM food_items";

        var items =
            await connection.QueryAsync<FoodItem>(sql);

        return Ok(items);
    }

    [HttpPost]
    public async Task<IActionResult> Create(FoodItem item)
    {
        using var connection =
            new NpgsqlConnection(_connectionString);

        var sql =
            @"INSERT INTO food_items
                (name, category, price, expiry_date)
              VALUES
                (@Name, @Category, @Price, @ExpiryDate)";

        await connection.ExecuteAsync(sql, item);

        return Ok("Food item added successfully.");
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(
        int id,
        FoodItem item)
    {
        using var connection =
            new NpgsqlConnection(_connectionString);

        var sql =
            @"UPDATE food_items
              SET
                name=@Name,
                category=@Category,
                price=@Price,
                expiry_date=@ExpiryDate
              WHERE id=@id";

        await connection.ExecuteAsync(
            sql,
            new
            {
                id,
                item.Name,
                item.Category,
                item.Price,
                item.ExpiryDate
            });

        return Ok("Updated.");
    }
}
```

---

## 6. Summary of PostgreSQL Queries

When writing PostgreSQL queries in your code, keep these differences from SQL Server in mind:

| Operation | PostgreSQL Query |
|----------|------------------|
| Insert | `INSERT INTO food_items (name, category...) VALUES (@Name, @Category...)` |
| Select | `SELECT id as "Id", name as "Name" ... FROM food_items` |
| Update | `UPDATE food_items SET name=@Name WHERE id=@id` |
| Delete | `DELETE FROM food_items WHERE id=@id` |

---

## Key Tips for PostgreSQL with .NET

- **Case Sensitivity:** PostgreSQL is case-sensitive regarding column names if they were created with quotes. It is best practice to use all lowercase column names (`expiry_date` instead of `ExpiryDate`).

- **Aliasing:** In your `SELECT` queries, use aliases (`SELECT name as Name`) to map PostgreSQL `snake_case` columns to your C# `PascalCase` model properties.

- **Npgsql:** Always use `NpgsqlConnection` instead of `SqlConnection` for PostgreSQL.