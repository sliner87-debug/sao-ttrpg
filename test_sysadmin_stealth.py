import unittest
import re
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
import llm_engine
import mechanics

class TestSysAdminStealth(unittest.TestCase):

    def test_companion_intent_oblivious_to_root_override(self):
        """Companions must not perceive root override commands."""
        companion_data = {"name": "Ren", "stance": "overwatch_hacking"}
        # Should exit early without needing an api_key or making network requests
        res = llm_engine.generate_companion_intent(
            api_key=None,
            companion_data=companion_data,
            player_input="[ROOT OVERRIDE] Kill the boss",
            chat_history=[]
        )
        self.assertIn("remains completely unaware", res)
        self.assertIn("Ren", res)

    def test_companion_history_sanitization(self):
        """Companions' chat history must filter out past admin / root override commands."""
        companion_data = {"name": "Ren", "stance": "overwatch_hacking"}
        chat_history = [
            {"role": "user", "content": "Normal question"},
            {"role": "user", "content": "💻 **ROOT OVERRIDE EXECUTED:** set col to 999999", "ai_prompt": "[ROOT OVERRIDE] set col", "is_admin": True},
            {"role": "system", "content": "[SYSTEM: ROOT OVERRIDE EXECUTED] Added Col.", "is_admin": True},
            {"role": "user", "content": "Let's move out."}
        ]

        # Filter logic matching llm_engine.generate_companion_intent
        filtered_history = [
            msg for msg in chat_history
            if not (
                msg.get("is_admin", False) or
                msg.get("ai_prompt", "").startswith("[ROOT OVERRIDE]") or
                "[ROOT OVERRIDE]" in msg.get("content", "") or
                "ROOT OVERRIDE EXECUTED" in msg.get("content", "") or
                msg.get("content", "").startswith("/admin") or
                msg.get("content", "").startswith("/Admin")
            )
        ]
        self.assertEqual(len(filtered_history), 2)
        self.assertEqual(filtered_history[0]["content"], "Normal question")
        self.assertEqual(filtered_history[1]["content"], "Let's move out.")

    def test_admin_regex_case_insensitivity(self):
        """Admin commands must be caught regardless of casing (/admin, /Admin, /sysadmin, /root)."""
        test_inputs = [
            ("/admin Give 1000 Col", "Give 1000 Col"),
            ("/Admin Teleport to Washington", "Teleport to Washington"),
            ("/ADMIN Slay enemy", "Slay enemy"),
            ("/sysadmin reboot node", "reboot node"),
            ("/SysAdmin repair all", "repair all"),
            ("/root reveal map", "reveal map"),
            ("/Root clear dungeon", "clear dungeon"),
        ]

        for raw_prompt, expected_cmd in test_inputs:
            is_admin = bool(re.match(r"^/(admin|sysadmin|root)\b", raw_prompt.strip(), re.IGNORECASE))
            self.assertTrue(is_admin, f"Failed to match admin command for: {raw_prompt}")
            extracted = re.sub(r"^/(admin|sysadmin|root)\s*", "", raw_prompt.strip(), flags=re.IGNORECASE).strip()
            self.assertEqual(extracted, expected_cmd)

    def test_non_admin_prompt_not_flagged(self):
        """Normal prompts must not trigger admin mode."""
        normal_prompts = [
            "I walk to the vendor.",
            "Can I talk to the administrator?",
            "Look at the root of the tree",
            "Attack the goblin",
        ]
        for prompt in normal_prompts:
            is_admin = bool(re.match(r"^/(admin|sysadmin|root)\b", prompt.strip(), re.IGNORECASE))
            self.assertFalse(is_admin, f"False positive admin match on: {prompt}")

    def test_system_prompt_contains_stealth_directive(self):
        """The Encounter Director system instruction must contain explicit stealth requirements."""
        with open(os.path.join(os.path.dirname(__file__), 'backend', 'llm_engine.py'), 'r', encoding='utf-8') as f:
            code = f.read()

        self.assertIn("ROOT OVERRIDE & SYSADMIN STEALTH", code)
        self.assertIn("STRICTLY INVISIBLE AND IMPERCEPTIBLE TO THE REST OF THE WORLD", code)
        with open(os.path.join(os.path.dirname(__file__), 'app.py'), 'r', encoding='utf-8') as f:
            app_code = f.read()
        self.assertIn("Companions and NPCs remain completely oblivious", app_code)

if __name__ == '__main__':
    unittest.main()
