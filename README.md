# Fusion Combustibles Lector

**FusionClass**: Una librería Python que usa una DLL provista por Fusion para leer los despachos de combustibles de controladores Wayne Fusion.

## Descripción

Este paquete proporciona un puente Python para interactuar con controladores de surtidores Wayne Fusion utilizando `pythonnet` para cargar y comunicarse con la DLL de Wayne.

## Características

- ✅ Conexión a controladores Fusion mediante dirección IP
- ✅ Lectura del último despacho usando `GetLastSale` (página 22 de la documentación)
- ✅ Lectura del último despacho usando `GetLastSaleOnFusion` (página 29 de la documentación)
- ✅ Polling continuo para detectar nuevos despachos
- ✅ Manejo de errores y logging comprehensivo
- ✅ Context manager para gestión automática de conexiones

## Stack Propuesto (Python Bridge)

### Librerías Necesarias

- **pythonnet**: Permite cargar la DLL de Wayne y comunicarse con ella desde Python

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/kernelinformatica/fusion-combustibles-lector.git
cd fusion-combustibles-lector
```

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Asegurarse de tener acceso a la DLL de Wayne Fusion

## Uso Básico

### Ejemplo Simple

```python
from fusion_reader import FusionController

# Configuración
CONTROLLER_IP = "192.168.1.100"  # IP del controlador Fusion
DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"  # Ruta a la DLL de Wayne

# Crear instancia del controlador
controller = FusionController(
    controller_ip=CONTROLLER_IP,
    dll_path=DLL_PATH
)

# Conectar al controlador
if controller.connect():
    # Obtener el último despacho
    sale = controller.get_last_sale()
    
    if sale:
        print(f"Despacho: {sale}")
    
    # Desconectar
    controller.disconnect()
```

### Usando Context Manager

```python
from fusion_reader import FusionController

CONTROLLER_IP = "192.168.1.100"
DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"

# Conexión y desconexión automáticas
with FusionController(CONTROLLER_IP, DLL_PATH) as controller:
    sale = controller.get_last_sale()
    if sale:
        print(f"Despacho: {sale}")
```

### Polling Continuo

```python
from fusion_reader import FusionController

def on_new_sale(sale_data):
    """Función llamada cuando se detecta un nuevo despacho"""
    print(f"Nuevo despacho: {sale_data}")

CONTROLLER_IP = "192.168.1.100"
DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"

controller = FusionController(CONTROLLER_IP, DLL_PATH)

if controller.connect():
    # Polling cada 5 segundos
    controller.poll_for_new_sales(
        callback=on_new_sale,
        interval=5
    )
```

## Cómo Funciona la Lógica

1. **El script se conecta al IP del controlador Fusion**: Se establece una conexión TCP/IP con el controlador utilizando la DLL de Wayne.

2. **Consulta si hay ventas nuevas**: Utiliza los métodos proporcionados por la DLL:
   - `GetLastSale()`: Método documentado en la página 22
   - `GetLastSaleOnFusion()`: Método documentado en la página 29

## API Reference

### FusionController

Clase principal para interactuar con controladores Wayne Fusion.

#### Constructor

```python
FusionController(controller_ip: str, dll_path: str)
```

**Parámetros:**
- `controller_ip` (str): Dirección IP del controlador Fusion
- `dll_path` (str): Ruta al archivo DLL de Wayne

**Raises:**
- `DLLLoadError`: Si la DLL no puede ser cargada

#### Métodos

##### `connect() -> bool`

Establece conexión con el controlador Fusion.

**Returns:** `True` si la conexión es exitosa, `False` en caso contrario

**Raises:** `ConnectionError` si no se puede establecer la conexión

##### `disconnect()`

Desconecta del controlador Fusion.

##### `get_last_sale() -> Optional[Dict[str, Any]]`

Obtiene la última transacción de venta del controlador (página 22).

**Returns:** Diccionario con información de la venta, o `None` si no hay ventas

**Raises:** 
- `ConnectionError`: Si no está conectado
- `FusionControllerError`: Si la operación falla

##### `get_last_sale_on_fusion() -> Optional[Dict[str, Any]]`

Obtiene la última transacción usando el método GetLastSaleOnFusion (página 29).

**Returns:** Diccionario con información de la venta, o `None` si no hay ventas

**Raises:**
- `ConnectionError`: Si no está conectado
- `FusionControllerError`: Si la operación falla

##### `poll_for_new_sales(callback, interval: int = 5, use_fusion_method: bool = False)`

Realiza polling continuo para detectar nuevas ventas.

**Parámetros:**
- `callback`: Función a ejecutar cuando se detecta una nueva venta
- `interval` (int): Intervalo de polling en segundos (default: 5)
- `use_fusion_method` (bool): Si es `True`, usa `GetLastSaleOnFusion` en lugar de `GetLastSale`

**Nota:** Esta es una operación bloqueante. Considere ejecutarla en un thread o proceso separado.

## Estructura de Datos de Venta

El diccionario retornado por `get_last_sale()` o `get_last_sale_on_fusion()` puede contener las siguientes claves (dependiendo de la DLL):

- `TransactionId`: Identificador de la transacción
- `PumpNumber`: Número de surtidor/boquilla
- `Product`: Tipo de producto/combustible
- `Volume`: Volumen despachado
- `PricePerUnit`: Precio por unidad (litro/galón)
- `TotalAmount`: Monto total de la transacción
- `Timestamp`: Marca de tiempo de la transacción

**Nota:** Las claves exactas dependen de la estructura de la DLL de Wayne. El código intenta detectar automáticamente las propiedades disponibles.

## Manejo de Errores

El paquete define tres excepciones personalizadas:

- `FusionControllerError`: Excepción base
- `DLLLoadError`: Error al cargar la DLL
- `ConnectionError`: Error de conexión con el controlador

Ejemplo de manejo de errores:

```python
from fusion_reader import FusionController
from fusion_reader.fusion_controller import (
    ConnectionError, 
    DLLLoadError, 
    FusionControllerError
)

try:
    controller = FusionController(CONTROLLER_IP, DLL_PATH)
    controller.connect()
    sale = controller.get_last_sale()
except DLLLoadError as e:
    print(f"Error cargando DLL: {e}")
except ConnectionError as e:
    print(f"Error de conexión: {e}")
except FusionControllerError as e:
    print(f"Error del controlador: {e}")
```

## Ejemplos

Consulte `example_usage.py` para ver ejemplos completos de uso, incluyendo:

1. Uso básico con gestión manual de conexión
2. Uso con context manager
3. Polling continuo para nuevas ventas
4. Manejo completo de errores

## Requisitos del Sistema

- Python 3.6+
- pythonnet 3.0.0+
- Acceso a la DLL de Wayne Fusion
- Conectividad de red con el controlador Fusion

## Notas Importantes

1. **DLL de Wayne**: Este paquete requiere acceso a la DLL propietaria de Wayne. Asegúrese de tener los permisos y licencias necesarios.

2. **Nombres de Clases y Métodos**: Los nombres exactos de clases, métodos y propiedades en la DLL pueden variar. Este código utiliza nombres comunes y patrones típicos. Ajuste según la documentación específica de su versión de la DLL de Wayne.

3. **Compatibilidad**: pythonnet funciona principalmente en Windows. Para otros sistemas operativos, puede ser necesario usar alternativas como Mono.

4. **Thread Safety**: El polling continuo es bloqueante. Para aplicaciones concurrentes, ejecute el polling en un thread o proceso separado.

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Cree una rama para su feature (`git checkout -b feature/AmazingFeature`)
3. Commit sus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abra un Pull Request

## Licencia

Este proyecto es propiedad de Kernel Informatica.

## Soporte

Para soporte o preguntas, contacte a Kernel Informatica.

## Referencias

- Documentación Wayne Fusion: Páginas 22 (GetLastSale) y 29 (GetLastSaleOnFusion)
- [pythonnet Documentation](http://pythonnet.github.io/)
- [Google AI Studio Prompt](https://aistudio.google.com/app/prompts/1Af2A19gwpn7ZcADBVEa9INvdPlH_gEvr)
