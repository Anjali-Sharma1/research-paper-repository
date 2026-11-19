-- ============================================================
-- RPRMS Database Schema
-- Module 1: departments, users
-- Module 2: (uses existing users table — no new tables needed)
-- Run: mysql -u root -p rprms_db < database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS rprms_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE rprms_db;

-- ── TABLE 1: departments ──────────────────────────────────────────────────────
-- Must be created before users (users has FK to departments)
CREATE TABLE IF NOT EXISTS departments (
    dept_id    INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    dept_name  VARCHAR(100)    NOT NULL UNIQUE,
    dept_code  VARCHAR(20)     NOT NULL UNIQUE,
    hod_name   VARCHAR(120)    DEFAULT NULL,
    created_at DATETIME        DEFAULT NOW()
) ENGINE=InnoDB;

-- ── TABLE 2: users ────────────────────────────────────────────────────────────
-- Central table. Every other module references user_id.
-- Module 2 uses: email, password_hash, role, is_active, last_login
CREATE TABLE IF NOT EXISTS users (
    user_id       INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(120)   NOT NULL,
    email         VARCHAR(120)   NOT NULL UNIQUE,
    password_hash VARCHAR(255)   NOT NULL,
    role          ENUM('admin','faculty','student') NOT NULL,
    phone         VARCHAR(20)    DEFAULT NULL,
    is_active     TINYINT(1)     NOT NULL DEFAULT 1,
    dept_id       INT UNSIGNED   DEFAULT NULL,
    created_by    INT UNSIGNED   DEFAULT NULL,
    created_at    DATETIME       DEFAULT NOW(),
    updated_at    DATETIME       DEFAULT NOW() ON UPDATE NOW(),
    last_login    DATETIME       DEFAULT NULL,

    CONSTRAINT fk_users_dept
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_users_created_by
        FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ── TABLE 3: notifications ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    notif_id   INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    user_id    INT UNSIGNED   NOT NULL,
    message    TEXT           NOT NULL,
    link       VARCHAR(255)   DEFAULT NULL,
    is_read    TINYINT(1)     NOT NULL DEFAULT 0,
    created_at DATETIME       DEFAULT NOW(),

    CONSTRAINT fk_notif_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── TABLE 4: activity_logs ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id     INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    user_id    INT UNSIGNED   DEFAULT NULL,
    action     VARCHAR(100)   NOT NULL,
    entity     VARCHAR(50)    DEFAULT NULL,
    entity_id  INT UNSIGNED   DEFAULT NULL,
    ip_address VARCHAR(45)    DEFAULT NULL,
    created_at DATETIME       DEFAULT NOW(),

    CONSTRAINT fk_log_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ── TABLE 5: papers ───────────────────────────────────────────────────────────
-- Module 5: Paper Upload & Metadata
-- uploaded_by FK → users, dept_id FK → departments
CREATE TABLE IF NOT EXISTS papers (
    paper_id      INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    paper_code    VARCHAR(30)    NOT NULL UNIQUE,
    title         VARCHAR(500)   NOT NULL,
    abstract      TEXT           DEFAULT NULL,
    keywords      VARCHAR(500)   DEFAULT NULL,
    research_area VARCHAR(150)   DEFAULT NULL,
    guide_name    VARCHAR(150)   DEFAULT NULL,
    dept_id       INT UNSIGNED   DEFAULT NULL,
    pub_year      YEAR           DEFAULT NULL,
    paper_type    ENUM('journal','conference','thesis','book_chapter','other')
                                 NOT NULL DEFAULT 'journal',
    uploaded_by   INT UNSIGNED   NOT NULL,
    file_name     VARCHAR(255)   NOT NULL,
    file_path     VARCHAR(500)   NOT NULL,
    file_size     BIGINT UNSIGNED DEFAULT NULL,
    status        ENUM('pending','approved','rejected','changes_requested')
                                 NOT NULL DEFAULT 'pending',
    qr_code_path  VARCHAR(500)   DEFAULT NULL,
    created_at    DATETIME       DEFAULT NOW(),
    updated_at    DATETIME       DEFAULT NOW() ON UPDATE NOW(),

    CONSTRAINT fk_papers_dept
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_papers_uploader
        FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ── TABLE 6: paper_status_history ────────────────────────────────────────────
-- Module 6: Paper Approval Workflow
-- Audit trail of every status change with reviewer comments
CREATE TABLE IF NOT EXISTS paper_status_history (
    history_id  INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    paper_id    INT UNSIGNED   NOT NULL,
    old_status  VARCHAR(30)    DEFAULT NULL,
    new_status  VARCHAR(30)    NOT NULL,
    changed_by  INT UNSIGNED   NOT NULL,
    comments    TEXT           DEFAULT NULL,
    changed_at  DATETIME       DEFAULT NOW(),

    CONSTRAINT fk_psh_paper
        FOREIGN KEY (paper_id)  REFERENCES papers(paper_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_psh_changed_by
        FOREIGN KEY (changed_by) REFERENCES users(user_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ── TABLE 7: paper_versions ───────────────────────────────────────────────────
-- Module 7: Paper Version Management
-- Every upload (initial + re-upload) creates one version row
CREATE TABLE IF NOT EXISTS paper_versions (
    version_id    INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    paper_id      INT UNSIGNED   NOT NULL,
    version_no    TINYINT UNSIGNED NOT NULL DEFAULT 1,
    file_name     VARCHAR(255)   NOT NULL,
    file_path     VARCHAR(500)   NOT NULL,
    file_size     BIGINT UNSIGNED DEFAULT NULL,
    uploaded_by   INT UNSIGNED   NOT NULL,
    change_notes  TEXT           DEFAULT NULL,
    uploaded_at   DATETIME       DEFAULT NOW(),

    CONSTRAINT fk_pv_paper
        FOREIGN KEY (paper_id)   REFERENCES papers(paper_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_pv_uploader
        FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ── TABLE 8: downloads ────────────────────────────────────────────────────────
-- Module 9: Bookmark & Download Tracking
CREATE TABLE IF NOT EXISTS downloads (
    download_id   INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    paper_id      INT UNSIGNED   NOT NULL,
    user_id       INT UNSIGNED   NOT NULL,
    downloaded_at DATETIME       DEFAULT NOW(),
    CONSTRAINT fk_dl_paper FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
    CONSTRAINT fk_dl_user  FOREIGN KEY (user_id)  REFERENCES users(user_id)   ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── TABLE 9: bookmarks ────────────────────────────────────────────────────────
-- Module 9: UNIQUE constraint prevents duplicate bookmarks
CREATE TABLE IF NOT EXISTS bookmarks (
    bookmark_id INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    paper_id    INT UNSIGNED   NOT NULL,
    user_id     INT UNSIGNED   NOT NULL,
    created_at  DATETIME       DEFAULT NOW(),
    CONSTRAINT uq_bookmark UNIQUE (paper_id, user_id),
    CONSTRAINT fk_bm_paper FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
    CONSTRAINT fk_bm_user  FOREIGN KEY (user_id)  REFERENCES users(user_id)   ON DELETE CASCADE
) ENGINE=InnoDB;
