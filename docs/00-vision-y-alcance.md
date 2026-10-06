# 00 · Visión y alcance

## Problema

ServicioCerca coordina técnicos de mantenimiento en los barrios de una ciudad. Cuando entra una solicitud, hoy decide **por teléfono y con conocimiento informal**:

- si la zona puede atenderse desde alguna base;
- qué técnico podría llegar con menor costo estimado.

Esa forma de decidir no es repetible, ni auditable, ni escala.

## Objetivo

Entregar un MVP que, con datos sintéticos, permita:

1. **Configurar** la red operativa: bases con sus técnicos, zonas y trayectos con tiempo positivo.
2. **Consultar la cobertura**: saber si una zona es alcanzable desde una base y qué zonas alcanza cada base.
3. **Consultar la alternativa de menor costo**: obtener la ruta y el costo total de una base a una zona, y qué base con técnico disponible llega más barato.
4. **Operar desde una consola** que muestra la red, resalta el resultado y responde de forma consistente cuando la atención no es posible.

## Usuarios y permisos

| Rol | Necesidad | Permiso API |
|---|---|---|
| Coordinador de operaciones | Registrar bases, técnicos, zonas y conexiones | `coordinator`: lectura y escritura |
| Operador de atención | Consultar cobertura y alternativa de atención | `operator`: solo lectura |
| (Sistema) routing-service | Leer la red para calcular | `internal`: solo lectura de la red |

## Alcance (incluido)

- Datos sintéticos de bases, técnicos, zonas y trayectos con tiempo positivo (en minutos).
- Registro y validación: identificadores, duplicados y pesos positivos.
- Cobertura por alcance (BFS) con traza.
- Camino de menor costo (Dijkstra) con traza y una comparación con el camino de menos tramos.
- Consola con visualización y resaltado del resultado.
- Aceptación de 4 escenarios: éxito, zona inexistente, red desconectada y peso inválido.

## Fuera de alcance

Según el brief, no se incluye:
- ubicación en tiempo real ni geolocalización;
- turnos complejos;
- pagos;
- asignación automática multi-técnico.

Tampoco se incluyen:
- gestión de usuarios ni contraseñas, porque basta con una API key por rol ([ADR 0004](adr/0004-auth-api-key-por-rol.md));
- despliegue en la nube, porque el uso es local con Docker.

## Criterio de éxito (del cliente)

> En una demo, el operador registra la red, consulta una zona, recibe una alternativa entendible
> y observa respuestas consistentes cuando la atención no es posible.

## Requisitos no funcionales

- Se ejecuta igual en macOS, Windows y Linux, porque todo corre en Docker.
- Se aplican SOLID y una arquitectura por capas; se puede trabajar en paralelo entre 4 personas.
- Seguridad: RBAC, validación estricta, secretos fuera del repositorio y contenedores endurecidos.
- Calidad: el harness automatizado (`make test`) es la Definition of Done.
