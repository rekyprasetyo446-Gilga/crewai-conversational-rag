-- Database Creation
CREATE DATABASE IF NOT EXISTS crewai_memory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crewai_memory;

-- 1. Chat Sessions Table
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content MEDIUMTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Agent Execution Logs Table
CREATE TABLE IF NOT EXISTS agent_execution_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    input_data MEDIUMTEXT NULL,
    output_data MEDIUMTEXT NULL,
    tool_calls JSON NULL,
    execution_time_ms INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_session (session_id, agent_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Shared Blackboard Table (for Agent Collaboration)
CREATE TABLE IF NOT EXISTS shared_blackboard (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    source_agent VARCHAR(100) NOT NULL,
    key_name VARCHAR(100) NOT NULL,
    value_data MEDIUMTEXT NOT NULL,
    tags VARCHAR(255) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_session_key (session_id, key_name),
    INDEX idx_session_bb (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. User Privileges (Optional - Configure per Hostinger environment)
-- CREATE USER IF NOT EXISTS 'crew_agent'@'%' IDENTIFIED BY 'AgentSecurePass123!';
-- GRANT ALL PRIVILEGES ON crewai_memory.* TO 'crew_agent'@'%';
-- FLUSH PRIVILEGES;
