def test_index_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "<title>Takcas Coder</title>" in html
    # Проверяем, что JS вынесен в отдельный файл, как мы и сделали
    assert 'src="script.js"' in html
    assert 'href="style.css"' in html

def test_static_served(client):
    assert client.get("/style.css").status_code == 200
    assert client.get("/script.js").status_code == 200

def test_frontend_personas(client):
    js = client.get("/script.js").get_data(as_text=True)
    # Проверяем, что фронт шлет правильные латинские ключи
    for key in ("taksas", "dubina", "prokrastinator", "potassium", "coder"):
        assert key in js
