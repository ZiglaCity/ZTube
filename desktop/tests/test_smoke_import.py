def test_import_main_does_not_start_gui():
    import main

    assert hasattr(main, "start_app")


def test_import_desktop_app():
    import desktop.ztube_desktop.app as app

    assert hasattr(app, "start_app")
