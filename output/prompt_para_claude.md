Eres analista de marketing especializado en visibilidad en buscadores de IA (GEO).
Redactas en español de España, para dirección de marketing: frases cortas, concretas, sin jerga.

Reglas:
- Usa SOLO las cifras que aparecen en los datos. No calcules porcentajes nuevos ni redondees distinto.
- Es una muestra pequeña: habla de indicios ("en esta muestra", "apunta a"), nunca de certezas.
- Describe hechos medidos, sin juicios de valor sobre las empresas.
- Las acciones deben ser concretas y estar justificadas por un dato del estudio o de la auditoría técnica.
- Si hay varios asistentes (ChatGPT, Gemini...), compara la marca principal entre ellos.
- En "reputation", una entrada por pregunta de marca (question_id), resumiendo todas sus respuestas.
- Propón 4 o 5 acciones, ordenadas de mayor a menor impacto.

Con los datos de abajo, devuelve ÚNICAMENTE un JSON válido con esta estructura (sin texto antes ni después):

{
  "headline": "Hallazgo principal en una frase, con su cifra.",
  "findings": [
    "Hallazgo 1 con su dato",
    "Hallazgo 2 con su dato",
    "Hallazgo 3 con su dato"
  ],
  "reputation": [
    {
      "question_id": "D1",
      "tone": "positivo | neutro | mixto | negativo",
      "summary": "Qué dicen los asistentes."
    }
  ],
  "actions": [
    {
      "action": "Qué hacer",
      "why": "Dato del estudio que lo justifica",
      "impact": "alto | medio | bajo",
      "effort": "alto | medio | bajo"
    }
  ]
}

DATOS DEL ESTUDIO:

{
 "estudio": {
  "titulo": "¿Recomienda la IA a Coolmod?",
  "marca_principal": "Coolmod"
 },
 "indicadores": {
  "brands": [
   {
    "id": "pccomponentes",
    "name": "PcComponentes",
    "is_main": false,
    "share_of_voice": {
     "count": 19,
     "n": 20,
     "rate": 95,
     "ci": [
      76,
      99
     ]
    },
    "first_mention": {
     "count": 16,
     "n": 20,
     "rate": 80,
     "ci": [
      58,
      92
     ]
    },
    "cited_as_source": {
     "count": 13,
     "n": 20,
     "rate": 65,
     "ci": [
      43,
      82
     ]
    },
    "share_of_voice_by_block": {
     "A": 100,
     "B": 88,
     "C": 100
    },
    "share_of_voice_by_engine": {
     "chatgpt": 100,
     "gemini": 90
    }
   },
   {
    "id": "amazon",
    "name": "Amazon",
    "is_main": false,
    "share_of_voice": {
     "count": 11,
     "n": 20,
     "rate": 55,
     "ci": [
      34,
      74
     ]
    },
    "first_mention": {
     "count": 0,
     "n": 20,
     "rate": 0,
     "ci": [
      0,
      16
     ]
    },
    "cited_as_source": {
     "count": 5,
     "n": 20,
     "rate": 25,
     "ci": [
      11,
      47
     ]
    },
    "share_of_voice_by_block": {
     "A": 75,
     "B": 38,
     "C": 50
    },
    "share_of_voice_by_engine": {
     "chatgpt": 40,
     "gemini": 70
    }
   },
   {
    "id": "coolmod",
    "name": "Coolmod",
    "is_main": true,
    "share_of_voice": {
     "count": 10,
     "n": 20,
     "rate": 50,
     "ci": [
      30,
      70
     ]
    },
    "first_mention": {
     "count": 0,
     "n": 20,
     "rate": 0,
     "ci": [
      0,
      16
     ]
    },
    "cited_as_source": {
     "count": 5,
     "n": 20,
     "rate": 25,
     "ci": [
      11,
      47
     ]
    },
    "share_of_voice_by_block": {
     "A": 88,
     "B": 38,
     "C": 0
    },
    "share_of_voice_by_engine": {
     "chatgpt": 40,
     "gemini": 60
    }
   },
   {
    "id": "mediamarkt",
    "name": "MediaMarkt",
    "is_main": false,
    "share_of_voice": {
     "count": 9,
     "n": 20,
     "rate": 45,
     "ci": [
      26,
      66
     ]
    },
    "first_mention": {
     "count": 3,
     "n": 20,
     "rate": 15,
     "ci": [
      5,
      36
     ]
    },
    "cited_as_source": {
     "count": 5,
     "n": 20,
     "rate": 25,
     "ci": [
      11,
      47
     ]
    },
    "share_of_voice_by_block": {
     "A": 38,
     "B": 25,
     "C": 100
    },
    "share_of_voice_by_engine": {
     "chatgpt": 50,
     "gemini": 40
    }
   },
   {
    "id": "neobyte",
    "name": "Neobyte",
    "is_main": false,
    "share_of_voice": {
     "count": 4,
     "n": 20,
     "rate": 20,
     "ci": [
      8,
      42
     ]
    },
    "first_mention": {
     "count": 0,
     "n": 20,
     "rate": 0,
     "ci": [
      0,
      16
     ]
    },
    "cited_as_source": {
     "count": 1,
     "n": 20,
     "rate": 5,
     "ci": [
      1,
      24
     ]
    },
    "share_of_voice_by_block": {
     "A": 38,
     "B": 12,
     "C": 0
    },
    "share_of_voice_by_engine": {
     "chatgpt": 10,
     "gemini": 30
    }
   }
  ],
  "engines": [
   {
    "id": "chatgpt",
    "name": "ChatGPT",
    "answers": 10
   },
   {
    "id": "gemini",
    "name": "Gemini",
    "answers": 10
   }
  ],
  "top_sources": [
   {
    "domain": "pccomponentes.com",
    "answers": 13,
    "rate": 65,
    "brand": "PcComponentes",
    "is_main": false
   },
   {
    "domain": "mediamarkt.es",
    "answers": 5,
    "rate": 25,
    "brand": "MediaMarkt",
    "is_main": false
   },
   {
    "domain": "amazon.es",
    "answers": 5,
    "rate": 25,
    "brand": "Amazon",
    "is_main": false
   },
   {
    "domain": "coolmod.com",
    "answers": 5,
    "rate": 25,
    "brand": "Coolmod",
    "is_main": true
   },
   {
    "domain": "elcorteingles.es",
    "answers": 2,
    "rate": 10,
    "brand": null,
    "is_main": false
   },
   {
    "domain": "contrapc.es",
    "answers": 2,
    "rate": 10,
    "brand": null,
    "is_main": false
   },
   {
    "domain": "pcscan.es",
    "answers": 2,
    "rate": 10,
    "brand": null,
    "is_main": false
   },
   {
    "domain": "pass.carrefour.es",
    "answers": 2,
    "rate": 10,
    "brand": null,
    "is_main": false
   },
   {
    "domain": "wikiversus.com",
    "answers": 2,
    "rate": 10,
    "brand": null,
    "is_main": false
   },
   {
    "domain": "m8d.io",
    "answers": 2,
    "rate": 10,
    "brand": null,
    "is_main": false
   }
  ],
  "reputation": {
   "answers": 4,
   "official_site_cited": 3,
   "sources": [
    [
     "coolmod.com",
     3
    ],
    [
     "idealo.es",
     2
    ],
    [
     "pccomponentes.com",
     2
    ],
    [
     "hardzone.es",
     1
    ],
    [
     "es.trustpilot.com",
     1
    ],
    [
     "ocu.org",
     1
    ],
    [
     "tustiendas.es",
     1
    ],
    [
     "reddit.com",
     1
    ]
   ]
  },
  "neutral_answers": 20,
  "runs_per_question": 3
 },
 "auditoria_tecnica": {
  "coolmod": {
   "url": "https://www.coolmod.com",
   "score": 67,
   "band": "foundation",
   "error": null,
   "categories": [
    {
     "key": "google_ai",
     "label": "Preparación para Google IA",
     "points": 18,
     "max": 20
    },
    {
     "key": "robots",
     "label": "Acceso de rastreadores de IA (robots.txt)",
     "points": 11,
     "max": 14
    },
    {
     "key": "schema",
     "label": "Datos estructurados",
     "points": 9,
     "max": 14
    },
    {
     "key": "content",
     "label": "Contenido citable",
     "points": 12,
     "max": 14
    },
    {
     "key": "brand_entity",
     "label": "Señales de marca",
     "points": 6,
     "max": 12
    },
    {
     "key": "meta",
     "label": "Metadatos",
     "points": 11,
     "max": 11
    },
    {
     "key": "llms",
     "label": "Archivo llms.txt",
     "points": 0,
     "max": 6
    },
    {
     "key": "signals",
     "label": "Señales técnicas",
     "points": 3,
     "max": 6
    },
    {
     "key": "ai_discovery",
     "label": "Endpoints para IA",
     "points": 0,
     "max": 3
    }
   ],
   "blockers": [
    "⚠️ CDN/WAF blocks AI crawlers: Googlebot. Configure your CDN to allow AI bot User-Agents (GPTBot, ClaudeBot, PerplexityBot)."
   ],
   "recommendations": [
    "Create /llms.txt for AI indexing: geo llms --base-url https://www.coolmod.com. Note: llms.txt is an organizational signal, not a proven ranking factor. It helps structure content for AI systems.",
    "[G-DATES] No valid publication or update date found — https://developers.google.com/search/docs/appearance/publication-dates",
    "[G-BYLINE] No author found: Google asks 'who created the content' — https://developers.google.com/search/docs/fundamentals/creating-helpful-content",
    "Use consistent brand name across title, og:title, H1, and schema Organization",
    "Add more sameAs links to Knowledge Graph pillars (currently 1/4: Wikipedia, Wikidata, LinkedIn, Crunchbase)"
   ]
  },
  "pccomponentes": {
   "url": "https://www.pccomponentes.com",
   "score": 0,
   "band": "critical",
   "error": "HTTP 403",
   "categories": [],
   "blockers": [],
   "recommendations": [
    "Site returned HTTP 403. Check for Cloudflare/WAF blocks or server errors."
   ]
  },
  "amazon": {
   "url": "https://www.amazon.es",
   "score": 42,
   "band": "foundation",
   "error": null,
   "categories": [
    {
     "key": "google_ai",
     "label": "Preparación para Google IA",
     "points": 16,
     "max": 20
    },
    {
     "key": "robots",
     "label": "Acceso de rastreadores de IA (robots.txt)",
     "points": 11,
     "max": 14
    },
    {
     "key": "schema",
     "label": "Datos estructurados",
     "points": 0,
     "max": 14
    },
    {
     "key": "content",
     "label": "Contenido citable",
     "points": 10,
     "max": 14
    },
    {
     "key": "brand_entity",
     "label": "Señales de marca",
     "points": 0,
     "max": 12
    },
    {
     "key": "meta",
     "label": "Metadatos",
     "points": 7,
     "max": 11
    },
    {
     "key": "llms",
     "label": "Archivo llms.txt",
     "points": 0,
     "max": 6
    },
    {
     "key": "signals",
     "label": "Señales técnicas",
     "points": 3,
     "max": 6
    },
    {
     "key": "ai_discovery",
     "label": "Endpoints para IA",
     "points": 0,
     "max": 3
    }
   ],
   "blockers": [
    "⚠️ Prompt injection in HTML comments detected — AI crawlers read comments, remove them",
    "Hidden text detected (display:none/visibility:hidden with content) — AI crawlers can read it and may penalize this cloaking pattern"
   ],
   "recommendations": [
    "⚠️ Prompt injection in HTML comments detected — AI crawlers read comments, remove them",
    "Hidden text detected (display:none/visibility:hidden with content) — AI crawlers can read it and may penalize this cloaking pattern",
    "Create /llms.txt for AI indexing: geo llms --base-url https://www.amazon.es. Note: llms.txt is an organizational signal, not a proven ranking factor. It helps structure content for AI systems.",
    "[G-DATES] No valid publication or update date found — https://developers.google.com/search/docs/appearance/publication-dates",
    "[G-BYLINE] No author found: Google asks 'who created the content' — https://developers.google.com/search/docs/fundamentals/creating-helpful-content"
   ]
  },
  "mediamarkt": {
   "url": "https://www.mediamarkt.es",
   "score": 74,
   "band": "good",
   "error": null,
   "categories": [
    {
     "key": "google_ai",
     "label": "Preparación para Google IA",
     "points": 18,
     "max": 20
    },
    {
     "key": "robots",
     "label": "Acceso de rastreadores de IA (robots.txt)",
     "points": 11,
     "max": 14
    },
    {
     "key": "schema",
     "label": "Datos estructurados",
     "points": 9,
     "max": 14
    },
    {
     "key": "content",
     "label": "Contenido citable",
     "points": 12,
     "max": 14
    },
    {
     "key": "brand_entity",
     "label": "Señales de marca",
     "points": 6,
     "max": 12
    },
    {
     "key": "meta",
     "label": "Metadatos",
     "points": 11,
     "max": 11
    },
    {
     "key": "llms",
     "label": "Archivo llms.txt",
     "points": 5,
     "max": 6
    },
    {
     "key": "signals",
     "label": "Señales técnicas",
     "points": 3,
     "max": 6
    },
    {
     "key": "ai_discovery",
     "label": "Endpoints para IA",
     "points": 0,
     "max": 3
    }
   ],
   "blockers": [],
   "recommendations": [
    "[G-DATES] No valid publication or update date found — https://developers.google.com/search/docs/appearance/publication-dates",
    "[G-BYLINE] No author found: Google asks 'who created the content' — https://developers.google.com/search/docs/fundamentals/creating-helpful-content",
    "Use consistent brand name across title, og:title, H1, and schema Organization",
    "Add more sameAs links to Knowledge Graph pillars (currently 1/4: Wikipedia, Wikidata, LinkedIn, Crunchbase)",
    "Add WebSite JSON-LD schema to homepage"
   ]
  },
  "neobyte": {
   "url": "https://www.neobyte.es",
   "score": 0,
   "band": "critical",
   "error": "HTTP 403",
   "categories": [],
   "blockers": [],
   "recommendations": [
    "Site returned HTTP 403. Check for Cloudflare/WAF blocks or server errors."
   ]
  }
 },
 "respuestas_reputacion": [
  {
   "question_id": "D1",
   "asistente": "ChatGPT",
   "pregunta": "¿Es fiable Coolmod?",
   "repeticion": 1,
   "respuesta": "Sí, Coolmod es una tienda de informática fiable en general, especialmente para comprar componentes de PC, tarjetas gráficas, periféricos y ordenadores gaming. Eso sí, hay algunos aspectos que conviene tener en cuenta antes de comprar.\n\nPor qué deberías visitar la tienda física de COOLMOD para comprar\n \nCoolmod\n4,5/5\nTrustpilot\n\nAlrededor de 15.000 opiniones. \n\nTrustpilot\n+1\n\nVisitar la tienda oficial \n\n¿Qué tal funciona?\nPrecios: suele tener ofertas competitivas en componentes de PC.\n\nEnvíos: muchos clientes destacan la rapidez y el buen embalaje, aunque también hay quejas por retrasos y problemas con las entregas.\n\nAtención al cliente: hay experiencias positivas, pero algunas personas informan de dificultades para contactar con la tienda cuando surge una incidencia.\n\nGarantías y devoluciones: es el punto que miraría con más atención, sobre todo si compras un ordenador completo o un componente caro. \n\nTrustpilot\n+2\n\n¿Hay algún motivo para tener cuidado?\nSí. En diciembre de 2025 se informó de una brecha de seguridad en Coolmod que habría expuesto datos de contacto de algunos clientes, como nombres, correos electrónicos y teléfonos. La información publicada indicó que no se habrían comprometido contraseñas ni datos bancarios. \n\nHardZone\n\nAdemás, la OCU recoge reclamaciones relacionadas con garantías, reparaciones y entregas. Esto no significa que todas las compras vayan a dar problemas, pero conviene conservar facturas y pruebas del estado del producto. \n\nOCU\n\nMi recomendación\nYo sí compraría en Coolmod si el precio es bueno y el producto está disponible, tomando estas precauciones:\n\nComprueba que el artículo esté realmente en stock.\n\nPaga con tarjeta o PayPal, si está disponible, para disponer de vías adicionales de reclamación.\n\nGuarda la confirmación del pedido y la factura.\n\nSi compras un PC caro, revisa el equipo y documenta cualquier daño nada más recibirlo.\n\nPara productos nuevos, Coolmod indica un plazo de garantía de 3 años en su propia página de soporte"
  },
  {
   "question_id": "D2",
   "asistente": "ChatGPT",
   "pregunta": "¿PcComponentes o Coolmod para comprar una tarjeta gráfica?",
   "repeticion": 1,
   "respuesta": "Si vas a comprar una tarjeta gráfica, yo compararía primero PcComponentes y Coolmod por el precio final y las condiciones de garantía y devolución. Las dos son tiendas conocidas en España, así que no elegiría automáticamente una por encima de la otra.\n\nMi criterio sería este:\n\nPcComponentes: la elegiría si cuesta lo mismo o casi lo mismo y prefieres comprar en una tienda generalista con un proceso de compra y posventa consolidado.\n\nCoolmod: la tendría muy en cuenta si encuentras una gráfica concreta más barata o una oferta especialmente buena.\n\nSi hay bastante diferencia de precio: no pagaría 50–100 € más por la misma tarjeta solo por comprar en una de las dos, salvo que las condiciones de envío, devolución o garantía lo justifiquen.\n\nHay una diferencia importante a favor de PcComponentes: sus condiciones publicadas contemplan hasta 30 días para devolver productos elegibles vendidos directamente por la tienda, con devolución gratuita; en Coolmod, el plazo general de desistimiento es de 14 días naturales. Comprueba siempre que la oferta concreta cumple esas condiciones. \n\nPcComponentes\n+1\n\nMi recomendación: si los precios son parecidos, me inclinaría por PcComponentes. Si Coolmod ofrece un ahorro significativo, también la consideraría una opción razonable.\n\nPara decirte cuál elegiría en tu caso, ¿qué tarjeta gráfica quieres comprar y cuánto cuesta en cada tienda? Si me pasas los dos enlaces, te comparo el precio, el modelo exacto, el vendedor y las condiciones de compra."
  },
  {
   "question_id": "D1",
   "asistente": "Gemini",
   "pregunta": "¿Es fiable Coolmod?",
   "repeticion": 1,
   "respuesta": "Sí, Coolmod es una tienda online totalmente fiable y legal. Es una empresa española veterana en el sector de la informática y el hardware gaming (con más de dos décadas de trayectoria), por lo que no tendrás problemas de timos o estafas; los pedidos siempre llegan o se efectúan las devoluciones correspondientes.   CoolmodNo obstante, las experiencias de los usuarios suelen dividirse en matices importantes que conviene conocer antes de comprar:   Precios competitivos: Frecuentemente tienen ofertas muy agresivas en componentes sueltos (tarjetas gráficas, procesadores) y ordenadores premontados, compitiendo directamente con gigantes como PcComponentes o Amazon.   RedditEl gran punto débil: Los plazos y la comunicación: Las queñas más habituales de los compradores se centran en que pueden ser lentos gestionando envíos o sacando adelante pedidos de PCs a medida (a veces tardan días en empezar a mover un paquete aunque todo ponga \"en stock\"). Además, su servicio de atención telefónica a veces colapsa, por lo que suele ser más efectivo gestionar cualquier incidencia a través de tickets o correo electrónico.   Disponibilidad real: Es muy importante revisar la etiqueta del producto. Si pone \"Envío inmediato\", suele cumplirse con rapidez; pero si indica \"bajo pedido\" o \"de 2 a 9 días\", significa que tienen que solicitarlo al proveedor y el proceso se alargará.   En resumen: puedes comprar con tranquilidad sabiendo que es un comercio consolidado y seguro, pero ten paciencia con los plazos de entrega y revisa bien el estado de stock del componente que te interese."
  },
  {
   "question_id": "D2",
   "asistente": "Gemini",
   "pregunta": "¿PcComponentes o Coolmod para comprar una tarjeta gráfica?",
   "repeticion": 1,
   "respuesta": "Tanto PcComponentes como Coolmod son dos de los comercios electrónicos de informática y hardware más fiables y consolidados de España. Ambas son tiendas totalmente seguras, pero tienen diferencias clave en cuanto a catálogo, gestión, precios y servicio postventa que conviene valorar antes de comprar una tarjeta gráfica.PcComponentesEs el gigante indiscutible del sector en España. Funciona de manera muy similar a un gran marketplace, lo que le otorga ventajas notables pero también algún inconveniente.   Puntos fuertes:Variedad y stock: Su catálogo es enorme. Además de productos propios, incluye a muchos vendedores externos, lo que facilita encontrar stock de cualquier ensamblador (ASUS, MSI, Gigabyte, etc.) o modelo concreto (tanto NVIDIA GeForce como AMD Radeon).   Logística y envíos: Su capacidad de entrega es muy rápida (habitualmente en 24-48 horas si hay stock propio) y los procesos de devolución suelen ser automatizados y ágiles.   Facilidades de pago: Ofrecen múltiples métodos de pago y opciones de financiación integradas.Puntos débiles:Al gestionar un volumen masivo de pedidos, su atención al cliente puede sentirse a veces más fría o impersonal.   Conviene revisar siempre si el producto lo vende directamente PcComponentes o una tienda externa asociada dentro de su plataforma para curarse en salud con las garantías.CoolmodEs una tienda más especializada y con solera (basada en Castellón), muy querida por los entusiastas del hardware y los montajes a medida.Puntos fuertes:Especialización técnica: Tradicionalmente han estado muy enfocados al sector gaming de altas prestaciones, refrigeración y componentes de ensambladores específicos.Precios y ofertas puntuales: A menudo lanzan promociones muy agresivas o descuentos directos en componentes de gama media-alta que pueden superar a la competencia.Puntos débiles:Gestión y plazos: Su estructura es más pequeña, por lo que en fechas de gran volumen de ventas (como Black Friday) o si tramitas una garantía/RMA compleja, el proceso puede volverse algo más lento que en PcComponentes.   Costes de envío: A diferencia de grandes superficies, en ocasiones cobran los gastos de envío o exigen un importe mínimo para que sean gratuitos.¿Cuál elegir?Elige PcComponentes si: Buscas la máxima rapidez en el envío, prefieres un proceso de devolución ultra sencillo o el modelo exacto de tarjeta gráfica que quieres solo está disponible (o más barato) en su plataforma.Elige Coolmod si: Tras comparar precios para ese modelo específico de gráfica te sale más económica o prefieres comprar en un comercio de perfil más tradicional y enfocado al entusiasta del PC.Consejo final: Antes de decidirte, compara el precio final con los gastos de envío incluidos en ambas webs, ya que al tratarse de componentes de importe elevado, una pequeña diferencia en el transporte o una oferta puntual suele decantar la balanza de un lado u otro."
  }
 ]
}