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
        sale_data = self.FusionSale()
        # Si se pasa sale_number, setearlo en el objeto sale_data antes de llamar a GetSale
        if sale_number is not None:
            # Si existe el setter, úsalo
            if hasattr(sale_data, 'SaleNumber'):
                sale_data.SaleNumber = sale_number
            elif hasattr(sale_data, 'SetSaleNumber'):
                sale_data.SetSaleNumber(sale_number)
        exito = self.fusion.GetSale(hose_id, sale_data)
        if exito:
            # Usar getters si existen, si no, fallback a atributo
            try:
                sale_number_val = sale_data.GetSaleNumber()
            except AttributeError:
                sale_number_val = getattr(sale_data, 'SaleNumber', None)
            try:
                litros = sale_data.GetVolume()
            except AttributeError:
                litros = getattr(sale_data, 'Volume', None)
            try:
                monto = sale_data.GetAmount()
            except AttributeError:
                monto = getattr(sale_data, 'Amount', None)
            try:
                producto = sale_data.GetProduct()
            except AttributeError:
                producto = getattr(sale_data, 'Product', None)
            try:
                fecha = sale_data.GetDateOfTransaction()
            except AttributeError:
                fecha = getattr(sale_data, 'DateTime', None)
            return {
                'litros': litros,
                'monto': monto,
                'producto': producto,
                'fecha': fecha,
                'sale_number': sale_number_val,
                'hose_id': hose_id
            }
        else:
            return None

    def obtener_ventas_del_dia(self, hose_id, fecha_dia):
        self.imprimir_firma_getsale()
        if isinstance(fecha_dia, str):
            fecha_dia = datetime.strptime(fecha_dia, "%Y-%m-%d").date()
        ventas = []
        sale_data = self.FusionSale()
        exito = self.fusion.GetSale(hose_id, sale_data)
        if not exito:
            return ventas
        try:
            ultimo_sale_number = sale_data.GetSaleNumber()
        except AttributeError:
            ultimo_sale_number = getattr(sale_data, 'SaleNumber', None)
        if not ultimo_sale_number:
            return ventas
        for sale_number in range(ultimo_sale_number, 0, -1):
            venta = self.obtener_venta(hose_id, sale_number)
            if not venta:
                continue
            try:
                fecha_venta_date = datetime.strptime(str(venta['fecha'])[:10], "%Y-%m-%d").date()
            except Exception:
                continue
            if fecha_venta_date == fecha_dia:
                ventas.append(venta)
            elif fecha_venta_date < fecha_dia:
                break
        return ventas

    def imprimir_firma_getsale(self):
        print("\n--- Firma de Fusion.GetSale ---")
        print(self.fusion.GetSale.__doc__)
        print("--- Fin de firma ---\n")
    # Aquí puedes agregar más métodos para otras operaciones

def main():
    parser = argparse.ArgumentParser(description="Bridge para FusionClass.dll - Consulta de surtidores")
    parser.add_argument('--dll', type=str, default=os.path.abspath(os.path.join(os.path.dirname(__file__), "FusionClass.dll")), help='Ruta a FusionClass.dll')
    parser.add_argument('--ip', type=str, required=False, help='IP del controlador Fusion')
    parser.add_argument('--hose_id', type=int, help='ID del pico/surtidor para consultar venta')
    parser.add_argument('--sale_number', type=int, default=0, help='Número de venta a consultar (0=última venta)')
    parser.add_argument('--accion', type=str, required=True, choices=['leer_producto', 'consultar_metodos', 'ultima_venta', 'venta_especifica', 'ventas_dia'], help='Acción a realizar')
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
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
