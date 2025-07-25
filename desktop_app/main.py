import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import logging
import flet as ft
from app.core.config import APP_NAME
from desktop_app.pages.welcome import WelcomePage
from desktop_app.pages.models import ModelManagerPage
from desktop_app.utils.autostart import enable_autostart


CUSTOM_FONT = "Labil Grotesk"
CUSTOM_FONT_FILE = "/fonts/LabilGrotesk.ttf"

logger = logging.getLogger(f"{APP_NAME}.desktop_app")

class AppState:
    def __init__(self):
        # The Flet app no longer controls the server's lifecycle directly.
        # It assumes the server is managed by the background_runner.
        self.page = None

app_state = AppState()

async def main(page: ft.Page):
    page.title = APP_NAME
    page.window.max_width = 520
    page.window.max_height = 730
    page.window_resizable = True
    page.window_always_on_top = False
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.fonts = {CUSTOM_FONT: str(CUSTOM_FONT_FILE)}
    page.theme = ft.Theme(font_family=CUSTOM_FONT)

    app_state.page = page

    # Check for arguments to determine initial page
    initial_route = "/welcome"
    if "--settings" in sys.argv:
        initial_route = "/settings" # You'll need to create a SettingsPage
    elif "--models" in sys.argv:
        initial_route = "/models"

    async def navigate_to_route(route):
        page.views.clear()
        if route == "/settings":
            # Assuming you'll create a SettingsPage
            # settings_page = await SettingsPage(page, app_state)
            # page.views.append(settings_page)
            # For now, just show model manager if settings isn't ready
            logger.info("Navigating to Settings (placeholder).")
            model_page = await ModelManagerPage(page, app_state)
            page.views.append(model_page)
        elif route == "/models":
            logger.info("Navigating to Model Manager.")
            model_page = await ModelManagerPage(page, app_state)
            page.views.append(model_page)
        else: # Default to welcome
            logger.info("Showing welcome page.")
            # Corrected: Pass the function and its argument to page.run_task
            welcome_view = await WelcomePage(on_next=lambda e: page.run_task(navigate_to_route, "/models"))
            page.views.append(welcome_view)
        page.update()

    if initial_route == "/welcome":
        # If no specific argument, show welcome and then proceed
        # Corrected: Pass the function and its argument to page.run_task
        welcome_view = await WelcomePage(on_next=lambda e: page.run_task(navigate_to_route, "/models"))
        page.views.append(welcome_view)
        page.update()
    else:
        await navigate_to_route(initial_route)

    # Enable autostart only if it's the first run or explicitly chosen by the user
    # This call should ideally be moved to a settings page where the user can toggle it.
    # If placed here, it will re-enable autostart every time the app starts.
    # For initial setup, it's fine, but consider user control.
    enable_autostart()

if __name__ == "__main__":
    ft.app(target=main)