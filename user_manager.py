import json
import os

class UserManager:
    def __init__(self, data_file="user_data.json"):
        self.data_file = data_file
        self.users = self._load_data()
    
    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.users, f)
    
    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "style": "romantic",
                "history": [],
                "girlfriend_name": "",
                "personal_details": {}
            }
            self._save_data()
        return self.users[user_id]
    
    def update_style(self, user_id, style):
        user_id = str(user_id)
        user = self.get_user(user_id)
        user["style"] = style
        self._save_data()
    
    def add_to_history(self, user_id, message_pair):
        """Add a message pair (girlfriend's message, bot's response) to history"""
        user_id = str(user_id)
        user = self.get_user(user_id)
        
        # Add new message pair
        user["history"].append(message_pair)
        
        # Keep only the last MAX_HISTORY_LENGTH messages
        from config import MAX_HISTORY_LENGTH
        if len(user["history"]) > MAX_HISTORY_LENGTH:
            user["history"] = user["history"][-MAX_HISTORY_LENGTH:]
        
        self._save_data()
    
    def update_girlfriend_name(self, user_id, name):
        user_id = str(user_id)
        user = self.get_user(user_id)
        user["girlfriend_name"] = name
        self._save_data()
    
    def add_personal_detail(self, user_id, key, value):
        user_id = str(user_id)
        user = self.get_user(user_id)
        user["personal_details"][key] = value
        self._save_data() 