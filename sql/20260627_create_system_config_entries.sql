CREATE TABLE IF NOT EXISTS `system_config_entries` (
  `config_key` varchar(64) NOT NULL,
  `label` varchar(64) NOT NULL DEFAULT '',
  `category` varchar(32) NOT NULL DEFAULT 'custom',
  `config_value` longtext NOT NULL,
  `is_secret` tinyint(1) NOT NULL DEFAULT 1,
  `is_enabled` tinyint(1) NOT NULL DEFAULT 1,
  `description` varchar(255) NOT NULL DEFAULT '',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_key`),
  KEY `idx_system_config_category` (`category`),
  KEY `idx_system_config_enabled` (`is_enabled`),
  KEY `idx_system_config_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
