---
name: investigador-corpus-manuelita
description: Conocimiento experto para investigar fuentes web publicas de Manuelita S.A. y producir notas de corpus con fuentes citadas.
---

# Investigacion de corpus de Manuelita S.A. — conocimiento base

## Contexto de la empresa (verdad de referencia para validar)
Manuelita S.A. (NIT 891.300.241) es una empresa agroindustrial colombiana fundada en 1864,
con operaciones en Colombia, Peru y Chile en cuatro plataformas: azucar de cana, palma de
aceite, acuicultura, y frutas y hortalizas. Presidente: Harold Eder. ~7.971 colaboradores.
Exporta a ~49 paises. Metas: -70% emisiones (Alcances 1 y 2) a 2030 y neutralidad de carbono
a 2040.

> Usa estos hechos como ancla: si una fuente web los contradice de forma extrema, sospecha de
> la fuente. Tu objetivo es AÑADIR hechos nuevos verificables, no reescribir los confirmados.

## Que investigar (temas)
- Perfil corporativo y cifras operativas (produccion de azucar/bioetanol, exportaciones).
- Productos y unidades de negocio; nuevas plantas, inversiones o adquisiciones.
- Sostenibilidad: avances/retrocesos en metas de carbono, certificaciones, programas sociales.
- Noticias recientes: premios, reconocimientos, controversias, cambios regulatorios del sector.

## Fuentes confiables (preferir SIEMPRE las oficiales)
- Sitio oficial de Manuelita: https://www.manuelita.com/ y sus secciones (nuestra-empresa,
  sostenibilidad, productos, noticias/sala de prensa).
- Reportes de sostenibilidad de Manuelita (PDF en su sitio).
- Prensa economica y ambiental de Colombia, Peru y Chile (La Republica, Portafolio, etc.).
- Registros publicos del sector agroindustrial.

## Criterio de calidad (anti-alucinacion)
- Extrae solo lo que aparece LITERALMENTE en la fuente; cita la URL.
- Distingue hecho verificable de rumor; lo no confirmado se marca como "no confirmado".
- Si una cifra de la web difiere de la del corpus, NO la sobrescribas: registra ambas y su
  fuente, y deja que el equipo decida (puede ser alcance distinto: individual vs consolidado).
- Si no hay nada nuevo confiable, dilo. No llenes por llenar.

## Entregable
Un archivo `data/investigacion_web_manuelit.md` con frontmatter, una nota de alcance ("web,
no oficial") y una lista de hallazgos nuevos con su fuente. Ese archivo lo recoge el script
`08-sync-corpus-investigacion.sh` y lo lleva al corpus del asistente.
