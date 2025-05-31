PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version VALUES('2afd24b4fb9e');
CREATE TABLE system_settings (
	id INTEGER NOT NULL, 
	"key" VARCHAR(100) NOT NULL, 
	value TEXT, 
	description TEXT, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE ("key")
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	username VARCHAR(100) NOT NULL, 
	hashed_password VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255), 
	role VARCHAR(20), 
	is_active BOOLEAN, 
	is_verified BOOLEAN, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME, 
	last_login DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO users VALUES(1,'admin@deadmanswitch.com','admin','$2b$12$6BGAGNjj2vD40FC2b9HCouGMNn2xDI9wQQD7Mx.QzfG54KbFyAWjS','System Administrator','admin',1,1,'2025-05-31 03:22:26','2025-05-31 04:47:38','2025-05-31 04:47:38.491631');
INSERT INTO users VALUES(2,'hans@yahoo.com','Hans','$2b$12$oyuLjEwCVEgH3w4TbWm0cuQItRz9.koHWoZFfhi.ey1xOo.Z1Ug66','hans','client',1,0,'2025-05-31 04:46:56',NULL,NULL);
INSERT INTO users VALUES(3,'user123@example.com','user123','$2b$12$dgCH9rteLvHpiyX2qVp6iO/42D.RxtAwbds8FYwADWOmDShwYDBRK','User 123','client',1,1,'2025-05-31 04:48:19',NULL,NULL);
INSERT INTO users VALUES(4,'user@example.com','user','$2b$12$uUf6ZPrNg41CMj9pMPb4IOD0rsY/WCd3g2OFLWaoeEyN6Wo67go0a','Test User','client',1,1,'2025-05-31 04:48:53','2025-05-31 04:49:22','2025-05-31 04:49:22.935438');
CREATE TABLE deadman_switches (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	check_in_interval DATETIME, 
	grace_period DATETIME, 
	status VARCHAR(20), 
	is_enabled BOOLEAN, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME, 
	last_check_in DATETIME, 
	next_check_in_due DATETIME, 
	triggered_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE check_ins (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	deadman_switch_id INTEGER NOT NULL, 
	check_in_time DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	ip_address VARCHAR(45), 
	user_agent TEXT, 
	location VARCHAR(255), 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deadman_switch_id) REFERENCES deadman_switches (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE emergency_contacts (
	id INTEGER NOT NULL, 
	deadman_switch_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255), 
	phone VARCHAR(20), 
	contact_relationship VARCHAR(100), 
	priority INTEGER, 
	is_active BOOLEAN, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(deadman_switch_id) REFERENCES deadman_switches (id)
);
CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	deadman_switch_id INTEGER NOT NULL, 
	recipient_email VARCHAR(255) NOT NULL, 
	recipient_phone VARCHAR(20), 
	subject VARCHAR(500), 
	message TEXT NOT NULL, 
	notification_type VARCHAR(50), 
	status VARCHAR(20), 
	scheduled_for DATETIME, 
	sent_at DATETIME, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	error_message TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deadman_switch_id) REFERENCES deadman_switches (id)
);
CREATE INDEX ix_system_settings_id ON system_settings (id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX ix_deadman_switches_id ON deadman_switches (id);
CREATE INDEX ix_check_ins_id ON check_ins (id);
CREATE INDEX ix_emergency_contacts_id ON emergency_contacts (id);
CREATE INDEX ix_notifications_id ON notifications (id);
COMMIT;
