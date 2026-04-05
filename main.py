import os
# PARCHE DE COMPATIBILIDAD PARA WINDOWS
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
os.environ['KIVY_WINDOW'] = 'sdl2'

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from kivymd.toast import toast
from kivy.storage.jsonstore import JsonStore
import requests

Window.size = (360, 640)

class LoginScreen(MDScreen):
    pass

class DashboardScreen(MDScreen):
    pass

KV = '''
MDScreenManager:
    LoginScreen:
    DashboardScreen:

<LoginScreen>:
    name: "login"
    MDBoxLayout:
        orientation: "vertical"
        padding: "40dp"
        spacing: "30dp"
        
        MDLabel:
            text: "MellyTech\\nDashboard"
            halign: "center"
            font_style: "H3"
            theme_text_color: "Primary"
            bold: True

        MDTextField:
            id: input_id
            hint_text: "ID de Sucursal (ej. MT-7742)"
            mode: "rectangle"
            icon_left: "store"

        MDRaisedButton:
            text: "VINCULAR MI FARMACIA"
            pos_hint: {"center_x": .5}
            elevation: 2
            on_release: app.vincular_dispositivo(input_id.text)
            
        Widget:

<DashboardScreen>:
    name: "dashboard"
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Panel de MellyTech"
            elevation: 3
            right_action_items: [["refresh", lambda x: app.cargar_desde_nube()], ["logout", lambda x: app.cerrar_sesion()]]

        MDBottomNavigation:
            
            # --- PESTAÑA 1: RESUMEN ---
            MDBottomNavigationItem:
                name: 'screen_resumen'
                text: 'Resumen'
                icon: 'view-dashboard'
                ScrollView:
                    MDBoxLayout:
                        orientation: "vertical"
                        padding: "20dp"
                        spacing: "20dp"
                        size_hint_y: None
                        height: self.minimum_height

                        MDCard:
                            orientation: "vertical"
                            padding: "16dp"
                            size_hint_y: None
                            height: "100dp"
                            elevation: 4
                            radius: [15, 15, 15, 15]
                            MDLabel:
                                text: "INGRESOS HOY"
                                font_style: "Subtitle2"
                                theme_text_color: "Custom"
                                text_color: 0.3, 0.8, 0.4, 1
                            MDLabel:
                                id: lbl_ventas
                                text: "$ 0.00"
                                halign: "right"
                                font_style: "H4"
                                theme_text_color: "Custom"
                                text_color: 0.3, 0.8, 0.4, 1

                        MDCard:
                            orientation: "vertical"
                            padding: "16dp"
                            size_hint_y: None
                            height: "100dp"
                            elevation: 4
                            radius: [15, 15, 15, 15]
                            MDLabel:
                                text: "SALIDAS / GASTOS"
                                font_style: "Subtitle2"
                                theme_text_color: "Custom"
                                text_color: 0.9, 0.3, 0.3, 1
                            MDLabel:
                                id: lbl_salidas
                                text: "$ 0.00"
                                halign: "right"
                                font_style: "H4"
                                theme_text_color: "Custom"
                                text_color: 0.9, 0.3, 0.3, 1

                        MDCard:
                            orientation: "vertical"
                            padding: "16dp"
                            size_hint_y: None
                            height: "100dp"
                            elevation: 4
                            radius: [15, 15, 15, 15]
                            md_bg_color: app.theme_cls.primary_color
                            MDLabel:
                                text: "TOTAL EN CAJA"
                                font_style: "Subtitle2"
                                theme_text_color: "Custom"
                                text_color: 1, 1, 1, 1
                            MDLabel:
                                id: lbl_total_caja
                                text: "$ 0.00"
                                halign: "right"
                                font_style: "H4"
                                theme_text_color: "Custom"
                                text_color: 1, 1, 1, 1

            # --- PESTAÑA 2: VENTAS HOY ---
            MDBottomNavigationItem:
                name: 'screen_ventas_hoy'
                text: 'Ventas Hoy'
                icon: 'cart-check'
                ScrollView:
                    MDList:
                        id: lista_ventas_hoy

            # --- PESTAÑA 3: INVENTARIO ---
            MDBottomNavigationItem:
                name: 'screen_inventario'
                text: 'Catálogo'
                icon: 'format-list-bulleted'
                ScrollView:
                    MDList:
                        id: lista_inventario

            # --- PESTAÑA 4: ALERTAS ---
            MDBottomNavigationItem:
                name: 'screen_alertas'
                text: 'Alertas'
                icon: 'bell-alert'
                ScrollView:
                    MDList:
                        id: lista_alertas
'''

class MellyTechMobile(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.store = JsonStore('config_melly.json')
        return Builder.load_string(KV)

    def on_start(self):
        if self.store.exists('sucursal'):
            self.root.current = "dashboard"
            self.cargar_desde_nube()

    def vincular_dispositivo(self, sucursal_id):
        if not sucursal_id.strip():
            toast("ID requerido")
            return
        self.store.put('sucursal', id=sucursal_id.strip())
        self.root.current = "dashboard"
        self.cargar_desde_nube()

    def cargar_desde_nube(self):
        if not self.store.exists('sucursal'): return
        id_actual = self.store.get('sucursal')['id']
        url = f"https://mellyfarm-18bc3-default-rtdb.firebaseio.com/sucursales/{id_actual}.json"
        
        try:
            r = requests.get(url, timeout=5)
            datos = r.json()
            if datos:
                dash = self.root.get_screen('dashboard')
                fin = datos.get('finanzas', {})
                dash.ids.lbl_ventas.text = f"${fin.get('ventas', 0):,.2f}"
                dash.ids.lbl_salidas.text = f"${fin.get('salidas', 0):,.2f}"
                dash.ids.lbl_total_caja.text = f"${fin.get('total_caja', 0):,.2f}"
                
                # --- CARGAR VENTAS HOY CON DETECTOR DE VACÍO ---
                ventas_del_dia = datos.get('vendidos_hoy', [])
                dash.ids.lista_ventas_hoy.clear_widgets()
                
                if len(ventas_del_dia) == 0:
                    # Si Firebase no mandó nada, mostramos este mensaje
                    item_vacio = TwoLineIconListItem(text="No hay ventas registradas en la nube", secondary_text="Ve al POS, cobra un producto y actualiza aquí.")
                    item_vacio.add_widget(IconLeftWidget(icon="information-outline"))
                    dash.ids.lista_ventas_hoy.add_widget(item_vacio)
                else:
                    # Si Firebase sí mandó productos, los mostramos
                    for v in ventas_del_dia:
                        item = TwoLineIconListItem(text=v['nombre'], secondary_text=f"Vendidos: {v['cant']} | Ingreso: ${v['subtotal']:.2f}")
                        item.add_widget(IconLeftWidget(icon="cart-check"))
                        dash.ids.lista_ventas_hoy.add_widget(item)

                # CARGAR INVENTARIO
                dash.ids.lista_inventario.clear_widgets()
                for prod in datos.get('inventario', []):
                    item = TwoLineIconListItem(text=prod['nombre'], secondary_text=f"Stock: {prod['stock']} | ${prod['precio']:.2f}")
                    item.add_widget(IconLeftWidget(icon="medical-bag"))
                    dash.ids.lista_inventario.add_widget(item)

                # CARGAR ALERTAS
                dash.ids.lista_alertas.clear_widgets()
                for a in datos.get('alertas', []):
                    dash.ids.lista_alertas.add_widget(TwoLineIconListItem(text=a['nombre'], secondary_text=a['mensaje']))
                
                toast("Sincronizado ✅")
        except:
            toast("Error de conexión ❌")

    def cerrar_sesion(self):
        self.store.delete('sucursal')
        self.root.current = "login"

if __name__ == "__main__":
    MellyTechMobile().run()