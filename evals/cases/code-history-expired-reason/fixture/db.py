"""Profile database client (connection details elided in this copy)."""


class _ProfileDB:
    def fetch_one(self, user_id):
        raise NotImplementedError

    def fetch_many(self, user_ids):
        raise NotImplementedError


profile_db = _ProfileDB()
