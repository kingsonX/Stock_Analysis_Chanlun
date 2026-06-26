CREATE DATABASE IF NOT EXISTS `Stock_Analysis_Chanlun`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `Stock_Analysis_Chanlun`;

CREATE TABLE IF NOT EXISTS `stock_basic_snapshots` (
  `ts_code` varchar(16) NOT NULL,
  `symbol` varchar(16) NOT NULL DEFAULT '',
  `name` varchar(64) NOT NULL DEFAULT '',
  `area` varchar(32) NOT NULL DEFAULT '',
  `industry` varchar(64) NOT NULL DEFAULT '',
  `market` varchar(32) NOT NULL DEFAULT '',
  `exchange` varchar(16) NOT NULL DEFAULT '',
  `list_date` varchar(16) NOT NULL DEFAULT '',
  `trade_date` date DEFAULT NULL,
  `raw_payload` json NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ts_code`),
  KEY `idx_stock_basic_trade_date` (`trade_date`),
  KEY `idx_stock_basic_name` (`name`),
  KEY `idx_stock_basic_symbol` (`symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analysis_watchlist_entries` (
  `ts_code` varchar(16) NOT NULL,
  `symbol` varchar(16) NOT NULL DEFAULT '',
  `name` varchar(64) NOT NULL DEFAULT '',
  `area` varchar(32) NOT NULL DEFAULT '',
  `industry` varchar(64) NOT NULL DEFAULT '',
  `market` varchar(32) NOT NULL DEFAULT '',
  `exchange` varchar(16) NOT NULL DEFAULT '',
  `list_date` varchar(16) NOT NULL DEFAULT '',
  `bak_trade_date` date DEFAULT NULL,
  `raw_payload` json NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ts_code`),
  KEY `idx_watchlist_updated_at` (`updated_at`),
  KEY `idx_watchlist_name` (`name`),
  KEY `idx_watchlist_symbol` (`symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hot_money_daily_fetches` (
  `trade_date` date NOT NULL,
  `source_api` varchar(32) NOT NULL DEFAULT 'hm_detail',
  `status` varchar(16) NOT NULL DEFAULT 'success',
  `record_count` int(11) NOT NULL DEFAULT '0',
  `fetched_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hot_money_daily_trades` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `trade_date` date NOT NULL,
  `ts_code` varchar(16) NOT NULL DEFAULT '',
  `ts_name` varchar(64) NOT NULL DEFAULT '',
  `buy_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `sell_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `net_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `hm_name` varchar(128) NOT NULL DEFAULT '',
  `hm_orgs` varchar(255) NOT NULL DEFAULT '',
  `tag` varchar(64) NOT NULL DEFAULT '',
  `raw_payload` json NOT NULL,
  `fetched_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_hot_money_trade_date` (`trade_date`),
  KEY `idx_hot_money_ts_code` (`ts_code`),
  KEY `idx_hot_money_hm_name` (`hm_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
