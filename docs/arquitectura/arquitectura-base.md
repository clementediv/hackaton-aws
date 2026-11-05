---
tipo: arquitectura
estado: plantilla
---
# Arquitectura base (agnóstica al reto)

Plantilla genérica. **Ya está adaptada al reto elegido en [arquitectura-chileatiende](arquitectura-chileatiende.md).**

```mermaid
flowchart LR
  U[Usuario / Frontend<br/>Amplify o Streamlit] --> API[API Gateway + Lambda<br/>FastAPI]
  API --> AG[Orquestador IA<br/>Bedrock Agents / LangGraph]
  AG --> LLM[Bedrock<br/>Claude]
  AG --> KB[Knowledge Base<br/>RAG sobre S3]
  AG --> ML[Modelo propio<br/>SageMaker endpoint]
  API --> DB[(DynamoDB)]
  S3[(S3 datos)] --> KB
  S3 --> ML
  EV[EventBridge] --> API
```

## Capas
1. **Ingesta**: S3 + Lambda/Glue para limpiar datos del reto.
2. **Inteligencia**: LLM vía Bedrock (razonamiento, extracción, RAG) + modelo propio si hay datos estructurados o imágenes.
3. **Orquestación**: Bedrock Agents (rápido de montar) o LangGraph en Lambda (más control).
4. **Producto**: frontend mínimo para la demo; la demo manda.
5. **Observabilidad**: CloudWatch + logs de prompts para depurar.

## Decisiones pendientes
- [ ] Bedrock Agents vs LangGraph → ADR
- [ ] Frontend: Streamlit (rápido) vs React/Amplify (más pulido) → ADR
