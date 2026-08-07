// ============================================================
//  Program.cs — ASP.NET Core 8 with Npgsql (PostgreSQL)
// ============================================================
using FoodManagementAPI.Data;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.OpenApi.Models;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);

// ── Services ──────────────────────────────────────────────
builder.Services.AddControllers();

// Register Npgsql data source (connection pooling, best practice for PostgreSQL)
var connString = builder.Configuration.GetConnectionString("DefaultConnection")!;
builder.Services.AddSingleton(new NpgsqlDataSourceBuilder(connString).Build());
builder.Services.AddSingleton<AppDbContext>();
builder.Services.AddScoped<FoodRepository>();

// CORS
builder.Services.AddCors(options =>
    options.AddPolicy("AllowAll", policy =>
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title       = "Food Management API",
        Version     = "v1",
        Description = "REST API backed by PostgreSQL — food items, inventory, categories, suppliers and orders.",
        Contact     = new OpenApiContact { Name = "Dev Team", Email = "dev@foodmgmt.local" }
    });
    var xmlFile = $"{System.Reflection.Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = System.IO.Path.Combine(System.AppContext.BaseDirectory, xmlFile);
    if (System.IO.File.Exists(xmlPath)) c.IncludeXmlComments(xmlPath);
});

// ── App Pipeline ──────────────────────────────────────────
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "Food Management API v1");
        c.RoutePrefix = string.Empty;
    });
}

app.UseCors("AllowAll");
app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();
app.Run();