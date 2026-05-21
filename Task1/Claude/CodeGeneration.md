I'll create a complete Food Management Web API in C# with all the SQL queries. Let me build this out fully.Created 8 files, ran a commandCreated 8 files, ran a commandNow let's create a visual API reference document:


VvisualizeVvisualize show_widgetNow let's copy all files to output:Ran a command, read a fileRan a command, read a fileHere's a complete breakdown of everything generated:

## Food Management Web API — C# + SQL Server

8 files delivered

FilePurposeSQL_Queries.sql-  Full DB schema, seed data, 13 stored procs, 2 views

Models/Models.cs - Domain entities: Category, Supplier, FoodItem, Inventory, Order, etc.

DTOs/DTOs.cs - Request/ response shapes with validation attributes

Data/FoodRepository.csDapper - based data access for all entities

Controllers/Controllers.cs5 - controllers with full REST endpoints

Program.csASP.NET - Core 8 minimal hosting setup with Swagger

appsettings.jsonConnection string config

FoodManagementAPI.csprojNuGet references (Dapper, SqlClient, Swashbuckle)

## API Endpoints

Dashboard — GET /api/dashboard — KPI summary (counts, revenue, alerts)

FoodItems — full CRUD + sub-resources:

GET /api/fooditems/low-stock — items below minimum threshold

GET /api/fooditems/expiring?days=7 — perishables expiring soon

PUT /api/fooditems/{id}/inventory — update stock details

POST /api/fooditems/{id}/stock-adjust — IN/OUT/WASTE/ADJUSTMENT

GET /api/fooditems/{id}/stock-movements — full audit trail

Orders — GET / POST / PATCH /{id}/status — status change to Delivered auto-deducts stock transactionally

Categories & Suppliers — full CRUD with soft delete

## Setup steps

Run SQL_Queries.sql against your SQL Server instance

Update the connection string in appsettings.json

dotnet restore then dotnet run

Swagger UI opens at https://localhost:{port}/
