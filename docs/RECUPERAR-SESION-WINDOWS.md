# Recuperar la sesión de Claude Code en Windows

Guía paso a paso para volver a entrar a **Claude Code** sin iniciar sesión otra
vez, usando un respaldo de la sesión. Está escrita para una persona sin
experiencia técnica: cada paso indica exactamente qué hacer.

Hay dos formas:

- **Opción A — Copiar los archivos a mano.** Rápida, no instala nada. Ideal si
  solo se necesita entrar una vez.
- **Opción B — Con el programa Claude Session Guard.** Coloca los archivos
  automáticamente y deja activo el respaldo para el futuro. Requiere instalar
  Python una sola vez.

---

## Antes de empezar

Se necesita:

1. Una computadora con **Windows**.
2. **Claude Code ya instalado.** Si la sesión se cerró, es porque ya estaba
   instalado, así que este punto normalmente ya se cumple.
3. Los **3 archivos de respaldo** que compartió otra persona, con estos nombres
   exactos:
   - `.credentials.json`
   - `.last-cleanup`
   - `.claude.json`

> **Sobre los nombres:** si los archivos llegaron con una fecha delante (por
> ejemplo `2026-07-21_085355_.credentials.json`), conviene pedir que los
> reenvíen **sin la fecha**, o usar la **Opción B**, que la quita sola.

> ⚠️ **Seguridad:** estos archivos son la "llave" de la cuenta de Claude.
> Cualquier persona que los tenga puede entrar a esa cuenta. Deben guardarse en
> un lugar privado y no compartirse.

---

## Opción A — Copiar los archivos a mano

### Paso 1. Abrir la carpeta personal del usuario

1. Abrir el **Explorador de archivos** (icono de carpeta amarilla en la barra de
   tareas, o presionar la tecla **Windows + E**).
2. Hacer clic en la **barra de direcciones** (la franja de arriba que muestra la
   ruta actual).
3. Escribir exactamente lo siguiente y presionar **Enter**:

   ```
   %USERPROFILE%
   ```

4. Se abrirá la carpeta personal (algo parecido a `C:\Users\NombreDeUsuario`).

### Paso 2. Colocar el archivo `.claude.json`

1. Tener a la vista los 3 archivos recibidos (por ejemplo en la carpeta
   **Descargas**).
2. Hacer clic derecho sobre **`.claude.json`** y elegir **Copiar**.
3. Volver a la carpeta personal del Paso 1 y pegar ahí (clic derecho →
   **Pegar**).
4. Si aparece un aviso preguntando si se desea **reemplazar** el archivo que ya
   existe, elegir **Reemplazar el archivo del destino**.

   > Este archivo va **suelto** dentro de la carpeta personal, **no** dentro de
   > ninguna subcarpeta.

### Paso 3. Colocar `.credentials.json` y `.last-cleanup`

1. En la **barra de direcciones** del Explorador, escribir lo siguiente y
   presionar **Enter**:

   ```
   %USERPROFILE%\.claude
   ```

2. Se abrirá la carpeta `.claude`.

   > Si aparece un error diciendo que la carpeta no existe, significa que Claude
   > Code no está instalado o que nunca se inició sesión en esta computadora. En
   > ese caso, instalar primero Claude Code y volver a este paso.

3. Copiar los archivos **`.credentials.json`** y **`.last-cleanup`** desde donde
   estén guardados y pegarlos dentro de esta carpeta `.claude`.
4. Cuando pregunte, elegir **Reemplazar el archivo del destino**.

### Paso 4. Abrir Claude Code

1. Cerrar Claude Code si estaba abierto.
2. Abrirlo de nuevo. Debe entrar directamente, sin pedir correo ni código de
   verificación.

Si no entró, revisar la sección **Si algo no funciona**.

---

## Opción B — Con el programa Claude Session Guard

Esta opción coloca los archivos automáticamente (les quita la fecha del nombre)
y deja activo el respaldo para el futuro. Requiere instalar **Python** una vez.

### Paso 1. Instalar Python

1. Abrir el navegador y entrar a: **https://www.python.org/downloads/**
2. Hacer clic en el botón amarillo grande **Download Python** (la versión más
   reciente).
3. Abrir el archivo que se descargó (aparece abajo en el navegador o en la
   carpeta **Descargas**).
4. **Muy importante:** en la primera pantalla del instalador, marcar la casilla
   de abajo que dice **“Add python.exe to PATH”**. Después hacer clic en
   **Install Now**.
5. Esperar a que termine y cerrar el instalador.

### Paso 2. Descargar el programa

1. Entrar a: **https://github.com/DiegoFernandoLojanTenesaca/claude-session-guard**
2. Hacer clic en el botón verde que dice **`< > Code`**.
3. En el menú que se abre, hacer clic en **Download ZIP**.
4. Abrir la carpeta **Descargas**, hacer clic derecho sobre el archivo ZIP y
   elegir **Extraer todo…** y luego **Extraer**.
5. Se creará una carpeta llamada `claude-session-guard-main`. Abrirla.

### Paso 3. Poner el respaldo en su lugar

1. En la **barra de direcciones** del Explorador, escribir lo siguiente y
   presionar **Enter**:

   ```
   %USERPROFILE%\claude-backups
   ```

   > Si aparece un error de que no existe, crearla: ir a `%USERPROFILE%`, hacer
   > clic derecho en un espacio vacío → **Nuevo → Carpeta**, y nombrarla
   > exactamente `claude-backups`.

2. Colocar dentro de `claude-backups` la **carpeta de respaldo** que compartió la
   otra persona (por ejemplo una carpeta llamada `2026-07-21_085355` con los
   archivos adentro). Simplemente copiar y pegar esa carpeta completa aquí.

### Paso 4. Instalar y restaurar

1. Volver a la carpeta del programa (`claude-session-guard-main`) y buscar el
   archivo **`install.bat`**.
2. Hacer **doble clic** en `install.bat`.

   > Si Windows muestra una pantalla azul que dice **“Windows protegió su PC”**,
   > hacer clic en **Más información** y luego en **Ejecutar de todas formas**.
   > Es normal: ocurre con programas que no tienen firma de pago.

3. Se abrirá una ventana negra por unos segundos. Esperar a que muestre la
   palabra **“Instalado”**. Si pide presionar una tecla, hacerlo.
4. Abrir el menú **Inicio**, escribir **Claude Session Guard** y abrir la
   aplicación.
5. En la ventana, hacer clic en el botón **Restaurar el último** y confirmar con
   **Sí**.

### Paso 5. Abrir Claude Code

Cerrar Claude Code y volver a abrirlo. Debe entrar directamente.

---

## Si algo no funciona

**Claude sigue pidiendo iniciar sesión.**
- Verificar que los archivos se pusieron en las rutas exactas y con los nombres
  correctos (`.credentials.json` y `.last-cleanup` dentro de `%USERPROFILE%\.claude`,
  y `.claude.json` suelto en `%USERPROFILE%`).
- Revisar que los nombres no tengan la fecha delante.
- Confirmar que Claude Code se cerró por completo antes de volver a abrirlo.

**No aparece la carpeta `.claude`.**
- Significa que Claude Code no está instalado en esta computadora. Instalarlo
  primero (ver la [documentación oficial](https://docs.claude.com/en/docs/claude-code/overview)),
  y luego repetir los pasos.

**`install.bat` se cierra de inmediato o dice que no encuentra Python.**
- Reinstalar Python (Opción B, Paso 1) y asegurarse de marcar la casilla
  **“Add python.exe to PATH”** durante la instalación.

**Se probó todo y aun así no inicia sesión.**
- Es posible que esta versión de Windows guarde el token en el **Administrador de
  credenciales de Windows** en lugar de en un archivo. En ese caso, el método de
  copiar archivos no es suficiente. Avisar a quien compartió el respaldo.

---

## Nota de seguridad

Los archivos de respaldo contienen el token de acceso: equivalen a la contraseña
de la cuenta de Claude. Recomendaciones:

- Guardarlos en un lugar privado (no en carpetas compartidas ni públicas).
- No enviarlos por canales inseguros.
- Si la cuenta es compartida, tener presente que quien reciba estos archivos
  tendrá acceso completo a esa sesión.
