import unittest

import server


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_index_returns_html_with_external_assets(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn("<title>Takcas Coder</title>", html)
        # JS и CSS вынесены в отдельные файлы — именно это ломалось
        self.assertIn('src="script.js"', html)
        self.assertIn('href="style.css"', html)

    def test_static_files_served(self):
        self.assertEqual(self.client.get("/style.css").status_code, 200)
        self.assertEqual(self.client.get("/script.js").status_code, 200)

    def test_script_uses_backend_persona_keys(self):
        js = self.client.get("/script.js").get_data(as_text=True)
        # Фронт должен слать латиницу, которую ждёт server.py
        for key in ("taksas", "dubina", "prokrastinator", "potassium", "coder"):
            self.assertIn(key, js)

    def test_script_targets_chat_endpoint(self):
        js = self.client.get("/script.js").get_data(as_text=True)
        self.assertIn("/chat", js)


if __name__ == "__main__":
    unittest.main()
