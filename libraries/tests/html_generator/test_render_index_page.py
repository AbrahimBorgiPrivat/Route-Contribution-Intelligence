import tempfile
import os
import webbrowser
from pathlib import Path
from libraries.utils.visualization.html_generator import render_index_page


def test_render_index_page_saved_mode():
    # --------------------------------------------------
    # Arrange
    # --------------------------------------------------
    routes = [
        {
            "route_id": 1,
            "profile": "foot",
            "t1_L_original": 1200,
            "t1_L_opt": 900,
            "t2_L_original": 1150,
            "t2_L_opt": 850,
        },
        {
            "route_id": 2,
            "profile": "car",
            "t1_L_original": 2400,
            "t1_L_opt": 1900,
            "t2_L_original": 2300,
            "t2_L_opt": 1800,
        },
    ]

    kpis = [
        {"name": "Rute ID", "key": "route_id"},
        {"name": "Profil", "key": "profile"},
        {"name": "T1 Længde (Org.)", "key": "t1_L_original"},
        {"name": "T1 Længde (Opt.)", "key": "t1_L_opt"},
        {"name": "T2 Længde (Org.)", "key": "t2_L_original"},
        {"name": "T2 Længde (Opt.)", "key": "t2_L_opt"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        views_root = Path(tmpdir)

        # --------------------------------------------------
        # Inject test template
        # --------------------------------------------------
        template_src = Path(
            "libraries/tests/_test_templates/templates/index_page.html"
        )
        assert template_src.exists(), "Test index_page.html template missing"

        template_dst = views_root / "templates"
        template_dst.mkdir(parents=True)

        (template_dst / "index_page.html").write_text(
            template_src.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        # --------------------------------------------------
        # Act (UNDER TEST)
        # --------------------------------------------------
        out = render_index_page(
            routes=routes,
            kpis=kpis,
            saved_or_show="save",
            views_root=str(views_root),
        )

        # --------------------------------------------------
        # Assert
        # --------------------------------------------------
        assert isinstance(out, dict)
        assert "html_path" in out

        html_path = views_root / "index.html"
        assert html_path.exists()

        html = html_path.read_text(encoding="utf-8")

        assert "1" in html
        assert "2" in html
        assert "Rute ID" in html
        assert "Profil" in html
        assert "./maps/all_routes_map.html" in html

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] render_index_page")
        print("-" * 70)
        print(f"HTML path : {html_path}")
        print("HTML preview:")
        print(html[:400])
        print("-" * 70)

def test_render_index_page_show_mode(monkeypatch, tmp_path) -> None:
    """
    Coverage test:
    Exercise SHOW branch (lines 82_87) in render_index_page.
    """
    print("\n=== TEST CASE: render_index_page SHOW mode ===")
    routes = [
        {"route_id": 1, "profile": "foot"},
        {"route_id": 2, "profile": "car"},
    ]
    kpis = [
        {"name": "Rute ID", "key": "route_id"},
        {"name": "Profil", "key": "profile"},
    ]
    views_root = tmp_path
    templates_dir = views_root / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "index_page.html").write_text(
        """
        <html>
            <body>
                <h1>Index</h1>
                {% for r in routes %}
                    <div>{{ r.route_id }} - {{ r.profile }}</div>
                {% endfor %}
                <iframe src="{{ map_file }}"></iframe>
            </body>
        </html>
        """,
        encoding="utf-8",
    )
    opened_urls = []
    def fake_open(url):
        opened_urls.append(url)
        return True
    monkeypatch.setattr(webbrowser, "open", fake_open)
    out = render_index_page(
        routes=routes,
        kpis=kpis,
        saved_or_show="show",
        views_root=str(views_root),
    )
    assert isinstance(out, dict)
    assert "html_path" in out
    html_path = out["html_path"]
    assert os.path.exists(html_path)
    html = Path(html_path).read_text(encoding="utf-8")
    assert "1 - foot" in html
    assert "2 - car" in html
    assert "<iframe" in html
    assert "./maps/all_routes_map.html" in html
    assert len(opened_urls) == 1
    assert opened_urls[0].startswith("file://")

if __name__ == "__main__":
    test_render_index_page_saved_mode()
