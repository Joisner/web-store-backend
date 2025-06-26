-- Tabla: users
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255),
    email NVARCHAR(255) NOT NULL UNIQUE,
    hashed_password NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) DEFAULT 'Usuario',
    status NVARCHAR(8) DEFAULT 'active', -- Enum: 'active', 'inactive'
    created_at DATETIME DEFAULT GETDATE(),
    avatar NVARCHAR(255) NULL
);

INSERT INTO users (name, email, hashed_password, role, status)
VALUES ('Juan Pérez', 'juan@email.com', 'hashedpass', 'Administrador', 'active');


-- Tabla: categories
CREATE TABLE categories (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    slug NVARCHAR(255) NOT NULL UNIQUE,
    parent_id INT NULL,
    color NVARCHAR(50) NULL,
    description NVARCHAR(MAX) NULL,
    CONSTRAINT FK_categories_parent FOREIGN KEY (parent_id) REFERENCES categories(id)
);

INSERT INTO categories (name, slug, color, description)
VALUES ('Electrónica', 'electronica', '#FF0000', 'Categoría de productos electrónicos');


-- Tabla: products
CREATE TABLE products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    short_description NVARCHAR(500) NULL,
    sku NVARCHAR(100) NOT NULL UNIQUE,
    barcode NVARCHAR(100) NULL,
    category_id INT NOT NULL,
    tags NVARCHAR(MAX) NULL,
    base_price FLOAT NOT NULL,
    sale_price FLOAT NULL,
    cost_price FLOAT NULL,
    stock INT DEFAULT 0,
    reserved_stock INT DEFAULT 0,
    low_stock_threshold INT DEFAULT 0,
    track_inventory BIT DEFAULT 1,
    allow_backorder BIT DEFAULT 0,
    meta_title NVARCHAR(255) NULL,
    meta_description NVARCHAR(MAX) NULL,
    slug NVARCHAR(255) NOT NULL UNIQUE,
    keywords NVARCHAR(MAX) NULL,
    og_image NVARCHAR(255) NULL,
    status NVARCHAR(8) NOT NULL DEFAULT 'draft', -- Enum: 'active', 'inactive', 'draft'
    visibility NVARCHAR(8) NOT NULL DEFAULT 'private', -- Enum: 'public', 'private', 'catalog'
    featured BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    created_by_user_id INT NULL,
    last_modified_by_user_id INT NULL,
    discounts NVARCHAR(MAX) NULL,
    customer_pricing NVARCHAR(MAX) NULL,
    CONSTRAINT FK_products_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT FK_products_created_by FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    CONSTRAINT FK_products_modified_by FOREIGN KEY (last_modified_by_user_id) REFERENCES users(id)
);

INSERT INTO products (name, sku, category_id, base_price, slug)
VALUES ('Laptop', 'SKU123', 1, 15000, 'laptop');


-- Tabla: product_images
CREATE TABLE product_images (
    id INT IDENTITY(1,1) PRIMARY KEY,
    url NVARCHAR(2048) NOT NULL,
    alt NVARCHAR(255) NULL,
    display_order INT DEFAULT 0,
    is_main BIT DEFAULT 0,
    product_id INT NOT NULL,
    CONSTRAINT FK_product_images_product FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO product_images (url, product_id)
VALUES ('https://ejemplo.com/imagen.jpg', 1);


-- Tabla: product_variants
CREATE TABLE product_variants (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    type NVARCHAR(10) NOT NULL, -- Enum: 'size', 'color', 'material', 'style'
    value NVARCHAR(100) NOT NULL,
    sku NVARCHAR(150) UNIQUE,
    price_override FLOAT NULL,
    stock INT DEFAULT 0 NOT NULL,
    image NVARCHAR(2048) NULL,
    product_id INT NOT NULL,
    CONSTRAINT FK_product_variants_product FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO product_variants (name, type, value, product_id)
VALUES ('Rojo', 'color', 'Rojo', 1);


-- Tabla: stock_histories
CREATE TABLE stock_histories (
    id INT IDENTITY(1,1) PRIMARY KEY,
    date DATETIME DEFAULT GETDATE() NOT NULL,
    type NVARCHAR(10) NOT NULL, -- Enum: 'adjustment', 'sale', 'purchase', 'return'
    quantity INT NOT NULL,
    previous_stock INT NOT NULL,
    new_stock INT NOT NULL,
    reason NVARCHAR(500) NULL,
    product_id INT NOT NULL,
    user_id INT NULL,
    user_name NVARCHAR(255) NULL,
    CONSTRAINT FK_stock_histories_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT FK_stock_histories_user FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO stock_histories (type, quantity, previous_stock, new_stock, product_id)
VALUES ('sale', 2, 10, 8, 1);
