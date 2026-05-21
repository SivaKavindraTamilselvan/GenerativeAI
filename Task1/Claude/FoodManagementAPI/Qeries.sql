-- ============================================================
--   FOOD MANAGEMENT SYSTEM — PostgreSQL
--   Compatible with: PostgreSQL 13+
-- ============================================================

-- ─────────────────────────────────────────────
-- 1. SCHEMA / EXTENSIONS
-- ─────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- for gen_random_uuid() if needed

-- ─────────────────────────────────────────────
-- 2. TABLE DEFINITIONS
-- ─────────────────────────────────────────────

CREATE TABLE categories (
    category_id   SERIAL       PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    description   TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE suppliers (
    supplier_id   SERIAL       PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    contact_name  VARCHAR(100),
    email         VARCHAR(200),
    phone         VARCHAR(20),
    address       TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE food_items (
    food_item_id      SERIAL          PRIMARY KEY,
    name              VARCHAR(150)    NOT NULL,
    description       TEXT,
    category_id       INT             NOT NULL REFERENCES categories(category_id),
    supplier_id       INT             REFERENCES suppliers(supplier_id),
    unit              VARCHAR(50)     NOT NULL,       -- kg, litre, piece, box …
    price_per_unit    NUMERIC(10,2)   NOT NULL,
    calories_per_unit INT,
    is_perishable     BOOLEAN         NOT NULL DEFAULT FALSE,
    image_url         VARCHAR(500),
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE
);

CREATE TABLE inventory (
    inventory_id        SERIAL          PRIMARY KEY,
    food_item_id        INT             NOT NULL UNIQUE REFERENCES food_items(food_item_id),
    quantity_available  NUMERIC(10,2)   NOT NULL DEFAULT 0,
    minimum_threshold   NUMERIC(10,2)   NOT NULL DEFAULT 0,
    expiry_date         DATE,
    storage_location    VARCHAR(100),
    last_restocked_at   TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
    order_id      SERIAL          PRIMARY KEY,
    order_number  VARCHAR(50)     NOT NULL UNIQUE,
    order_date    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    status        VARCHAR(50)     NOT NULL DEFAULT 'Pending'
                  CHECK (status IN ('Pending','Confirmed','Delivered','Cancelled')),
    total_amount  NUMERIC(12,2)   NOT NULL DEFAULT 0,
    notes         TEXT,
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    order_item_id SERIAL          PRIMARY KEY,
    order_id      INT             NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    food_item_id  INT             NOT NULL REFERENCES food_items(food_item_id),
    quantity      NUMERIC(10,2)   NOT NULL,
    unit_price    NUMERIC(10,2)   NOT NULL,
    total_price   NUMERIC(12,2)   GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE stock_movements (
    movement_id   SERIAL          PRIMARY KEY,
    food_item_id  INT             NOT NULL REFERENCES food_items(food_item_id),
    movement_type VARCHAR(20)     NOT NULL
                  CHECK (movement_type IN ('IN','OUT','ADJUSTMENT','WASTE')),
    quantity      NUMERIC(10,2)   NOT NULL,
    reason        TEXT,
    reference_id  INT,
    moved_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_by    VARCHAR(100)
);

-- ─────────────────────────────────────────────
-- 3. INDEXES
-- ─────────────────────────────────────────────
CREATE INDEX idx_food_items_category   ON food_items(category_id);
CREATE INDEX idx_food_items_supplier   ON food_items(supplier_id);
CREATE INDEX idx_inventory_food_item   ON inventory(food_item_id);
CREATE INDEX idx_order_items_order     ON order_items(order_id);
CREATE INDEX idx_order_items_food      ON order_items(food_item_id);
CREATE INDEX idx_stock_movements_food  ON stock_movements(food_item_id);
CREATE INDEX idx_orders_status         ON orders(status);

-- ─────────────────────────────────────────────
-- 4. AUTO-UPDATE updated_at TRIGGER
-- ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_food_items_updated
    BEFORE UPDATE ON food_items
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_categories_updated
    BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_inventory_updated
    BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_orders_updated
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- ─────────────────────────────────────────────
-- 5. SEED DATA
-- ─────────────────────────────────────────────
INSERT INTO categories (name, description) VALUES
('Vegetables',  'Fresh and frozen vegetables'),
('Fruits',      'Fresh seasonal fruits'),
('Dairy',       'Milk, cheese, yoghurt and butter'),
('Grains',      'Rice, wheat, flour and cereals'),
('Beverages',   'Juices, water and soft drinks'),
('Meat & Fish', 'Fresh and frozen proteins');

INSERT INTO suppliers (name, contact_name, email, phone) VALUES
('FreshFarm Co.',    'Ravi Kumar',  'ravi@freshfarm.com',    '+91-9876543210'),
('Organic World',   'Priya Nair',  'priya@organicworld.in', '+91-9123456789'),
('Metro Wholesale', 'Arjun Mehta', 'arjun@metro.in',        '+91-9012345678');

INSERT INTO food_items
    (name, description, category_id, supplier_id, unit, price_per_unit, calories_per_unit, is_perishable)
VALUES
('Tomato',      'Fresh red tomatoes',      1, 1, 'kg',    40.00,  18, TRUE),
('Spinach',     'Fresh spinach leaves',    1, 1, 'kg',    30.00,  23, TRUE),
('Banana',      'Yellow ripe bananas',     2, 2, 'dozen', 50.00,  89, TRUE),
('Apple',       'Kashmiri red apples',     2, 2, 'kg',   150.00,  52, TRUE),
('Whole Milk',  'Full-fat pasteurised',    3, 3, 'litre', 60.00,  61, TRUE),
('Basmati Rice','Premium aged basmati',    4, 3, 'kg',    90.00, 130, FALSE),
('Wheat Flour', 'Whole wheat atta',        4, 3, 'kg',    45.00, 340, FALSE),
('Orange Juice','100% fresh squeezed',     5, 2, 'litre', 80.00,  45, TRUE),
('Chicken',     'Fresh boneless breast',   6, 1, 'kg',   220.00, 165, TRUE),
('Salmon',      'Atlantic salmon fillet',  6, 3, 'kg',   650.00, 208, TRUE);

INSERT INTO inventory
    (food_item_id, quantity_available, minimum_threshold, expiry_date, storage_location)
VALUES
(1,  50, 10, NOW() + INTERVAL '5 days',  'Fridge-A1'),
(2,  30,  5, NOW() + INTERVAL '3 days',  'Fridge-A2'),
(3,  20,  5, NOW() + INTERVAL '7 days',  'Shelf-B1'),
(4,  40, 10, NOW() + INTERVAL '14 days', 'Shelf-B2'),
(5,  15,  5, NOW() + INTERVAL '3 days',  'Fridge-C1'),
(6, 100, 20, NULL,                        'StoreRoom-D1'),
(7, 200, 50, NULL,                        'StoreRoom-D2'),
(8,  25,  5, NOW() + INTERVAL '7 days',  'Fridge-A3'),
(9,  30, 10, NOW() + INTERVAL '2 days',  'Fridge-C2'),
(10, 15,  5, NOW() + INTERVAL '2 days',  'Fridge-C3');

-- ─────────────────────────────────────────────
-- 6. POSTGRESQL FUNCTIONS (replaces SQL Server stored procs)
-- ─────────────────────────────────────────────

-- ── 6a. Get all food items with inventory ──
CREATE OR REPLACE FUNCTION fn_get_all_food_items()
RETURNS TABLE (
    food_item_id       INT,
    name               VARCHAR,
    description        TEXT,
    category_id        INT,
    category_name      VARCHAR,
    supplier_id        INT,
    supplier_name      VARCHAR,
    unit               VARCHAR,
    price_per_unit     NUMERIC,
    calories_per_unit  INT,
    is_perishable      BOOLEAN,
    image_url          VARCHAR,
    quantity_available NUMERIC,
    minimum_threshold  NUMERIC,
    expiry_date        DATE,
    storage_location   VARCHAR,
    is_low_stock       BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.food_item_id, f.name, f.description,
        c.category_id, c.name AS category_name,
        s.supplier_id, s.name AS supplier_name,
        f.unit, f.price_per_unit, f.calories_per_unit,
        f.is_perishable, f.image_url,
        i.quantity_available, i.minimum_threshold,
        i.expiry_date, i.storage_location,
        (i.quantity_available <= i.minimum_threshold) AS is_low_stock
    FROM  food_items f
    JOIN  categories c ON c.category_id = f.category_id
    LEFT JOIN suppliers s ON s.supplier_id = f.supplier_id
    LEFT JOIN inventory i ON i.food_item_id = f.food_item_id
    WHERE f.is_active = TRUE
    ORDER BY f.name;
END;
$$ LANGUAGE plpgsql;

-- ── 6b. Get food item by ID ──
CREATE OR REPLACE FUNCTION fn_get_food_item_by_id(p_food_item_id INT)
RETURNS TABLE (
    food_item_id       INT,
    name               VARCHAR,
    description        TEXT,
    category_id        INT,
    category_name      VARCHAR,
    supplier_id        INT,
    supplier_name      VARCHAR,
    unit               VARCHAR,
    price_per_unit     NUMERIC,
    calories_per_unit  INT,
    is_perishable      BOOLEAN,
    image_url          VARCHAR,
    quantity_available NUMERIC,
    minimum_threshold  NUMERIC,
    expiry_date        DATE,
    storage_location   VARCHAR,
    last_restocked_at  TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.food_item_id, f.name, f.description,
        c.category_id, c.name AS category_name,
        s.supplier_id, s.name AS supplier_name,
        f.unit, f.price_per_unit, f.calories_per_unit,
        f.is_perishable, f.image_url,
        i.quantity_available, i.minimum_threshold,
        i.expiry_date, i.storage_location, i.last_restocked_at
    FROM  food_items f
    JOIN  categories c ON c.category_id = f.category_id
    LEFT JOIN suppliers s ON s.supplier_id = f.supplier_id
    LEFT JOIN inventory i ON i.food_item_id = f.food_item_id
    WHERE f.food_item_id = p_food_item_id AND f.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- ── 6c. Create food item ──
CREATE OR REPLACE FUNCTION fn_create_food_item(
    p_name              VARCHAR,
    p_description       TEXT,
    p_category_id       INT,
    p_supplier_id       INT,
    p_unit              VARCHAR,
    p_price_per_unit    NUMERIC,
    p_calories_per_unit INT,
    p_is_perishable     BOOLEAN,
    p_image_url         VARCHAR
) RETURNS INT AS $$
DECLARE
    v_new_id INT;
BEGIN
    INSERT INTO food_items
        (name, description, category_id, supplier_id, unit, price_per_unit, calories_per_unit, is_perishable, image_url)
    VALUES
        (p_name, p_description, p_category_id, p_supplier_id, p_unit, p_price_per_unit, p_calories_per_unit, p_is_perishable, p_image_url)
    RETURNING food_item_id INTO v_new_id;

    -- Auto-create blank inventory record
    INSERT INTO inventory (food_item_id, quantity_available, minimum_threshold)
    VALUES (v_new_id, 0, 0);

    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;

-- ── 6d. Update food item ──
CREATE OR REPLACE FUNCTION fn_update_food_item(
    p_food_item_id      INT,
    p_name              VARCHAR,
    p_description       TEXT,
    p_category_id       INT,
    p_supplier_id       INT,
    p_unit              VARCHAR,
    p_price_per_unit    NUMERIC,
    p_calories_per_unit INT,
    p_is_perishable     BOOLEAN,
    p_image_url         VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE food_items SET
        name              = p_name,
        description       = p_description,
        category_id       = p_category_id,
        supplier_id       = p_supplier_id,
        unit              = p_unit,
        price_per_unit    = p_price_per_unit,
        calories_per_unit = p_calories_per_unit,
        is_perishable     = p_is_perishable,
        image_url         = p_image_url
        -- updated_at handled by trigger
    WHERE food_item_id = p_food_item_id;
END;
$$ LANGUAGE plpgsql;

-- ── 6e. Soft-delete food item ──
CREATE OR REPLACE FUNCTION fn_delete_food_item(p_food_item_id INT)
RETURNS VOID AS $$
BEGIN
    UPDATE food_items SET is_active = FALSE
    WHERE food_item_id = p_food_item_id;
END;
$$ LANGUAGE plpgsql;

-- ── 6f. Update inventory ──
CREATE OR REPLACE FUNCTION fn_update_inventory(
    p_food_item_id       INT,
    p_quantity_available NUMERIC,
    p_minimum_threshold  NUMERIC,
    p_expiry_date        DATE,
    p_storage_location   VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE inventory SET
        quantity_available = p_quantity_available,
        minimum_threshold  = p_minimum_threshold,
        expiry_date        = p_expiry_date,
        storage_location   = p_storage_location,
        last_restocked_at  = NOW()
        -- updated_at by trigger
    WHERE food_item_id = p_food_item_id;
END;
$$ LANGUAGE plpgsql;

-- ── 6g. Adjust stock (IN / OUT / WASTE / ADJUSTMENT) ──
CREATE OR REPLACE FUNCTION fn_adjust_stock(
    p_food_item_id  INT,
    p_movement_type VARCHAR,
    p_quantity      NUMERIC,
    p_reason        TEXT,
    p_reference_id  INT,
    p_created_by    VARCHAR
) RETURNS VOID AS $$
BEGIN
    IF p_movement_type = 'IN' THEN
        UPDATE inventory SET
            quantity_available = quantity_available + p_quantity,
            last_restocked_at  = NOW()
        WHERE food_item_id = p_food_item_id;
    ELSE
        UPDATE inventory SET
            quantity_available = quantity_available - p_quantity
        WHERE food_item_id = p_food_item_id;
    END IF;

    INSERT INTO stock_movements
        (food_item_id, movement_type, quantity, reason, reference_id, created_by)
    VALUES
        (p_food_item_id, p_movement_type, p_quantity, p_reason, p_reference_id, p_created_by);
END;
$$ LANGUAGE plpgsql;

-- ── 6h. Create order (with auto order number) ──
CREATE OR REPLACE FUNCTION fn_create_order(p_notes TEXT)
RETURNS TABLE(new_order_id INT, order_number VARCHAR) AS $$
DECLARE
    v_order_id     INT;
    v_order_number VARCHAR;
BEGIN
    v_order_number := 'ORD-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('orders_order_id_seq')::TEXT, 4, '0');

    INSERT INTO orders (order_number, notes)
    VALUES (v_order_number, p_notes)
    RETURNING order_id INTO v_order_id;

    RETURN QUERY SELECT v_order_id, v_order_number;
END;
$$ LANGUAGE plpgsql;

-- ── 6i. Add item to order ──
CREATE OR REPLACE FUNCTION fn_add_order_item(
    p_order_id     INT,
    p_food_item_id INT,
    p_quantity     NUMERIC
) RETURNS VOID AS $$
DECLARE
    v_unit_price NUMERIC;
BEGIN
    SELECT price_per_unit INTO v_unit_price
    FROM food_items WHERE food_item_id = p_food_item_id;

    INSERT INTO order_items (order_id, food_item_id, quantity, unit_price)
    VALUES (p_order_id, p_food_item_id, p_quantity, v_unit_price);

    -- Recalculate order total
    UPDATE orders SET
        total_amount = (SELECT COALESCE(SUM(total_price), 0) FROM order_items WHERE order_id = p_order_id)
    WHERE order_id = p_order_id;
END;
$$ LANGUAGE plpgsql;

-- ── 6j. Update order status (deducts stock on Delivered) ──
CREATE OR REPLACE FUNCTION fn_update_order_status(
    p_order_id INT,
    p_status   VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE orders SET status = p_status
    WHERE order_id = p_order_id;

    IF p_status = 'Delivered' THEN
        -- Insert stock-out movements for all line items
        INSERT INTO stock_movements (food_item_id, movement_type, quantity, reason, reference_id)
        SELECT food_item_id, 'OUT', quantity, 'Order Delivered', p_order_id
        FROM   order_items WHERE order_id = p_order_id;

        -- Deduct from inventory
        UPDATE inventory i
        SET    quantity_available = i.quantity_available - oi.quantity
        FROM   order_items oi
        WHERE  oi.order_id = p_order_id
          AND  oi.food_item_id = i.food_item_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ── 6k. Get low-stock items ──
CREATE OR REPLACE FUNCTION fn_get_low_stock_items()
RETURNS TABLE (
    food_item_id       INT,
    name               VARCHAR,
    unit               VARCHAR,
    quantity_available NUMERIC,
    minimum_threshold  NUMERIC,
    expiry_date        DATE,
    storage_location   VARCHAR,
    category_name      VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.food_item_id, f.name, f.unit,
        i.quantity_available, i.minimum_threshold,
        i.expiry_date, i.storage_location,
        c.name AS category_name
    FROM  inventory i
    JOIN  food_items f  ON f.food_item_id = i.food_item_id
    JOIN  categories c  ON c.category_id  = f.category_id
    WHERE i.quantity_available <= i.minimum_threshold
      AND f.is_active = TRUE
    ORDER BY i.quantity_available ASC;
END;
$$ LANGUAGE plpgsql;

-- ── 6l. Get expiring items within N days ──
CREATE OR REPLACE FUNCTION fn_get_expiring_items(p_days_ahead INT DEFAULT 7)
RETURNS TABLE (
    food_item_id       INT,
    name               VARCHAR,
    unit               VARCHAR,
    quantity_available NUMERIC,
    expiry_date        DATE,
    storage_location   VARCHAR,
    days_until_expiry  INT,
    category_name      VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.food_item_id, f.name, f.unit,
        i.quantity_available,
        i.expiry_date, i.storage_location,
        (i.expiry_date - CURRENT_DATE)::INT AS days_until_expiry,
        c.name AS category_name
    FROM  inventory i
    JOIN  food_items f ON f.food_item_id = i.food_item_id
    JOIN  categories c ON c.category_id  = f.category_id
    WHERE i.expiry_date IS NOT NULL
      AND i.expiry_date <= CURRENT_DATE + p_days_ahead
      AND f.is_active = TRUE
    ORDER BY i.expiry_date ASC;
END;
$$ LANGUAGE plpgsql;

-- ── 6m. Dashboard summary ──
CREATE OR REPLACE FUNCTION fn_get_dashboard_summary()
RETURNS TABLE (
    total_food_items  BIGINT,
    total_categories  BIGINT,
    total_suppliers   BIGINT,
    pending_orders    BIGINT,
    today_orders      BIGINT,
    total_revenue     NUMERIC,
    low_stock_count   BIGINT,
    expiring_count    BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)               FROM food_items  WHERE is_active = TRUE),
        (SELECT COUNT(*)               FROM categories  WHERE is_active = TRUE),
        (SELECT COUNT(*)               FROM suppliers   WHERE is_active = TRUE),
        (SELECT COUNT(*)               FROM orders      WHERE status = 'Pending'),
        (SELECT COUNT(*)               FROM orders      WHERE order_date::DATE = CURRENT_DATE),
        (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'Delivered'),
        (SELECT COUNT(*)               FROM inventory   WHERE quantity_available <= minimum_threshold),
        (SELECT COUNT(*)               FROM inventory   WHERE expiry_date IS NOT NULL
                                                          AND expiry_date <= CURRENT_DATE + 7);
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────────
-- 7. VIEWS
-- ─────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_food_inventory AS
SELECT
    f.food_item_id,
    f.name          AS food_name,
    f.unit,
    f.price_per_unit,
    c.name          AS category,
    s.name          AS supplier,
    i.quantity_available,
    i.minimum_threshold,
    i.expiry_date,
    i.storage_location,
    CASE
        WHEN i.quantity_available <= i.minimum_threshold          THEN 'Low Stock'
        WHEN i.expiry_date <= CURRENT_DATE + 3                    THEN 'Expiring Soon'
        ELSE 'OK'
    END AS stock_status
FROM  food_items f
JOIN  categories c ON c.category_id  = f.category_id
LEFT JOIN suppliers  s ON s.supplier_id  = f.supplier_id
LEFT JOIN inventory  i ON i.food_item_id = f.food_item_id
WHERE f.is_active = TRUE;


CREATE OR REPLACE VIEW vw_order_summary AS
SELECT
    o.order_id,
    o.order_number,
    o.order_date,
    o.status,
    o.total_amount,
    o.notes,
    COUNT(oi.order_item_id) AS item_count,
    COALESCE(SUM(oi.quantity), 0) AS total_quantity
FROM  orders o
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_number, o.order_date, o.status, o.total_amount, o.notes;


-- ─────────────────────────────────────────────
-- 8. USEFUL STANDALONE QUERIES
-- ─────────────────────────────────────────────

-- All food items with stock status
-- SELECT * FROM vw_food_inventory;

-- Low stock alert
-- SELECT * FROM fn_get_low_stock_items();

-- Expiring within 5 days
-- SELECT * FROM fn_get_expiring_items(5);

-- Dashboard KPIs
-- SELECT * FROM fn_get_dashboard_summary();

-- Full order details
-- SELECT o.order_number, o.status, oi.quantity, f.name, oi.unit_price, oi.total_price
-- FROM orders o
-- JOIN order_items oi ON oi.order_id = o.order_id
-- JOIN food_items f   ON f.food_item_id = oi.food_item_id
-- WHERE o.order_id = 1;

-- Stock movement history for a product
-- SELECT sm.movement_type, sm.quantity, sm.reason, sm.moved_at
-- FROM stock_movements sm
-- WHERE sm.food_item_id = 1
-- ORDER BY sm.moved_at DESC;

-- Category-wise inventory value
-- SELECT c.name AS category, COUNT(f.food_item_id) AS items,
--        SUM(i.quantity_available * f.price_per_unit) AS total_value
-- FROM food_items f
-- JOIN categories c ON c.category_id = f.category_id
-- JOIN inventory i  ON i.food_item_id = f.food_item_id
-- WHERE f.is_active = TRUE
-- GROUP BY c.name
-- ORDER BY total_value DESC;