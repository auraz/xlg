"""Fill plugin tests."""

from xlg.plugins.fill import load_sites, load_profile, resolve_target, extract_form_html, map_fields_with_claude, fill_form_fields, cmd_fill


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


def test_fill_form_fields(mocker):
    mock_page = mocker.MagicMock()
    mappings = {"#name": "John", "#zip": "90210"}
    fill_form_fields(mock_page, mappings)
    assert mock_page.fill.call_count == 2
    mock_page.fill.assert_any_call("#name", "John")
    mock_page.fill.assert_any_call("#zip", "90210")


def test_cmd_fill_integration(tmp_path, mocker):
    sites_file = tmp_path / "data" / "sites.json"
    profile_file = tmp_path / "data" / "profile.json"
    sites_file.parent.mkdir(parents=True)
    sites_file.write_text('{"test": "https://example.com/form"}')
    profile_file.write_text('{"name": "John"}')
    mocker.patch.dict("os.environ", {"XLG_CONFIG_DIR": str(tmp_path)})
    mock_playwright = mocker.patch("xlg.plugins.fill.sync_playwright")
    mock_browser = mocker.MagicMock()
    mock_page = mocker.MagicMock()
    mock_page.content.return_value = "<form><input id='name'></form>"
    mock_browser.new_page.return_value = mock_page
    mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
    mock_claude = mocker.patch("xlg.plugins.fill.anthropic.Anthropic")
    mock_claude.return_value.messages.create.return_value.content = [mocker.MagicMock(text='{"#name": "John"}')]
    mocker.patch("builtins.input", return_value="")
    result = cmd_fill(None, "test")
    assert "filled" in result.lower()
