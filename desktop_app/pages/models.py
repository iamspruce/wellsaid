import asyncio
import flet as ft
import logging
from pathlib import Path

from app.core.config import APP_NAME

from desktop_app.utils.model_manager import ( 
    list_available_models,
    download_model,
    delete_model,
)

logger = logging.getLogger(f"{APP_NAME}.desktop_app.model_manager")


async def ModelManagerPage(page: ft.Page, app_state):
    status_text = ft.Text("")

    async def handle_download(model_key: str, button: ft.ElevatedButton):
        button.disabled = True
        button.text = "Downloading..."
        status_text.value = f"⬇️ Downloading '{model_key}'..."
        page.update()
        try:
            await download_model(model_key)
            status_text.value = f"✅ '{model_key}' downloaded successfully."
        except Exception as e:
            logger.error(f"Failed to download model {model_key}: {e}", exc_info=True)
            status_text.value = f"❌ Download failed: {e}"
        finally:
            button.disabled = False
            await refresh_model_list()
            page.update()

    async def handle_delete(model_key: str, button: ft.ElevatedButton):
        button.disabled = True
        button.text = "Deleting..."
        status_text.value = f"🗑️ Deleting '{model_key}'..."
        page.update()
        try:
            deleted = delete_model(model_key)
            if deleted:
                status_text.value = f"🗑️ '{model_key}' deleted."
            else:
                status_text.value = f"Model '{model_key}' was not found."
        except Exception as e:
            logger.error(f"Failed to delete model {model_key}: {e}", exc_info=True)
            status_text.value = f"❌ Delete failed: {e}"
        finally:
            button.disabled = False
            await refresh_model_list()
            page.update()

    async def refresh_model_list():
        model_list_column.controls.clear()

        for model_info in list_available_models():
            model_key = model_info["key"]
            name = model_info["name"]
            purpose = model_info["purpose"]
            downloaded = model_info["downloaded"]
            example = model_info.get("example", {})
            input_text = example.get("input", "")
            output_text = example.get("output", "")

            example_text = (
                f"Example:\n  ➤ Input: {input_text}\n  ➤ Output: {output_text}"
                if input_text and output_text
                else ""
            )

            action_button = ft.ElevatedButton(
                text="Delete" if downloaded else "Download",
                bgcolor=ft.Colors.RED_100 if downloaded else ft.Colors.GREEN_100,
                color=ft.Colors.BLACK,
                on_click=lambda e, m_key=model_key: (
                    asyncio.create_task(handle_delete(m_key, e.control))
                    if downloaded else
                    asyncio.create_task(handle_download(m_key, e.control))
                )
            )

            card = ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(name, size=18, weight=ft.FontWeight.BOLD),
                                ft.Text(purpose, size=14),
                                ft.Text(example_text, size=12, color=ft.Colors.GREY_700, selectable=True),
                            ], spacing=5),
                            expand=True
                        ),
                        ft.Container(
                            content=action_button,
                            alignment=ft.alignment.center_right,
                            margin=ft.margin.only(left=10)
                        ),
                    ])
                )
            )

            model_list_column.controls.append(card)

        page.update()

    model_list_column = ft.Column(spacing=15)

    scrollable_model_list = ft.Container(
        content=model_list_column,
        expand=True,        
    )

    view = ft.View(
        route="/models",
        controls=[
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column([
                    ft.Image(src="/images/logo.png", width=100, height=100),
                    ft.Text("Manage your models", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("Add and remove only what you intend to use.", size=16, text_align=ft.TextAlign.CENTER),
                    ft.Divider(),
                    scrollable_model_list,
                    ft.Divider(),
                    status_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.START,
        scroll=ft.ScrollMode.AUTO
    )

    await refresh_model_list()
    return view
