-- To CREATE the database:
--   CREATE DATABASE btc;
--   GRANT ALL PRIVILEGES ON btc.* TO 'btc'@'localhost' IDENTIFIED
--   BY 'btcpass';
--
-- To reload the TABLEs:
--   mysql --user=btc --password=btcpass --database=btc < schema.sql

SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";

DROP TABLE IF EXISTS account;
CREATE TABLE account (
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
    INDEX(email),
    INDEX(token)
);

DROP TABLE IF EXISTS reset;
CREATE TABLE reset (
    reset_code VARCHAR(60) not NULL PRIMARY KEY,
    email VARCHAR(40) not NULL UNIQUE
);

DROP TABLE IF EXISTS user_bid_order;
CREATE TABLE user_bid_order (
    id FLOAT(40, 0) NOT NULL PRIMARY KEY,
    uid INT NOT NULL,
    amount DECIMAL(16, 8) NOT NULL,
    price DECIMAL(16, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(uid)
);

DROP TABLE IF EXISTS user_bid_order_his;
CREATE TABLE user_bid_order_his (
    id INT NOT NULL,
    uid INT NOT NULL,
    amount DECIMAL(16, 8) NOT NULL,
    price DECIMAL(16, 2) NOT NULL,
    strike_price DECIMAL(16, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT 0,
    done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(uid)
);

DROP TABLE IF EXISTS user_ask_order;
CREATE TABLE user_ask_order (
    id FLOAT(40, 0) NOT NULL PRIMARY KEY,
    uid INT NOT NULL,
    amount DECIMAL(16, 8) NOT NULL,
    price DECIMAL(16, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(uid)
);

DROP TABLE IF EXISTS user_ask_order_his;
CREATE TABLE user_ask_order_his (
    id int NOT NULL,
    uid INT NOT NULL,
    amount DECIMAL(16, 8) NOT NULL,
    price DECIMAL(16, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT 0,
    done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(uid)
);

DROP VIEW IF EXISTS ordered_user_bid_order_view;
CREATE VIEW ordered_user_bid_order_view as
SELECT * FROM user_bid_order
ORDER BY price DESC, created_at ASC;

DROP VIEW IF EXISTS ordered_user_ask_order_view;
CREATE VIEW ordered_user_ask_order_view as
SELECT * FROM user_ask_order
ORDER BY price ASC, created_at ASC;

DROP TABLE IF EXISTS transaction;
CREATE TABLE transaction (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(16, 8) NOT NULL,
    price DECIMAL(16, 2) NOT NULL,
    bid_order_id INT NOT NULL,
    ask_order_id INT NOT NULL,
    bid_user_id INT NOT NULL,
    ask_user_id INT NOT NULL,
    done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
