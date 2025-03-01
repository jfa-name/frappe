import frappe


class DbManager:
	def __init__(self, db):
		"""
		Pass root_conn here for access to all databases.
		"""
		if db:
			self.db = db

	def get_current_host(self):
		return self.db.sql("select user()")[0][0].split("@")[1]

	def create_user(self, user, password, host=None):
		host = host or self.get_current_host()
		password_predicate = f" IDENTIFIED BY '{password}'" if password else ""
		self.db.sql(f"CREATE USER '{user}'@'{host}'{password_predicate}")

	def delete_user(self, target, host=None):
		host = host or self.get_current_host()
		self.db.sql(f"DROP USER IF EXISTS '{target}'@'{host}'")

	def create_database(self, target):
		if target in self.get_database_list():
			self.drop_database(target)
		self.db.sql(f"CREATE DATABASE `{target}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

	def drop_database(self, target):
		self.db.sql_ddl(f"DROP DATABASE IF EXISTS `{target}`")

	def grant_all_privileges(self, target, user, host=None):
		host = host or self.get_current_host()
		permissions = (
			(
				"SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, "
				"CREATE TEMPORARY TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, "
				"CREATE ROUTINE, ALTER ROUTINE, EXECUTE, LOCK TABLES"
			)
			if frappe.conf.rds_db
			else "ALL PRIVILEGES"
		)
		self.db.sql(f"GRANT {permissions} ON `{target}`.* TO '{user}'@'{host}'")

	def flush_privileges(self):
		self.db.sql("FLUSH PRIVILEGES")

	def get_database_list(self):
		return self.db.sql("SHOW DATABASES", pluck=True)

	@staticmethod
	def restore_database(target, source, user, password):
		import os
		from distutils.spawn import find_executable

		from frappe.utils import make_esc

		esc = make_esc("$ ")
		pv = find_executable("pv")

		if pv:
			pipe = f"{pv} {source} | " + r"sed '/\/\*M\{0,1\}!999999\\- enable the sandbox mode \*\//d' |"
		else:
			pipe = f"cat {source} | " + r"sed '/\/\*M\{0,1\}!999999\\- enable the sandbox mode \*\//d' |"

		if pipe:
			print("Restoring Database file...")

		command = (
			"{pipe} mysql -u {user} -p{password} -h{host} "
			+ ("-P{port}" if frappe.db.port else "")
			+ " {target}"
		)

		command = command.format(
			pipe=pipe,
			user=esc(user),
			password=esc(password),
			host=esc(frappe.db.host),
			target=esc(target),
			port=frappe.db.port,
		)

		os.system(command)
		frappe.cache().delete_keys("")  # Delete all keys associated with this site.
