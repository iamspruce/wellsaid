import flet as ft
from app.core.config import APP_NAME



async def WelcomePage(on_next):
    return ft.View(
        route="/welcome",
        controls=[
            ft.Container(
                padding=50,
                expand=True,
                content=ft.Column(
                    [
                        ft.Text(
                            f"Say it well, Say it better - {APP_NAME}",
                            size=48,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            font_family="Labil Grotesk"  
                        ),
                        ft.Text(
                            "Let's get you started with setting up your free offline grammar checker.",
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                            font_family="Labil Grotesk"
                        ),
                        ft.CupertinoFilledButton(
                            content=ft.Text("Next"),
                            opacity_on_click=0.3,
                            on_click=on_next,
                            width=200,
                            
                        ),

                        ft.Container(expand=True),  # Pushes image to bottom
                        ft.Container(
                            alignment=ft.alignment.bottom_right,
                            content=ft.Image(
                                src="/images/logo_welcome.png",
                                width=220,
                                height=220,
                                fit=ft.ImageFit.CONTAIN
                            )
                        ),
                    ],
                    spacing=30,
                    expand=True,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        ]
    )
