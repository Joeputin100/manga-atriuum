from streamlit.testing.v1 import AppTest
import sys
sys.path.insert(0, ".")

def test_app_loads():
    at = AppTest.from_file('streamlit_app.py').run()
    # Check the title element
    assert at.title.value == "📚 Manga Lookup Tool"

def test_series_input():
    at = AppTest.from_file('streamlit_app.py').run()
    # The app loads the main form, check for text inputs
    text_inputs = at.text_input
    assert len(text_inputs) > 0  # Ensure at least one text input exists
    # Simulate input (adjust based on app structure)
    text_inputs[0].input('Naruto').run()
    # Check session state (may need adjustment)
    assert 'Naruto' in str(at.session_state)
