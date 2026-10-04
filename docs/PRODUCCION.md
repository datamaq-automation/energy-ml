# Guía de Producción: Modo SSH

## Requisitos Previos

### 1. Conectividad Tailscale

La aplicación debe estar en la misma red Tailscale que la VPS.

```bash
# Verificar que Tailscale está activo
tailscale status

# Debería mostrar algo como:
# 100.x.x.x     your-machine     linux   -
# 100.y.y.y     vps              linux   active; relay "..."
```

**Si Tailscale no está instalado:**
```bash
# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Sigue las instrucciones para autenticarte
```

### 2. Configuración SSH (sin contraseña)

La máquina debe tener acceso SSH sin contraseña a la VPS.

**En tu máquina local:**

```bash
# Generar clave SSH si no existe
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Mostrar la clave pública
cat ~/.ssh/id_ed25519.pub
```

**En la VPS (por un administrador):**

```bash
# Agregar la clave pública a ~/.ssh/authorized_keys
echo "ssh-ed25519 AAAA... your@machine" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

**Configurar ~/.ssh/config (local):**

```
Host vps
    Hostname vps
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    BatchMode yes
```

**Validar acceso:**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 vps true
# Si devuelve exit code 0, está OK. Sino, revisar claves.
```

### 3. MySQL en la VPS

Verificar que root puede acceder a MySQL sin contraseña (típico en desarrollo):

```bash
ssh vps "mysql --batch --skip-column-names -e 'SELECT d.name, t.recorded_at, t.total_active_power FROM datamaq_telemetry.telemetry_instantaneous t JOIN datamaq_telemetry.devices d ON d.id = t.device_id LIMIT 1'"

# Debería devolver: Trafo arriba    2026-10-03 12:00:00    92000
```

---

## Configuración en `config.py`

```python
MEDICIONES_SOURCE: str = Field(default="local")      # "local" o "ssh"
MEDICIONES_CACHE_DIR: str = Field(default="data/prod-cache")
```

Setear via **variable de entorno:**

```bash
export MEDICIONES_SOURCE=ssh
./run.sh start prod
```

O via **argumento en run.sh:**

```bash
./run.sh start prod   # Exporta MEDICIONES_SOURCE=ssh automáticamente
```

---

## Levantando la Aplicación en Producción

### Paso 1: Validar conectividad

```bash
# El script automatiza esto, pero puedes verificar manualmente:
ssh -o BatchMode=yes -o ConnectTimeout=5 vps true && echo "✅ SSH OK" || echo "❌ SSH falló"
```

### Paso 2: Iniciar servidor

```bash
./run.sh start prod
```

**Salida esperada:**

```
🚀 Iniciando servidor FastAPI en modo producción (datos desde VPS)...
🔐 Modo PROD: validando conectividad SSH a VPS...
✅ Conectividad SSH validada
INFO:     Aplicación FastAPI creada
🔄 Modo PROD: sincronizando mediciones desde VPS...
📥 Conectando a VPS 'vps' via SSH (timeout 30s)...
✅ Descarga desde VPS completada. Procesando datos...
📊 Datos recuperados: 2 medidores
  - Trafo arriba: 5040 registros
  - Trafo abajo: 5040 registros
💾 Cacheado: Trafo arriba → data/prod-cache/planta_2_a.csv (5040 registros)
💾 Cacheado: Trafo abajo → data/prod-cache/planta_2_b.csv (5040 registros)
✅ Mediciones del VPS sincronizadas al startup
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Paso 3: Verificar que funciona

```bash
# En otra terminal:
curl http://localhost:8000/api/v1/mediciones/fuente | jq .

# Debería devolver:
{
  "fuente": "ssh",
  "medidores": ["planta_2_a", "planta_2_b"],
  "ultima_descarga": {
    "instante": "2026-10-04T12:30:00",
    "duracion_segundos": 2.4,
    "filas_por_medidor": {
      "Trafo arriba": 5040,
      "Trafo abajo": 5040
    }
  }
}
```

---

## Troubleshooting

### ❌ "No se puede conectar a VPS 'vps' via SSH"

**Causas posibles:**

1. **Tailscale no está activo**
   ```bash
   tailscale status
   # Si no aparece la VPS, reconectar:
   sudo tailscale up
   ```

2. **Host 'vps' no resuelve**
   ```bash
   # Verificar que está en ~/.ssh/config
   cat ~/.ssh/config | grep -A3 "Host vps"
   
   # O usar IP de Tailscale:
   ssh -o BatchMode=yes -o ConnectTimeout=5 100.y.y.y true
   ```

3. **Clave pública no instalada en VPS**
   ```bash
   # Pedir a admin que agregue tu clave a ~/.ssh/authorized_keys en VPS
   cat ~/.ssh/id_ed25519.pub  # Copiar esto
   ```

4. **Permisos en ~/.ssh incorrectos**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   ```

### ❌ "SSH/MySQL error: Access denied for user 'root'"

El usuario root no tiene acceso a MySQL sin contraseña en la VPS.

**Solución:** Contactar a administrador VPS para:
- Verificar que `skip-grant-tables` está habilitado, O
- Crear usuario sin contraseña específicamente para este script

### ❌ "SSH timeout después de 30s"

La descarga tarda mucho (VPS lenta o datos enormes).

**Opciones:**

1. Aumentar timeout en `src/infrastructure/ssh/medicion_repository.py:22`
   ```python
   SSH_TIMEOUT = 60  # Aumentar de 30
   ```

2. Filtrar datos históricos: modificar `CONSULTA_SQL` en `src/infrastructure/ssh/medicion_repository.py:25`
   ```sql
   AND t.recorded_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)  # Últimos 7 días
   ```

### ❌ Cache corrupto: "Cache ausente: data/prod-cache/planta_2_a.csv"

El cache se borró o está vacío.

**Solución:** Reiniciar el servidor (sincroniza automáticamente)
```bash
./run.sh start prod
```

### ❌ ¿Cómo sé si está usando dev o prod?

```bash
curl http://localhost:8000/api/v1/mediciones/fuente | jq .fuente
# Devuelve: "local" o "ssh"
```

---

## Monitoreo y Métricas

### Verificar fuente de datos y metadatos

```bash
curl http://localhost:8000/api/v1/mediciones/fuente | jq .
```

**Campos útiles:**

- `fuente`: "local" o "ssh"
- `medidores`: lista de medidores disponibles
- `ultima_descarga.duracion_segundos`: cuánto tardó la descarga SSH
- `ultima_descarga.filas_por_medidor`: cantidad de registros descargados

### Logs

```bash
# Ver logs en tiempo real (si corrés con `exec` en lugar de daemon)
tail -f logs/energy-ml.log | grep -i "ssh\|descarga\|mediciones"
```

---

## Diferencias entre Dev y Prod

| Aspecto | Dev | Prod |
|---------|-----|------|
| **Fuente** | `data/input/*.csv` (versionado) | MySQL en VPS (actualizado) |
| **Startup** | ~1s | ~3s (descarga SSH) |
| **Fail-fast** | No (inicia sin datos) | Sí (valida SSH, sale si falla) |
| **Cache** | N/A | `data/prod-cache/` (persiste) |
| **Sincronización** | Una sola vez (flag en instancia) | Una sola vez por proceso (lru_cache) |
| **Caso de uso** | Educación, testing local | Producción con datos actualizados |

---

## Configuración Recomendada para Producción

### En .env (si usas)

```bash
MEDICIONES_SOURCE=ssh
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=False
```

### En systemd (si corres como servicio)

```ini
[Unit]
Description=energy-ml FastAPI (Producción)
After=network.target tailscale.service

[Service]
Type=simple
User=energia
WorkingDirectory=/home/energia/energy-ml
Environment="MEDICIONES_SOURCE=ssh"
ExecStart=/home/energia/energy-ml/run.sh start prod
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl enable energy-ml
sudo systemctl start energy-ml
sudo systemctl status energy-ml
sudo journalctl -u energy-ml -f
```

---

## Respaldo: ¿Qué pasa si el VPS se cae?

- **En startup:** El servidor **no levanta** (`RuntimeError` → exit 1)
- **Ya corriendo:** Los datos quedan en `data/prod-cache/` del startup anterior
- **En siguientes requests:** Usan datos en caché (pueden ser viejos)

**Estrategia:** Monitorear health checks y alertas si el VPS se desconecta.

```bash
# Health check simple
curl http://localhost:8000/health && echo "✅" || echo "❌"

# Más detallado
curl http://localhost:8000/api/v1/mediciones/fuente | jq .ultima_descarga.instante
```
