import sqlite3

from .config import DATABASE_PATH


class VCLogQueries:
	create_config_table = """
CREATE TABLE IF NOT EXISTS vc_log_config (
	guild_id TEXT PRIMARY KEY,
	channel_id TEXT NOT NULL
)
"""

	upsert_channel = """
INSERT INTO vc_log_config (guild_id, channel_id)
VALUES (?, ?)
ON CONFLICT(guild_id)
DO UPDATE SET channel_id = excluded.channel_id;
"""

	get_channel = """
SELECT channel_id
FROM vc_log_config
WHERE guild_id = ?;
"""

	remove_channel = """
DELETE FROM vc_log_config
WHERE guild_id = ?;
"""


class VCLogDatabase:
	def __init__(self):
		with self.connect_db() as db:
			db.cursor().execute(VCLogQueries.create_config_table)
			db.commit()

	def connect_db(self):
		return sqlite3.connect(DATABASE_PATH)

	def set_channel(self, guild_id, channel_id):
		with self.connect_db() as db:
			db.cursor().execute(
				VCLogQueries.upsert_channel,
				(str(guild_id), str(channel_id))
			)
			db.commit()

	def get_channel(self, guild_id):
		with self.connect_db() as db:
			result = db.cursor().execute(
				VCLogQueries.get_channel,
				(str(guild_id),)
			).fetchone()

		return result[0] if result else None

	def remove_channel(self, guild_id):
		with self.connect_db() as db:
			db.cursor().execute(
				VCLogQueries.remove_channel,
				(str(guild_id),)
			)
			db.commit()
