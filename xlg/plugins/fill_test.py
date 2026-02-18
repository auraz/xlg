"""Fill plugin tests."""

from xlg.plugins.fill import load_sites, load_profile, resolve_target, extract_form_html, map_fields_with_claude


def test_load_sites(tmp_path):
    sites_file = tmp_path / "sites.json"
    sites_file.write_text('{"amazon": "https://amazon.com/checkout"}')
    sites = load_sites(sites_file)
    assert sites["amazon"] == "https://amazon.com/checkout"


def test_load_profile(tmp_path):
    profile_file = tmp_path / "profile.json"
    profile_file.write_text('{"name": "John", "zip": "90210"}')
    profile = load_profile(profile_file)
    assert profile["name"] == "John"


def test_resolve_target_alias(tmp_path):
    sites_file = tmp_path / "sites.json"
    sites_file.write_text('{"amazon": "https://amazon.com/checkout"}')
    url = resolve_target("amazon", sites_file)
    assert url == "https://amazon.com/checkout"


def test_resolve_target_url():
    url = resolve_target("https://example.com", None)
    assert url == "https://example.com"


def test_extract_form_html():
    html = """
    <html>
    <body>
        <header>Nav</header>
        <form id="checkout">
            <input name="name" type="text">
            <input name="zip" type="text">
        </form>
        <footer>Footer</footer>
    </body>
    </html>
    """
    form_html = extract_form_html(html)
    assert "<form" in form_html
    assert 'name="name"' in form_html
    assert "<header>" not in form_html


def test_map_fields_with_claude(mocker):
    mock_client = mocker.MagicMock()
    mock_client.messages.create.return_value.content = [mocker.MagicMock(text='{"#name": "John", "#zip": "90210"}')]
    profile = {"name": "John", "zip": "90210"}
    form_html = '<form><input id="name"><input id="zip"></form>'
    mappings = map_fields_with_claude(mock_client, form_html, profile)
    assert mappings == {"#name": "John", "#zip": "90210"}
