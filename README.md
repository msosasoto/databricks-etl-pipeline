# Databricks ETL Pipeline

Pipeline ETL básico para procesar datos de ventas usando PySpark y Delta Lake en Databricks, con deployment automatizado mediante Databricks Asset Bundles.

## 📊 Descripción del Proyecto

Este proyecto implementa un pipeline de datos end-to-end que:
- **Ingesta** datos de ventas desde una tabla Delta
- **Transforma** los datos aplicando lógica de negocio
- **Carga** resultados en una tabla Delta optimizada

### Transformaciones aplicadas
- ✅ Cálculo de monto total por orden (`quantity × price`)
- ✅ Extracción de componentes temporales (año, mes, día de la semana)
- ✅ Clasificación de órdenes por volumen (Small/Medium/Large)
- ✅ Categorización por precio (Budget/Standard/Premium)
- ✅ Registro de timestamp de procesamiento

### Métricas generadas
- 📈 Ventas totales por país
- 📦 Ventas por categoría de producto
- 💰 Estadísticas de montos (min, max, avg, total)

## 📁 Estructura del Proyecto
```
databricks-etl-pipeline/
├── data/
│   ├── raw/              # Datos fuente (ventas_raw.csv)
│   └── processed/        # Datos transformados (local)
├── resources/
│   └── notebooks/
│       └── etl_pipeline.ipynb  # Notebook principal del pipeline
├── src/                  # Código reutilizable (próximas iteraciones)
├── tests/                # Pruebas unitarias (próximas iteraciones)
├── docs/                 # Documentación adicional
├── databricks.yml        # Configuración del Databricks Asset Bundle
├── README.md
├── .gitignore
└── requirements.txt
```

## 🚀 Cómo Ejecutar

### Prerrequisitos
- Cuenta de Databricks (Free Tier o superior)
- Databricks CLI instalada
- VS Code con extensión de Databricks

### Setup inicial

1. **Clonar el repositorio**:
```bash
git clone https://github.com/msosasoto/databricks-etl-pipeline.git
cd databricks-etl-pipeline
```

2. **Configurar Databricks CLI**:
```bash
databricks auth login --host <TU_WORKSPACE_URL>
```

3. **Subir datos iniciales**:
   - Cargar `data/raw/ventas_raw.csv` a Databricks como tabla Delta
   - Catálogo: `datasets_github_projects`
   - Schema: `default`
   - Tabla: `ventas_raw`

### Desarrollo y Deployment

1. **Editar el notebook localmente** en VS Code:
```bash
code resources/notebooks/etl_pipeline.ipynb
```

2. **Validar configuración**:
```bash
databricks bundle validate
```

3. **Deployar a Databricks**:
```bash
databricks bundle deploy
```

4. **Ejecutar el Job** desde Databricks Web:
   - Ve a **Workflows** → `[dev] ETL Pipeline`
   - Clic en **Run Now**

### Tablas generadas
- 📥 **Entrada**: `datasets_github_projects.default.ventas_raw`
- 📤 **Salida**: `datasets_github_projects.default.ventas_transformed`

## 🛠️ Stack Tecnológico

| Herramienta | Versión | Propósito |
|------------|---------|-----------|
| **Databricks** | Free Tier | Plataforma de procesamiento |
| **PySpark** | 3.5+ | Motor de transformaciones |
| **Delta Lake** | 3.0+ | Almacenamiento transaccional |
| **Python** | 3.10+ | Lenguaje base |
| **Databricks CLI** | 0.275+ | Deployment automatizado |
| **Databricks Asset Bundles** | - | Infraestructura como código |

## 📊 Resultados

### Dataset Original
- 10 registros de ventas
- 8 columnas
- Rango: 2024-01-15 a 2024-01-19

### Dataset Transformado
- 10 registros enriquecidos
- 15 columnas (7 nuevas columnas calculadas)
- Formato: Delta Lake con versionamiento

### Métricas de Negocio
- **Revenue total**: $3,654.88
- **Ticket promedio**: $365.49
- **Categoría top**: Electronics (60% de órdenes)

## 🔄 Flujo de Desarrollo
```
Editar en VS Code → databricks bundle deploy → Ejecutar en Databricks
```

Los cambios en `resources/notebooks/etl_pipeline.ipynb` se sincronizan automáticamente con el workspace de Databricks mediante el Bundle.

## 🎯 Próximos Pasos

- [ ] Implementar pruebas unitarias con pytest
- [ ] Agregar validación de calidad de datos
- [ ] Crear pipeline orquestado con Databricks Workflows
- [ ] Implementar CI/CD con GitHub Actions
- [ ] Añadir logging estructurado

## 👤 Autor

**Mariano Sosa**  
Ingeniero de Datos  
Stack: Python | PySpark | Azure | Databricks | Docker

---

📝 *Este es el Proyecto #1 de una serie de proyectos incrementales en ingeniería de datos*