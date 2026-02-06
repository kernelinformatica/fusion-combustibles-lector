import clr
import os
import time

# 1. Referenciar la DLL
# Ajusta la ruta a la ubicación real de FusionClass.dll
dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "FusionClass.dll"))
if not os.path.exists(dll_path):
    print(f"ERROR: No se encuentra la DLL en {dll_path}")
    exit()

try:
    clr.AddReference(dll_path)
    try:
        from FusionClass import Fusion
        print("DLL cargada correctamente con 'from FusionClass import Fusion'.")
    except ImportError:
        try:
            from Fusion import Fusion
            print("DLL cargada correctamente con 'from Fusion import Fusion'.")
        except ImportError:
            # Acceso alternativo usando getattr
            import sys
            fusion_mod = sys.modules.get('FusionClass')
            if fusion_mod:
                Fusion = getattr(fusion_mod, 'Fusion', None)
                if Fusion:
                    print("DLL cargada correctamente usando getattr.")
                else:
                    print("No se pudo acceder a la clase Fusion.")
                    exit()
            else:
                print("No se pudo importar FusionClass ni Fusion.")
                exit()
except Exception as e:
    print(f"Error al cargar la DLL o importar Fusion: {e}")
    print("Asegúrate de tener instalado 'Visual Studio 2013 Redistributable' (Requisito pág 6)")
    exit()

# 2. Intentar conexión
c_fusion = Fusion()
ip_test = "200.85.107.15"

print(f"Conectando a Fusion en {ip_test}...")
c_fusion.Connection(ip_test)

# Esperar un momento para que la conexión se establezca
time.sleep(2)

# 3. Probar lectura de Grados (Productos)
print("\n--- Listado de Productos en Fusion ---")
for i in range(1, 9):
    nombre_temp = ""
    # El método GetGrade devuelve una tupla en PythonNet (Booleano, String)
    exito, nombre_res = c_fusion.GetGrade(i, nombre_temp)
    if exito:
        print(f"ID {i}: {nombre_res}")
    else:
        print(f"ID {i}: No configurado")

print("\nPrueba finalizada. Si ves los nombres de productos arriba, ¡estás conectado!")
