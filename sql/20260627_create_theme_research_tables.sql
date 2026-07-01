CREATE TABLE IF NOT EXISTS theme_research_tasks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  task_id VARCHAR(128) NOT NULL,
  theme_name VARCHAR(128) NOT NULL,
  market VARCHAR(32) NOT NULL DEFAULT 'A股',
  analysis_depth VARCHAR(32) NOT NULL DEFAULT 'standard',
  time_horizon VARCHAR(32) NOT NULL DEFAULT '短中线',
  status VARCHAR(32) NOT NULL DEFAULT 'created',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_theme_research_task_id (task_id),
  KEY idx_theme_research_status (status),
  KEY idx_theme_research_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS theme_research_steps (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  task_id VARCHAR(128) NOT NULL,
  step_no INT NOT NULL,
  step_title VARCHAR(255) NOT NULL,
  event_type VARCHAR(32) NOT NULL DEFAULT 'step_update',
  status VARCHAR(32) NOT NULL,
  message TEXT,
  data_preview LONGTEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_theme_research_steps_task (task_id),
  KEY idx_theme_research_steps_event (event_type),
  KEY idx_theme_research_steps_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS theme_research_reports (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  task_id VARCHAR(128) NOT NULL,
  theme_name VARCHAR(128) NOT NULL,
  report_json LONGTEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_theme_research_reports_task_id (task_id),
  KEY idx_theme_research_reports_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
