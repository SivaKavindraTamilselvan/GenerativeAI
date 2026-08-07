using Microsoft.AspNetCore.Mvc;
using Dapper;
using System.Data;

[ApiController]
[Route("api/[controller]")]
public class FoodController : ControllerBase
{
    // We now inject the connection interface
    private readonly IDbConnection _db;

    public FoodController(IDbConnection db)
    {
        _db = db;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        // No need to create a new connection, just use _db
        var sql = "SELECT id as Id, name as Name, category as Category, price as Price, expiry_date as ExpiryDate FROM food_items";
        var items = await _db.QueryAsync<FoodItem>(sql);
        return Ok(items);
    }

    [HttpPost]
    public async Task<IActionResult> Create(FoodItem item)
    {
        var sql = @"INSERT INTO food_items (name, category, price, expiry_date) 
                    VALUES (@Name, @Category, @Price, @ExpiryDate)";
        
        // Dapper handles the mapping from the 'item' object properties to the SQL @parameters
        await _db.ExecuteAsync(sql, item);
        return Ok("Food item added successfully.");
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, FoodItem item)
    {
        var sql = @"UPDATE food_items 
                    SET name = @Name, 
                        category = @Category, 
                        price = @Price, 
                        expiry_date = @ExpiryDate 
                    WHERE id = @id";
        
        // Pass an anonymous object that includes the 'id' from the route and properties from 'item'
        await _db.ExecuteAsync(sql, new { 
            id, 
            item.Name, 
            item.Category, 
            item.Price, 
            item.ExpiryDate 
        });
        
        return Ok("Updated successfully.");
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var sql = "DELETE FROM food_items WHERE id = @id";
        await _db.ExecuteAsync(sql, new { id });
        return Ok("Deleted successfully.");
    }
}