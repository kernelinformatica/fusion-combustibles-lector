import os
import sys
import argparse
import time
from datetime import datetime

try:
    import clr  # pythonnet
except ImportError:
    raise ImportError("pythonnet debe estar instalado en el entorno. Instala con: pip install pythonnet")

class FusionBridge:
    def __init__(self, dll_path):
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"No se encuentra la DLL en {dll_path}")
        # Usar AddReference solo si está disponible
        if hasattr(clr, 'AddReference'):
            clr.AddReference(dll_path)
        else:
            raise ImportError("No se encontró 'AddReference' en clr. Actualiza pythonnet >= 3.x y elimina cualquier archivo clr.py local.")
        import importlib
        fusion_mod = importlib.import_module('FusionClass')
        self.Fusion = getattr(fusion_mod, 'Fusion')
        self.FusionSale = getattr(fusion_mod, 'FusionSale')
        self.fusion = self.Fusion()

    def conectar(self, ip):
        self.fusion.Connection(ip)
        time.sleep(2)

    def leer_producto(self, grado):
        nombre_temp = ""
        exito, nombre_res = self.fusion.GetGrade(grado, nombre_temp)
        if exito:
            return nombre_res
        else:
            return None

    def listar_metodos(self):
        print("\n--- Métodos públicos de Fusion ---")
        for method in dir(self.fusion):
            if not method.startswith('_'):
                print(method)
        print("--- Fin de métodos ---\n")

    def obtener_venta(self, hose_id, sale_number=None):
        #self.imprimir_firma_getsale()
        sale_data = self.FusionSale()
        # Si se pasa sale_number, setearlo en el objeto sale_data antes de llamar a GetSale
        if sale_number is not None:
            if hasattr(sale_data, 'SaleNumber'):
                sale_data.SaleNumber = sale_number
        exito = self.fusion.GetSale(hose_id, sale_data)
        if exito:
            try:
                venta = {
                    'venta_id': sale_data.GetSaleID(),
                    'surtidor_id': sale_data.GetPumpNr(),
                    'pump_id': sale_data.GetPumpNr(),  # Agregado pump_id
                    'pico_id': sale_data.GetHoseNr(),
                    'producto_id': sale_data.GetGradeNr(),
                    'volumen': sale_data.GetVolume(),
                    'importe': sale_data.GetAmount(),
                    'precio_unitario': sale_data.GetPPU(),
                    'tipo_pago': sale_data.GetPaymentType(),
                    'fecha': sale_data.GetDateOfTransaction(),
                    'hora': sale_data.GetTimeOfTransaction(),
                    'volumen_inicial': sale_data.GetInitialVolume(),
                    'volumen_final': sale_data.GetFinalVolume(),
                    'nivel_precio': sale_data.GetPriceLevel(),
                    'tipo_transaccion': sale_data.GetTypeOfTransaction(),
                    'importe_preset': sale_data.GetPresetAmount(),
                    'turno_id': sale_data.GetShiftID(),
                    'producto': sale_data.GetGradeNr(),
                    'nombre_producto': self.leer_producto(sale_data.GetGradeNr()),
                }
            except Exception as e:
                venta = {'error': f'Error extrayendo datos de la venta: {e}'}
            return venta
        else:
            return None

    def obtener_picos(self):
        hoses = []
        try:
            config = self.fusion.GetConfig()
            print("Atributos de FusionForecourt (GetConfig()):", dir(config))
            # Aquí puedes ajustar el nombre correcto según lo que imprima
            # for pump in config.Pumps:
            #     for hose in pump.Hoses:
            #         hoses.append(hose.HoseNr)
        except Exception as e:
            print(f"Error obteniendo hoses: {e}")
        return hoses

    def obtener_ventas_del_dia(self, hose_id, fecha_dia):
        print(":: Obteniendo ventas del día ", fecha_dia, ", aguarde un momento por favor...")
        if isinstance(fecha_dia, str):
            fecha_dia = datetime.strptime(fecha_dia, "%Y-%m-%d").date()
        ventas = []
        ventas_ids = set()  # Para evitar duplicados, solo por venta_id (SaleID)
        hose_ids = []
        try:
            """
            # esto no deveulve bien las coss lo comento temporalmente para seguir adelante, pero es importante entender la estructura real de la config y como acceder a bombas y picos reales
            config = self.fusion.GetConfig()
            n_bombas = getattr(config, 'm_iPumps', 0)
            o_pump = getattr(config, 'o_Pump', None)
            if o_pump is not None and n_bombas:
                # Recorrer todas las bombas y sus picos reales
                for idx in range(n_bombas):
                    pump = o_pump[idx]
                    pump_id = getattr(pump, 'm_iPumpNr', None)
                    hoses = getattr(pump, 'o_Hose', None)
                    n_hoses = getattr(pump, 'm_iHoses', 0)
                    if hoses is not None and n_hoses:
                        for hidx in range(n_hoses):
                            hose = hoses[hidx]
                            hose_id_real = getattr(hose, 'm_iHoseNr', None)
                            if pump_id is not None and hose_id_real is not None:
                                hose_ids.append((pump_id, hose_id_real))
            else:
                # Fallback si no se puede obtener la config real
                hose_ids = [(None, i) for i in range(1, 22)]
            """
            hose_ids = [(None, i) for i in range(1, 22)]
        except Exception as e:
            print(f"Error obteniendo configuración de bombas y picos: {e}")
            hose_ids = [(None, i) for i in range(1, 22)]

        if hose_id and int(hose_id) > 0:
            hose_ids = [hid for hid in hose_ids if hid[1] == int(hose_id)]
        if not hose_ids:
            hose_ids = [(None, int(hose_id))] if hose_id and int(hose_id) > 0 else [(None, i) for i in range(1, 22)]

        for pump_id, pico_id in hose_ids:
            sale_data = self.FusionSale()
            exito = self.fusion.GetSale(int(pico_id), sale_data)
            if not exito:
                continue
            try:
                ultimo_sale_number = int(sale_data.GetSaleID())
            except Exception:
                ultimo_sale_number = 0
            if not ultimo_sale_number:
                continue
            for sale_number in range(int(ultimo_sale_number), 0, -1):
                venta = self.obtener_venta(int(pico_id), int(sale_number))
                if venta:
                    fecha_venta = venta.get('fecha')
                    fecha_venta_dt = None
                    if fecha_venta:
                        if isinstance(fecha_venta, str) and len(fecha_venta) == 8 and fecha_venta.isdigit():
                            try:
                                fecha_venta_dt = datetime.strptime(fecha_venta, "%Y%m%d").date()
                            except Exception:
                                fecha_venta_dt = None
                        else:
                            try:
                                fecha_venta_dt = datetime.strptime(str(fecha_venta), "%Y-%m-%d").date()
                            except Exception:
                                try:
                                    fecha_venta_dt = datetime.strptime(str(fecha_venta)[:10], "%Y-%m-%d").date()
                                except Exception:
                                    fecha_venta_dt = None
                        if fecha_venta_dt and fecha_venta_dt != fecha_dia:
                            continue
                    clave = venta.get('venta_id')
                    if clave in ventas_ids:
                        continue
                    ventas_ids.add(clave)
                    if pump_id is not None:
                        venta['surtidor_id'] = pump_id
                        venta['pump_id'] = pump_id
                    if pico_id is not None:
                        venta['pico_id'] = pico_id
                    ventas.append(venta)

        self.procesar_ventas_recibidas(ventas)


    def procesar_ventas_recibidas(self, ventas):
        print(f":: Procesando {len(ventas)} ventas recibidas, aguarde un momento por favor...")
        for venta in ventas:
            print(f"Venta ID: {venta.get('venta_id')}, Pico ID: {venta.get('pico_id')}, Fecha: {venta.get('fecha')}, Importe: {venta.get('importe')}")



    def imprimir_firma_getsale(self):
        print("\n--- Firma de Fusion.GetSale ---")
        print(self.fusion.GetSale.__doc__)
        print("--- Fin de firma ---\n")

    def listar_productos(self, grados=8):
        #--accion listar_productos --ip 200.85.107.15
        productos = []
        for grado in range(1, int(grados) + 1):
            nombre = self.leer_producto(grado)
            if nombre:
                productos.append((grado, nombre))
        return productos

    def obtener_ultima_venta(self, hose_id=None):
        try:
            fusion_sale = self.FusionSale()
            if hose_id:
                exito = self.fusion.GetLastSale(int(hose_id), fusion_sale)
            else:
                exito = self.fusion.GetLastSale(fusion_sale)
            if not exito:
                return {"error": "No se encontró una venta."}
            # Extraer todos los campos relevantes según la documentación
            venta = {
                "sale_id": fusion_sale.GetSaleID(),
                "pump_id": fusion_sale.GetPumpNr(),
                "hose_id": fusion_sale.GetHoseNr(),
                "grade_id": fusion_sale.GetGradeNr(),
                "volume": fusion_sale.GetVolume(),
                "amount": fusion_sale.GetAmount(),
                "ppu": fusion_sale.GetPPU(),
                "payment_type": fusion_sale.GetPaymentType(),
                "fecha": fusion_sale.GetDateOfTransaction(),
                "hora": fusion_sale.GetTimeOfTransaction(),
                # Puedes agregar más campos si lo necesitas
            }
            return venta
        except Exception as e:
            return {"error": f"Error obteniendo la última venta: {e}"}

    def diagnostico_picos_bombas(self):
        """
        Diagnóstico: muestra cuántas bombas y picos detecta la DLL y sus IDs reales.
        También imprime los atributos y el valor de config para analizar la estructura real.
        """
        try:
            config = self.fusion.GetConfig()
            print("Tipo de config:", type(config))
            print("Atributos disponibles en config:", dir(config))
            print("Valor de config:", config)
            # Nuevo diagnóstico para m_iPumps y o_Pump
            n_bombas = getattr(config, 'm_iPumps', None)
            print(f"Cantidad de bombas (m_iPumps): {n_bombas}")
            o_pump = getattr(config, 'o_Pump', None)
            print(f"Tipo de o_Pump: {type(o_pump)}")
            if o_pump is not None:
                try:
                    print(f"Longitud de o_Pump: {len(o_pump)}")
                except Exception:
                    print("o_Pump no es iterable o no tiene longitud.")
                # Diagnóstico del primer elemento
                try:
                    primer_pump = o_pump[0]
                    print("Atributos del primer elemento de o_Pump:", dir(primer_pump))
                except Exception:
                    print("No se pudo acceder al primer elemento de o_Pump.")
            else:
                print("o_Pump es None.")
        except Exception as e:
            print(f"Error en diagnóstico de picos y bombas: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bridge para FusionClass.dll - Consulta de surtidores")
    parser.add_argument('--dll', type=str, default=os.path.abspath(os.path.join(os.path.dirname(__file__), "FusionClass.dll")), help='Ruta a FusionClass.dll')
    parser.add_argument('--ip', type=str, required=False, help='IP del controlador Fusion')
    parser.add_argument('--hose_id', type=int, help='ID del pico/surtidor para consultar venta')
    parser.add_argument('--sale_number', type=int, default=0, help='Número de venta a consultar (0=última venta)')
    parser.add_argument('--accion', type=str, required=True, choices=['leer_producto', 'consultar_metodos', 'ultima_venta', 'venta_especifica', 'ventas_dia', 'listar_productos'], help='Acción a realizar')
    parser.add_argument('--grado', type=int, help='Número de grado/producto a consultar (1-8)')
    parser.add_argument('--fecha_dia', type=str, help='Fecha para filtrar ventas (YYYY-MM-DD)')
    args = parser.parse_args()

    try:
        bridge = FusionBridge(args.dll)
        if args.accion == 'consultar_metodos':
            bridge.listar_metodos()
            bridge.imprimir_firma_getsale()
            sys.exit(0)
        if args.accion == 'leer_producto':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            if args.grado is None:
                print("Debe indicar --grado para leer un producto.")
                sys.exit(1)
            nombre = bridge.leer_producto(args.grado)
            if nombre:
                print(f"Producto en grado {args.grado}: {nombre}")
            else:
                print(f"No hay producto configurado en grado {args.grado}.")
        if args.accion == 'ultima_venta':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            if args.hose_id is None:
                print("Debe indicar --hose_id para consultar la última venta.")
                sys.exit(1)
            venta = bridge.obtener_venta(args.hose_id, 0)
            if venta:
                print("Datos de la última venta:")
                for k, v in venta.items():
                    print(f"{k}: {v}")
            else:
                print("No se pudo obtener la última venta para el pico indicado.")
        if args.accion == 'venta_especifica':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            if args.hose_id is None or args.sale_number is None:
                print("Debe indicar --hose_id y --sale_number para consultar una venta específica.")
                sys.exit(1)
            venta = bridge.obtener_venta(args.hose_id, args.sale_number)
            if venta:
                print(f"Datos de la venta sale_number={args.sale_number}:")
                for k, v in venta.items():
                    print(f"{k}: {v}")
            else:
                print("No se pudo obtener la venta para el pico y número indicados.")
        if args.accion == 'ventas_dia':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            if args.hose_id is None or not args.fecha_dia:
                print("Debe indicar --hose_id y --fecha_dia para consultar ventas del día.")
                sys.exit(1)
            ventas = bridge.obtener_ventas_del_dia(args.hose_id, args.fecha_dia)
            if ventas:
                print(f"Ventas del día {args.fecha_dia} para hose_id={args.hose_id}:")
                for venta in ventas:
                    print(venta)
            else:
                print("No se encontraron ventas para ese día y pico.")
        if args.accion == 'listar_productos':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            productos = bridge.listar_productos()
            if productos:
                print("Productos configurados:")
                for grado, nombre in productos:
                    print(f"Grado {grado}: {nombre}")
            else:
                print("No se encontraron productos configurados.")
            sys.exit(0)
        if args.accion == 'diagnostico_picos_bombas':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            bridge.diagnostico_picos_bombas()
            sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
