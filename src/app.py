import flet as ft
import asyncio
from backend import GeminiLiveClient

async def main(page: ft.Page):
    page.title = "Gemini Live Asistan"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 750
    
    current_client = None
    gemini_buffer = ""
    current_gemini_bubble = None
    
    api_key_input = ft.TextField(
        label="Google API Key", 
        password=True, 
        can_reveal_password=True, 
        border_color="blue"
    )
    
    login_status_text = ft.Text("Hazır", color="grey", size=12)
    chat_status_text = ft.Text("Bağlanıyor...", color="white", size=12)

    chat_list_column = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.ALWAYS,
        auto_scroll=False
    )
    
    def create_chat_bubble(sender, message):
        is_gemini = sender == "Gemini"        
        bubble_color = "blueGrey900" if is_gemini else "teal800"
        alignment = ft.MainAxisAlignment.START if is_gemini else ft.MainAxisAlignment.END
        avatar = ft.Icon(ft.Icons.AUTO_AWESOME if is_gemini else ft.Icons.PERSON, color="white54")
        message_text = ft.Markdown(message, selectable=True)
        
        content = ft.Row(
            controls=[
                avatar if is_gemini else ft.Container(),
                ft.Container(
                    content=ft.Column([
                        ft.Text(sender, size=10, weight="bold", color="white54"),
                        message_text
                    ]),
                    bgcolor=bubble_color,
                    padding=15,
                    border_radius=15,
                    width=280,
                ),
                avatar if not is_gemini else ft.Container(),
            ],
            alignment=alignment,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        
        return content, message_text

    def on_message_received(sender, text):
        nonlocal gemini_buffer, current_gemini_bubble        
        if sender == "Gemini":
            gemini_buffer += text
            if current_gemini_bubble is None:
                bubble, message_ref = create_chat_bubble("Gemini", gemini_buffer)
                chat_list_column.controls.append(bubble)
                current_gemini_bubble = message_ref
            else:
                current_gemini_bubble.value = gemini_buffer
            
            try:
                page.update()
            except:
                pass
                
        else:
            if current_gemini_bubble is not None:
                gemini_buffer = ""
                current_gemini_bubble = None
            
            bubble, _ = create_chat_bubble(sender, text)
            chat_list_column.controls.append(bubble)
            page.update()

    def on_status_changed(msg):
        chat_status_text.value = msg
        try:
            chat_status_text.update()
        except:
            pass

    async def toggle_connection(e):
        nonlocal current_client
        
        if current_client and current_client.running:
            current_client.stop()
            chat_status_text.value = "Duraklatıldı."
            
            control_btn.text = "Devam Et"
            control_btn.icon = ft.Icons.PLAY_ARROW
            control_btn.bgcolor = "green"
            page.update()
            
        else:
            control_btn.text = "Durdur"
            control_btn.icon = ft.Icons.STOP
            control_btn.bgcolor = "red"
            chat_status_text.value = "Yeniden bağlanılıyor..."
            page.update()
            
            if current_client:
                await current_client.start_session()

    async def first_connect(e):
        nonlocal current_client
        if not api_key_input.value:
            api_key_input.error_text = "API Key gerekli"
            api_key_input.update()
            return
        
        api_key_input.error_text = None
        
        view_switcher.content = chat_view 
        page.update()
        
        current_client = GeminiLiveClient(
            api_key=api_key_input.value,
            on_message_callback=on_message_received,
            on_status_callback=on_status_changed
        )
        
        await current_client.start_session()
    
    connect_btn = ft.ElevatedButton("Sohbete Başla", on_click=first_connect, icon=ft.Icons.LOGIN)
    
    control_btn = ft.ElevatedButton(
        "Durdur", 
        on_click=toggle_connection, 
        icon=ft.Icons.STOP, 
        bgcolor="red",
        color="white"
    )

    login_view = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.HEADSET_MIC, size=80, color="blue"),
            ft.Text("Gemini Sesli Sohbet", size=24, weight="bold"),
            ft.Divider(height=20, color="transparent"),
            api_key_input,
            connect_btn,
            login_status_text
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30,
        alignment=ft.alignment.center
    )

    chat_view = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("Canlı Sohbet", size=16, weight="bold"),
                control_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            bgcolor="surfaceVariant",
        ),
        ft.Container(
            content=chat_list_column,
            padding=15,
            expand=True,
            bgcolor="black12"
        ),
        ft.Container(content=chat_status_text, padding=5, bgcolor="black26")
    ], spacing=0)

    view_switcher = ft.AnimatedSwitcher(
        content=login_view,
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=500,
        reverse_duration=500,
    )

    page.add(view_switcher)
    page.scroll = ft.ScrollMode.ALWAYS 

if __name__ == "__main__":
    ft.app(target=main)