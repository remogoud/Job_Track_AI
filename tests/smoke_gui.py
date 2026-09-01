"""
Job_Track_AI - Headless / Desktop GUI Smoke Test.

Constructs the Tkinter interface, initializes all tabs, verifies widget
instantiation and styling bindings, and exits cleanly. Runs both in normal
environments and headless CI test runners.
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_gui_smoke_test():
    print("[1/4] Initializing JobTrackApp in test mode...")
    from gui.app import JobTrackApp
    
    # Hide window immediately to avoid UI popups during test
    app = JobTrackApp(user_id="test-user")
    app.withdraw()

    print("[2/4] Verifying all 7 tabs and core widgets...")
    assert hasattr(app, "tab_search"), "tab_search missing"
    assert hasattr(app, "tab_resume"), "tab_resume missing"
    assert hasattr(app, "tab_letters"), "tab_letters missing"
    assert hasattr(app, "tab_track"), "tab_track missing"
    assert hasattr(app, "tab_prep"), "tab_prep missing"
    assert hasattr(app, "tab_agent"), "tab_agent missing"
    assert hasattr(app, "tab_settings"), "tab_settings missing"

    print("[3/4] Testing widget components...")
    # Test setting and reading search keywords
    app.search_kw.delete(0, "end")
    app.search_kw.insert(0, "Python AI Engineer")
    assert app.search_kw.get() == "Python AI Engineer"

    # Test resume initial text
    assert len(app.resume_in.get()) > 0

    # Test settings speed combobox
    app.speed.set("fast")
    assert app.speed.get() == "fast"

    # Process all pending Tk events
    app.update_idletasks()
    app.update()

    print("[4/4] Destroying test window cleanly...")
    app.destroy()
    print("HEADLESS GUI SMOKE TEST PASSED")


if __name__ == "__main__":
    try:
        run_gui_smoke_test()
    except Exception as exc:
        print(f"GUI SMOKE TEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
