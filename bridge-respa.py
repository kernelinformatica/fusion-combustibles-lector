import clr
import os
import sys
import argparse
import time

from datetime import datetime

class FusionBridge:
    def __init__(self, dll_path):
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"No se encuentra la DLL en {dll_path}")
        clr.AddReference(dll_path)
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
        self.imprimir_firma_getsale()
        sale_data = self.FusionSale()
        # Si se pasa sale_number, setearlo en el objeto sale_data antes de llamar a GetSale
        if sale_number is not None:
            if hasattr(sale_data, 'SaleNumber'):
                sale_data.SaleNumber = sale_number
        exito = self.fusion.GetSale(hose_id, sale_data)
        if exito:
            # Usar getters si existen, si no, fallback a atributo
            try:
                sale_number_val = sale_data.GetSaleID()
            except AttributeError:
                sale_number_val = getattr(sale_data, 'SaleId', 0)
            try:
                litros = sale_data.GetVolume()
            except AttributeError:
                litros = getattr(sale_data, 'Volume', 0)
            try:
                monto = sale_data.GetAmount()
            except AttributeError:
                monto = getattr(sale_data, 'Amount',0)
            # Intentar obtener el código de producto correctamente
            producto = 0
            try:
                producto = sale_data.GetProduct()
            except AttributeError:
                try:
                    producto = sale_data.GetGradeNr()
                except AttributeError:
                    producto = getattr(sale_data, 'Product', 0)
            # Obtener nombre del producto si es posible
            nombre_producto = self.leer_producto(producto) if producto else None
            try:
                fecha = sale_data.GetDateOfTransaction()
            except AttributeError:
                fecha = getattr(sale_data, 'DateTime', None)
            return {
                'litros': litros,
                'monto': monto,
                'producto': producto,
                'producto_nombre': nombre_producto,
                'fecha': fecha,
                'nro_comp': sale_number_val,
                'id_pico': hose_id
            }
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

        if isinstance(fecha_dia, str):
            fecha_dia = datetime.strptime(fecha_dia, "%Y-%m-%d").date()
        ventas = []
        hose_ids = [hose_id] if hose_id and hose_id > 0 else self.obtener_picos()
        for hid in hose_ids:
            sale_data = self.FusionSale()
            exito = self.fusion.GetSale(hid, sale_data)
            if not exito:
                continue
            try:
                ultimo_sale_number = sale_data.GetSaleID()
            except AttributeError:
                ultimo_sale_number = getattr(sale_data, 'SaleNumber', None)
            if not ultimo_sale_number:
                continue
            for sale_number in range(ultimo_sale_number, 0, -1):
                venta = self.obtener_venta(hid, sale_number)
                ventas.append({
                    'litros': venta.get('litros'),
                    'monto': venta.get('monto'),
                    'producto': venta.get('producto'),
                    'producto_nombre': venta.get('producto_nombre'),
                    'fecha': venta.get('fecha'),
                    'nro_comp': venta.get('nro_comp'),
                    'id_pico': venta.get('id_pico')
                })


        return ventas

    def imprimir_firma_getsale(self):
        print("\n--- Firma de Fusion.GetSale ---")
        print(self.fusion.GetSale.__doc__)
        print("--- Fin de firma ---\n")

    def listar_productos(self, grados=8):
        #--accion listar_productos --ip 200.85.107.15
        productos = []
        for grado in range(1, grados + 1):
            nombre = self.leer_producto(grado)
            if nombre:
                productos.append((grado, nombre))
        return productos

    def obtener_ventas_periodo(self, fecha_dia=None):
        """
        Obtiene ventas del día usando PeriodStatusRequest y PeriodSalesByGrade.
        Devuelve una lista de dicts con producto, volumen y monto.
        """
        import clr
        clr.AddReference("System")
        from System.Text import StringBuilder
        # 1. Obtener el PID del día actual
        period_info = StringBuilder()
        try:
            exito = self.fusion.PeriodStatusRequest(period_info)
        except Exception as e:
            print(f"Error al llamar PeriodStatusRequest: {e}")
            return []
        if not exito:
            print("No se pudo obtener el status del periodo.")
            return []
        period_info_str = period_info.ToString()
        print(f"period_info devuelto (raw): '{period_info_str}'")
        if not period_info_str.strip():
            print("period_info está vacío. Verifica la configuración del Fusion y que existan datos históricos.")
            return []
        # Buscar el PID del día en el string period_info
        pid = None
        for campo in period_info_str.split('|'):
            if campo.strip().startswith('DID') or campo.strip().startswith('DTI') or campo.strip().startswith('SSD'):
                pid = campo.split('=')[1].strip()
                print(f"PID detectado: {pid} (campo: {campo})")
                break
        if not pid:
            print("No se encontró el PID del día en period_info. Campos disponibles:")
            for campo in period_info_str.split('|'):
                print(campo)
            return []
        # 2. Llamar a PeriodSalesByGrade con PT='D' y PID
        ventas_info = StringBuilder()
        try:
            exito = self.fusion.PeriodSalesByGrade('D', pid, ventas_info)
        except Exception as e:
            print(f"Error al llamar PeriodSalesByGrade: {e}")
            return []
        if not exito:
            print("No se pudo obtener ventas del periodo.")
            return []
        ventas_info_str = ventas_info.ToString()
        # 3. Parsear ventas_info
        ventas = []
        campos = ventas_info_str.split('|')
        # Buscar cantidad de grades
        qt = 0
        for campo in campos:
            if campo.strip().startswith('QT'):
                try:
                    qt = int(campo.split('=')[1].strip())
                except Exception:
                    qt = 0
        # Extraer datos por cada grade
        for i in range(1, qt+1):
            grade = None
            money = None
            volume = None
            for campo in campos:
                if campo.strip().startswith(f'G{i}NR'):
                    grade = campo.split('=')[1].strip()
                if campo.strip().startswith(f'G{i}MN'):
                    money = campo.split('=')[1].strip()
                if campo.strip().startswith(f'G{i}VO'):
                    volume = campo.split('=')[1].strip()
            if grade:
                ventas.append({
                    'producto': grade,
                    'monto': money,
                    'litros': volume
                })
        return ventas
    # Aquí puedes agregar más métodos para otras operaciones

def main():
    parser = argparse.ArgumentParser(description="Bridge para FusionClass.dll - Consulta de surtidores")
    parser.add_argument('--dll', type=str, default=os.path.abspath(os.path.join(os.path.dirname(__file__), "FusionClass.dll")), help='Ruta a FusionClass.dll')
    parser.add_argument('--ip', type=str, required=False, help='IP del controlador Fusion')
    parser.add_argument('--hose_id', type=int, help='ID del pico/surtidor para consultar venta')
    parser.add_argument('--sale_number', type=int, default=0, help='Número de venta a consultar (0=última venta)')
    parser.add_argument('--accion', type=str, required=True, choices=['leer_producto', 'consultar_metodos', 'ultima_venta', 'venta_especifica', 'ventas_dia', 'listar_productos', 'ventas_periodo'], help='Acción a realizar')
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
        if args.accion == 'ventas_periodo':
            if not args.ip:
                print("Debe indicar --ip para conectar.")
                sys.exit(1)
            bridge.conectar(args.ip)
            ventas = bridge.obtener_ventas_periodo(args.fecha_dia)
            if ventas:
                print(f"Ventas del periodo para hose_id={args.hose_id}:")
                for venta in ventas:
                    print(venta)
            else:
                print("No se encontraron ventas para el periodo indicado.")
            sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
