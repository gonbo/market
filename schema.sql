-- To create the database:
--   CREATE DATABASE btc;
--   GRANT ALL PRIVILEGES ON btc.* TO 'btc'@'localhost' IDENTIFIED
--   BY 'btcpass';
--
-- To reload the tables:
--   mysql --user=btc --password=btcpass --database=btc < schema.sql

SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";

DROP TABLE IF EXISTS account;
create table account (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(40) NOT NULL UNIQUE,
    username VARCHAR(40) NOT NULL,
    password VARCHAR(60) NOT NULL,
    created_at TIMESTAMP DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    token VARCHAR(100),
    cny DECIMAL(16, 2) DEFAULT 0,
    btc DECIMAL(16, 8) DEFAULT 0,
    frozen_cny DECIMAL(16, 2) DEFAULT 0,
    frozen_btc DECIMAL(16, 8) DEFAULT 0,
    index(email),
    index(token)
);

DROP TABLE IF EXISTS reset_password;
create table reset (
    reset_code VARCHAR(60) not NULL PRIMARY KEY,
    email VARCHAR(40) not NULL UNIQUE
);
